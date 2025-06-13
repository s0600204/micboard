import json
import logging
import platform
import re
import select
import socket
import struct
import threading

import ifaddr

import config
from device_config import BASE_CONST
from discover import add_rx_to_dlist


class ShureDiscovery:

    DCID_JSON_FILE = config.app_dir('dcid.json')
    MCAST_GRP = '239.255.254.253'
    MCAST_PORT = 8427

    def __init__(self, discover_callback=None):
        self.dcid_definitions = None
        self.discover_callback = discover_callback or self.process_discovery_packet
        self.ignored_addrs = ['127.0.0.1'] # Local addresses to not bind to
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

    def discover(self):
        self.bind_listeners()

        if platform.system() != "Windows":
            # On *nix systems, although all the sockets are bound to different *local* addresses, 
            # they're all bound to the same *multicast* address. Thus, they all receive the same
            # message(s) at the same time, so we only need to `select` on one of them.
            socks = [self.listener_sockets[0]]
        else:
            # As to Windows, I need to check if we need to listen to all the sockets, or just
            # the first one as above.
            socks = self.listener_sockets

        while True:
            read_socks, _, error_socks = select.select(socks, [], socks, .2)

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
            logging.debug('Received SLP message with function-id %s\n(%s)', message[1], message)
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
        for (type_k, type_v) in BASE_CONST.items():
            for (model_k, model_v) in type_v['DCID_MODEL'].items():
                if model_k == dcid_model:
                    return type_k, model_v
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

        # Get device definition from BASE_CONST
        rx_type, channels = self.get_device_definition(device)

        add_rx_to_dlist(ip, rx_type, channels)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join()
