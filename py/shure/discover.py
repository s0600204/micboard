import json
import logging
import platform
import random
import re
import select
import socket
import struct
import threading
import time

import ifaddr

import config
from discover import add_rx_to_dlist
from shure.networkdevice import ShureNetworkDevice


class ShureDiscovery:

    DCID_JSON_FILE = config.app_dir('dcid.json')
    MCAST_GRP = '239.255.254.253'
    MCAST_PORT = 8427
    WINDOWS_KEEPALIVE_TIMEOUT = 30 # seconds


    def __init__(self, discover_callback=None):
        self.dcid_definitions = None
        self.discover_callback = discover_callback or self.process_discovery_packet
        self.ignored_addrs = ['127.0.0.1'] # Local addresses to not bind to
        self.last_keepalive_sent = -self.WINDOWS_KEEPALIVE_TIMEOUT
        self.listener_sockets = []
        self.thread = threading.Thread(target=self.discover)

    def bind_listeners(self):
        '''
        On computers with multiple NICs, binding using `socket.INADDR_ANY` only connects to the
        "default" adapter, which is not necessarily the adapter through which the devices we're
        want to discover may be found. (Also, if the "default" adapter is offline, attempting to
        bind to it may throw an exception.)
        '''
        for adapter in ifaddr.get_adapters():
            for addr in adapter.ips:
                if not addr.is_IPv4 or addr.ip in self.ignored_addrs:
                    continue
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # On Windows, one binds to the local address on the interface;
                # On *nix systems, one binds to the Multicast group address.
                if platform.system() == "Windows":
                    try:
                        sock.bind((addr.ip, self.MCAST_PORT))
                    except OSError as error:
                        if error.errno == 10049 and addr.ip.startswith("169.254."):
                            # Windows (10) assigns a link-local address to unconnected adapters,
                            # despite them bring, y'know, *not connected* to anything.
                            logging.debug(
                                "Skipping unbindable address %s on unconnected interface '%s' (aka '%s')",
                                addr.ip, adapter.nice_name, addr.nice_name
                            )
                            self.ignored_addrs.append(addr.ip)
                            continue
                        raise error
                else:
                    sock.bind((self.MCAST_GRP, self.MCAST_PORT))

                mreq = struct.pack("4s4s", socket.inet_aton(self.MCAST_GRP), socket.inet_aton(addr.ip))
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

                logging.debug(
                    "Discovering Shure devices via %s on '%s",
                    addr.ip, adapter.nice_name
                )
                self.listener_sockets.append(sock)

    def build_service_request_message(self):
        scope = b'DEFAULT'
        service_type = b'acn.esta'
        xid = random.randint(1, 65535)
        message = (
            b'\x02',                       # SLP version
            b'\x01',                       # function_id (SrvRqst in this case)
            b'\x00\x00\x00',               # message length (populated below)
            (0x00|0x00|0x20).to_bytes(1),  # Overflow/Fresh/Request-multicast flags
            b'\x00',                       # reserved
            b'\x00\x00\x00',               # next extension offset
            xid.to_bytes(2),               # xid
            b'\x00\x02',                   # language tag length
            b'en',                         # language tag
            len(b'').to_bytes(2),          # length of list of Previous Responders
            b'',                           # comma-separated list of Previous Responders
            len(service_type).to_bytes(2),
            service_type,
            len(scope).to_bytes(2),        # length of list of scope names
            scope,                         # comma-separated list of scope names
            len(b'').to_bytes(2),          # length of predicate string
            b'',                           # predicate string
            len(b'').to_bytes(2),          # length of SLP SPI string
            b'',                           # SLP SPI string
        )
        message = b''.join(message)
        return message[:2] + len(message).to_bytes(3) + message[5:]

    def discover(self):
        self.bind_listeners()

        system = platform.system()
        if system == "Windows":
            # On Windows messages only "appear" on the socket they arrive on...
            socks = self.listener_sockets
        else:
            # ...but on *nix systems all messages "appear" on all our listening sockets.
            #
            # This is possibly because whilst they're all assigned to different interfaces, they're
            # all bound to the same address.
            #
            # Whatever the reason, we only need to `select.select()` one of the sockets.
            socks = [self.listener_sockets[0]]

        while True:
            read_socks, write_socks, error_socks = select.select(socks, socks, socks, .2)

            if system == "Windows":
                # From experimentation, it appears that on Windows we can only *receive* messages
                # from a multicast group if we've recently *sent* a message to the group. It does
                # not matter what we send, but it makes sense for it to be an SLPv2 message.
                #
                # Thus, we send a "Service Request" message - ordinarily used to find providers of
                # a specific service on the network. We don't expect a response.
                now = int(time.perf_counter())
                if now - self.last_keepalive_sent > self.WINDOWS_KEEPALIVE_TIMEOUT:
                    for tx in write_socks:
                        tx.sendto(self.build_service_request_message(), (self.MCAST_GRP, self.MCAST_PORT))
                    self.last_keepalive_sent = now

            for rx in read_socks:
                try:
                    data, (ip4_addr, _) = rx.recvfrom(1024)
                except Exception as e:
                    logging.error(e)
                else:
                    self.discover_callback(ip4_addr, data)

            for rx in error_socks:
                logging.error("Errored: ", rx)

    def get_attrs_from_slp(self, message):
        '''
        SLPv2 is RFC2608 (https://datatracker.ietf.org/doc/html/rfc2608)

        We don't parse the full SLP header(s), as we don't need to, just the pertinent bits.

        Attributes may either be in the form <key>=<value>, or simply <value>, e.g.:
        >> "attr1,(attr-with-a=value),attr3,(attr-with=two,values)"

        Thus, we filter them into a dict and an array respectively:
        >> kv_attrs = {'attr-with-a': value, 'attr-with': 'two,values'}
        >> v_attrs = [attr1, attr3]
        '''
        if message[1] != 7:
            # Function-ID
            #   If not `7` ("Attribute Reply"), then it doesn't contain what we're looking for
            return [], {}

        # Find the end of the common SLP message header
        language_tag_length = int.from_bytes(message[12:14])
        slp_header_end = 14 + language_tag_length

        # Find the start and end point of the Attributes
        attributes_start = slp_header_end + 4
        attributes_length = int.from_bytes(message[slp_header_end+2:attributes_start])
        attributes_end = attributes_start + attributes_length

        # Extract and return the Attributes
        raw_attrs = message[attributes_start:attributes_end].decode("UTF-8")
        v_attrs = []
        kv_attrs = {}
        for element in re.split(r',(?![^(]*\))', raw_attrs):
            if element[0] == '(':
                key, value = element[1:-1].split('=', 1)
                kv_attrs[key] = value
            else:
                v_attrs.append(element)
        return v_attrs, kv_attrs

    def get_dcid_definition(self, dcid):
        if not self.dcid_definitions:
            with open(self.DCID_JSON_FILE, 'r') as f:
                self.dcid_definitions = json.load(f)

        return self.dcid_definitions.get(dcid, {})

    def get_dcid_from_slp_attrs(self, v_attrs, kv_attrs):
        if 'csl-esta.dmp' in kv_attrs:
            dcid = kv_attrs['csl-esta.dmp']
            return dcid[dcid.index('cd:')+3:]
        return None

    def get_device_definition(self, dcid_definition):
        dcid_model = dcid_definition['model']
        for device_type, device_class in ShureNetworkDevice.DEVICE_CLASS_MAP.items():
            for model_name, model in device_class.DCID_NAME_MAPPING.items():
                if model_name == dcid_model:
                    return {
                        'type': device_type,
                        **device_class.MODELS[model],
                    }

        return None

    def process_discovery_packet(self, ip, data):
        # Get DCID of device
        dcid = self.get_dcid_from_slp_attrs(*self.get_attrs_from_slp(data))
        if not dcid:
            return

        # Get device definition matching DCID
        device = self.get_dcid_definition(dcid)
        if not device:
            logging.warning('Unrecognised DCID: %s', dcid)
            return

        # Get device definition from device class
        device = self.get_device_definition(device)

        add_rx_to_dlist(ip, device['type'], device['channels'])

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join()
