import logging

from channel import chart_update_list, data_update_list
from networkdevice import NetworkDevice
from util import NetworkProtocol

from shure.mic_axtd import WirelessAXTDMic
from shure.mic_qlxd import WirelessQLXDMic
from shure.mic_slxd import WirelessSLXDMic
from shure.mic_uhfr import WirelessUHFRMic
from shure.mic_ulxd import WirelessULXDMic

from shure.iem_p10t import WirelessP10tIEM


class ShureNetworkDevice(NetworkDevice):

    PORT = 2202
    DEVICE_CLASS_MAP = {
        'axtd': WirelessAXTDMic,
        'p10t': WirelessP10tIEM,
        'qlxd': WirelessQLXDMic,
        'slxd': WirelessSLXDMic,
        'ulxd': WirelessULXDMic,
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
                    try:
                        if split[0] == 'SAMPLE' and split[2] == 'ALL':
                            ch.parse_sample(split)
                            chart_update_list.append(ch.chart_json())

                        if split[0] in ['REP', 'REPLY', 'REPORT']:
                            ch.parse_report(split[2], split[3:])

                            if ch not in data_update_list:
                                data_update_list.append(ch)

                    except Exception as e:
                        print("Index Error(TX): {}".format(data.split()))
                        print(e)

                elif split[0] in ['REP', 'REPORT']:
                    self.raw[split[1]] = ' '.join(split[2:])
            except:
                logging.warning("Index Error(RX): %s", data)

    def split_raw_rx(self, data):
        data = data.decode(self.ENCODING)
        sep = '>'
        return [entry + sep for entry in data.split(sep) if entry]


class ShureNetworkUDPDevice(ShureNetworkDevice):

    DEVICE_CLASS_MAP = {
        'uhfr': WirelessUHFRMic,
    }
    NETWORK_PROTOCOL = NetworkProtocol.UDP

    def split_raw_rx(self, data):
        data = data.decode(self.ENCODING)
        return [entry for entry in data.split("*") if entry]
