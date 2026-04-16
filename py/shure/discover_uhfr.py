import enum
from ipaddress import IPv4Address, IPv4Network
import logging
from queue import Queue
import select
import socket
import struct
import threading

import ifaddr

from discover import add_rx_to_dlist, DeviceDiscovery
from shure.mic_uhfr import WirelessUHFRMic


class SnetMsgType(enum.Enum):
    Discovery = 1
    Normal = 3
    Special = 4


class ShureUHFRDiscovery(DeviceDiscovery):
    """
    Based on and inspired by Thomas Matheison's WirelessMicSuiteServer
    (https://github.com/space928/WirelessMicSuiteServer), released
    under the GPL-3.0 licence.

    I do not know whether "SNet" is the official name for the underlying
    protocol, or a moniker he gave. Likewise, I do not know where he got
    the values of CHECKSUM_LUT from, or if/how they were calculated.
    """

    BCAST_PORT = 2201
    BCAST_SNET_ID = b'\xFF\xFF\xFF\xFF'
    OWN_SNET_ID = b'\x32\x16\x08\x04' # Made up

    # List of Device IDs to ignore messages from
    ID_BLACKLIST = (
        OWN_SNET_ID,
        b'\x15\xe1\x11\x80', # WWB6
    )

    CHECKSUM_LUT = [
        0x0000, 0xc0c1, 0xc181, 0x0140, 0xc301, 0x03c0, 0x0280, 0xc241,
        0xc601, 0x06c0, 0x0780, 0xc741, 0x0500, 0xc5c1, 0xc481, 0x0440,
        0xcc01, 0x0cc0, 0x0d80, 0xcd41, 0x0f00, 0xcfc1, 0xce81, 0x0e40,
        0x0a00, 0xcac1, 0xcb81, 0x0b40, 0xc901, 0x09c0, 0x0880, 0xc841,
        0xd801, 0x18c0, 0x1980, 0xd941, 0x1b00, 0xdbc1, 0xda81, 0x1a40,
        0x1e00, 0xdec1, 0xdf81, 0x1f40, 0xdd01, 0x1dc0, 0x1c80, 0xdc41,
        0x1400, 0xd4c1, 0xd581, 0x1540, 0xd701, 0x17c0, 0x1680, 0xd641,
        0xd201, 0x12c0, 0x1380, 0xd341, 0x1100, 0xd1c1, 0xd081, 0x1040,
        0xf001, 0x30c0, 0x3180, 0xf141, 0x3300, 0xf3c1, 0xf281, 0x3240,
        0x3600, 0xf6c1, 0xf781, 0x3740, 0xf501, 0x35c0, 0x3480, 0xf441,
        0x3c00, 0xfcc1, 0xfd81, 0x3d40, 0xff01, 0x3fc0, 0x3e80, 0xfe41,
        0xfa01, 0x3ac0, 0x3b80, 0xfb41, 0x3900, 0xf9c1, 0xf881, 0x3840,
        0x2800, 0xe8c1, 0xe981, 0x2940, 0xeb01, 0x2bc0, 0x2a80, 0xea41,
        0xee01, 0x2ec0, 0x2f80, 0xef41, 0x2d00, 0xedc1, 0xec81, 0x2c40,
        0xe401, 0x24c0, 0x2580, 0xe541, 0x2700, 0xe7c1, 0xe681, 0x2640,
        0x2200, 0xe2c1, 0xe381, 0x2340, 0xe101, 0x21c0, 0x2080, 0xe041,
        0xa001, 0x60c0, 0x6180, 0xa141, 0x6300, 0xa3c1, 0xa281, 0x6240,
        0x6600, 0xa6c1, 0xa781, 0x6740, 0xa501, 0x65c0, 0x6480, 0xa441,
        0x6c00, 0xacc1, 0xad81, 0x6d40, 0xaf01, 0x6fc0, 0x6e80, 0xae41,
        0xaa01, 0x6ac0, 0x6b80, 0xab41, 0x6900, 0xa9c1, 0xa881, 0x6840,
        0x7800, 0xb8c1, 0xb981, 0x7940, 0xbb01, 0x7bc0, 0x7a80, 0xba41,
        0xbe01, 0x7ec0, 0x7f80, 0xbf41, 0x7d00, 0xbdc1, 0xbc81, 0x7c40,
        0xb401, 0x74c0, 0x7580, 0xb541, 0x7700, 0xb7c1, 0xb681, 0x7640,
        0x7200, 0xb2c1, 0xb381, 0x7340, 0xb101, 0x71c0, 0x7080, 0xb041,
        0x5000, 0x90c1, 0x9181, 0x5140, 0x9301, 0x53c0, 0x5280, 0x9241,
        0x9601, 0x56c0, 0x5780, 0x9741, 0x5500, 0x95c1, 0x9481, 0x5440,
        0x9c01, 0x5cc0, 0x5d80, 0x9d41, 0x5f00, 0x9fc1, 0x9e81, 0x5e40,
        0x5a00, 0x9ac1, 0x9b81, 0x5b40, 0x9901, 0x59c0, 0x5880, 0x9841,
        0x8801, 0x48c0, 0x4980, 0x8941, 0x4b00, 0x8bc1, 0x8a81, 0x4a40,
        0x4e00, 0x8ec1, 0x8f81, 0x4f40, 0x8d01, 0x4dc0, 0x4c80, 0x8c41,
        0x4400, 0x84c1, 0x8581, 0x4540, 0x8701, 0x47c0, 0x4680, 0x8641,
        0x8201, 0x42c0, 0x4380, 0x8341, 0x4100, 0x81c1, 0x8081, 0x4040];


    def __init__(self):
        self.listener_sockets = []
        self.thread = threading.Thread(target=self.discover)

        self._known_devices: dict[bytes, str] = {}
        self._networks: list[IPv4Network] = []
        self._send_queue: Queue = Queue()

    def build_discovery_packet(self):
        return self.build_snet_packet(
            self.BCAST_SNET_ID,
            SnetMsgType.Discovery,
            struct.pack('>HH4s', 1, 1, self.OWN_SNET_ID)
        )

    def build_snet_packet(
        self,
        recipient_id: bytes,
        message_type: SnetMsgType,
        payload: bytes
    ) -> bytes:
        header = struct.pack(
            '>4s4sxxHH',
            recipient_id,
            self.OWN_SNET_ID,
            message_type.value,
            len(payload),
        )
        return header + self.calculate_checksum(header) + payload

    def calculate_checksum(self, data: bytes) -> bytes:
        retval = ~0 & 0xFFFF
        for idx in range(len(data)):
            retval = self.CHECKSUM_LUT[(retval ^ data[idx]) & 0xFF] ^ (retval >> 8)
        return struct.pack('>H', ~retval & 0xFFFF)

    def discover(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", self.BCAST_PORT))
        socks = [sock]

        self._networks = []
        for adapter in ifaddr.get_adapters():
            for addr in adapter.ips:
                if not addr.is_IPv4 or self.is_ignored_address(addr.ip):
                    continue
                self._networks.append(
                    IPv4Network((addr.ip, addr.network_prefix), False)
                )

        while True:
            read_socks, write_socks, error_socks = select.select(socks, socks, socks, .2)

            for rx in read_socks:
                try:
                    data, (ipv4, _) = rx.recvfrom(1024)
                except Exception as e:
                    logging.error(e)
                else:
                    self.process_snet_packet(IPv4Address(ipv4), data)

            if write_socks and not self._send_queue.empty():
                ipv4_addr, bytestring = self._send_queue.get()
                for sock in write_socks:
                    try:
                        sock.sendto(bytestring, (str(ipv4_addr), self.BCAST_PORT))
                    except Exception as error:
                        # TODO: Write better error handling
                        logging.error("TX ERROR IP: %s String: %s\t%s", ipv4_addr, bytestring, error)

            for rx in error_socks:
                logging.error("Errored: ", rx)

    def get_broadcast_addr_for(self, address: IPv4Address) -> IPv4Address | None:
        for network in self._networks:
            if address in network:
                return network.broadcast_address
        return None

    def process_snet_packet(
        self,
        ipv4_address: IPv4Address,
        data: bytes
    ) -> None:
        if len(data) < 16:
            # Message too short
            return

        (
            recipient_id,
            sender_id,
            msg_type,
            payload_length,
            checksum,
        ) = struct.unpack('>4s4sxxHHH', data[0:16])
        payload = data[16:]

        if sender_id in self.ID_BLACKLIST:
            # For now we're using a blacklist - IDs we know are not
            # devices. Hopefully a better solution will become apparent
            # once more UR4S and UR4D devices have been tested with.
            #
            # The blacklist includes our own ID.
            return

        if self._known_devices.get(sender_id, None):
            # We've already discovered this device, and as we don't use
            # SNet for anything except device discovery, ignore it.
            return

        if recipient_id == self.BCAST_SNET_ID and msg_type == SnetMsgType.Discovery.value:
            self._known_devices[sender_id] = None

            # We don't know how to tell the difference between UR4S and
            # UR4D models from their discovery packets. We can work
            # around this by requesting the model name via SNet.
            #
            # We announce that we exist, then make the actual request.
            broadcast_address = self.get_broadcast_addr_for(ipv4_address)
            self._send_queue.put((
                broadcast_address,
                self.build_discovery_packet()
            ))
            self._send_queue.put((
                broadcast_address,
                self.build_snet_packet(
                    sender_id,
                    SnetMsgType.Normal,
                    '* GET MODEL_NAME *'.encode('ascii')
                )
            ))
            return

        if (
            recipient_id != self.OWN_SNET_ID      # Not for us
        or  msg_type != SnetMsgType.Normal.value  # Wrong message type
        or  sender_id not in self._known_devices  # Haven't received a Discovery packet from this
        ):
            return

        payload = payload.decode('ascii')
        payload = payload.strip('* ')
        payload = payload.rstrip()
        split = payload.split()

        if split[0] != 'REPORT' or split[1] != 'MODEL_NAME':
            # Not the message we're waiting for
            return

        device_model = split[2]
        self._known_devices[sender_id] = device_model
        model_definition = WirelessUHFRMic.MODELS.get(device_model, None)
        if not model_definition:
            logging.warning("Unrecognised UHF-R model: %s", device_model)
            return

        add_rx_to_dlist(str(ipv4_address), 'uhfr', device_model, model_definition['channels'])

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join()
