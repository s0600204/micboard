import logging

from networkdevice import NetworkDevice

from shure.mic_axtd import WirelessAXTDMic
from shure.mic_qulxd import WirelessQULXDMic
from shure.mic_uhfr import WirelessUHFRMic


class ShureNetworkDevice(NetworkDevice):

    PORT = 2202
    DEVICE_CLASS_MAP = {
        'axtd': WirelessAXTDMic,
        'qlxd': WirelessQULXDMic,
        'uhfr': WirelessUHFRMic,
        'ulxd': WirelessQULXDMic,
    }

    def parse_raw_rx(self, data):
        data = data.strip('< >').strip('* ')
        data = data.replace('{', '').replace('}', '')
        data = data.rstrip()
        split = data.split()
        if data:
            try:
                if split[0] in ['REP', 'REPORT', 'SAMPLE'] and split[1] in ['1', '2', '3', '4']:
                    ch = self.get_device_by_channel(int(split[1]))
                    ch.parse_raw_ch(data)

                elif split[0] in ['REP', 'REPORT']:
                    self.raw[split[1]] = ' '.join(split[2:])
            except:
                logging.warning("Index Error(RX): %s", data)

    def split_raw_rx(self, data):
        data = data.decode(self.ENCODING)
        if self.type == 'uhfr':
            return [entry for entry in data.split("*") if entry]

        sep = '>'
        return [entry + sep for entry in data.split(sep) if entry]
