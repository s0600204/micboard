import json
import time

from channel import ChannelDeviceReportEnum
from mic import BATTERY_TIMEOUT, WirelessMicBatteryStatus, WirelessMicReportEnum
# ~ from sennheiser.mic import SennheiserMicReportEnum
from sennheiser.mic_ssc import WirelessSSCMic
from util import WIRELESS_QUERY_QUEUE_INTERVAL


class WirelessEWDXMic(WirelessSSCMic):

    NAME = 'Evolution Wireless Digital'

    ANTENNA_COUNT = 1
    REPORT_MAPPING = {
        '/m/rx/af'                : WirelessMicReportEnum.AFLevel,
        '/m/rx/divi'              : WirelessMicReportEnum.Antenna,
        '/m/rx/rssi'              : WirelessMicReportEnum.RFLevels,
        '/mates/tx/battery/gauge' : WirelessMicReportEnum.Battery,
        '/mates/tx/trim'          : WirelessMicReportEnum.TXOffset, # TXGain
        '/rx/frequency'           : ChannelDeviceReportEnum.Frequency,
        # ~ '/rx/gain'                : WirelessMicReportEnum.RXGain,
        '/rx/name'                : ChannelDeviceReportEnum.Name,
    }
    MODELS = {
        'EWDX2'      : { 'channels': 2, 'name': 'EW-DX EM 2' },
        'EWDX2Dante' : { 'channels': 2, 'name': 'EW-DX EM 2 Dante' },
        'EWDX4Dante' : { 'channels': 4, 'name': 'EW-DX EM 4 Dante' },
    }

    def build_monitoring_request(self):
        return json.dumps({
            'osc': {
                'state': {
                    'subscribe': [{
                        '#': {
                            # ~ 'count': 100_000, # default: 1000,
                            'lifetime': WIRELESS_QUERY_QUEUE_INTERVAL, # seconds; default: 10
                            # ~ 'max': 0, # milliseconds; default: 0
                            # ~ 'min': 0, # milliseconds; default: 0
                        },
                        # ~ 'audio': {
                            # ~ f'out{self.channel}': {
                                # ~ 'level': None,
                            # ~ },
                        # ~ },
                        'm': {
                            f'rx{self.channel}': {
                                'af': None, # AF Signal
                                'divi': None, # Diversity
                                'rssi': None, # RF Signal
                                #'rsqi': None, # RF Quality
                            },
                        },
                        'mates': {
                            f'tx{self.channel}': {
                                'battery': {
                                    'gauge': None,
                                },
                                # ~ 'lock': None,
                                'trim': None, # tx gain
                            },
                        },
                        f'rx{self.channel}': {
                            'frequency': None,
                            # ~ 'gain' None, # rx gain
                            'name': None, 
                        },
                    }]
                }
            }
        })

    def build_get_all_strings(self):
        return [
            # ~ self.translate_to_json('/device/identity/version'),
            # ~ self.translate_to_json('/device/identity/product'),
            *self.build_query_strings(),
        ]

    def build_query_strings(self):
        return [
            self.build_monitoring_request(),
        ]

    def monitoring_disable(self):
        # Might have possible problem, as subscription messages supersede all previous from a
        # given client, and thus might clobber other channels' requests for subscription.
        # Possible solution: keep track of channels subs on the network device (self.rx), and
        # build based on that.
        return json.dumps({
            "osc": {
                "state": {
                    "subscribe": {
                        "cancel": True,
                    }
                }
            }
        })

    def set_antenna(self, antenna):
        # /m/rx{*}/divi
        self.antenna = {
            0: 'XX', # Neither
            1: 'BX', # Antenna A
            2: 'XB', # Antenna B
        }.get(antenna, 'XX')

    def set_audio_level(self, audio_level):
        # /m/rx{*}/af
        # -138.5 - 0 dBfs
        self.audio_level = round(100 * 10 ** (audio_level / 20))
        if self.audio_level == 100:
            self.set_peak_flag()

    def set_battery(self, level):
        # /mates/tx{*}/battery/gauge
        # Sent as number (percentage) or null (None).
        # Using same battery segment points as MCP for ease.
        if level is None:
            self.battery = 0
            self.battery_status = WirelessMicBatteryStatus.Unknown
        else:
            level_thresholds = {
                70 : (3, WirelessMicBatteryStatus.Good),
                30 : (2, WirelessMicBatteryStatus.Good),
                0  : (1, WirelessMicBatteryStatus.Replace),
                -99: (0, WirelessMicBatteryStatus.Critical),
            }
            for threshold, state in level_thresholds.items():
                if level > threshold:
                    self.battery = state[0]
                    self.battery_status = state[1]
                    break

        if self.battery_status != WirelessMicBatteryStatus.Unknown:
            self.prev_battery = level
            self.timestamp = time.time()
        elif (time.time() - self.timestamp) < BATTERY_TIMEOUT:
            self.battery_status = level_dict[self.prev_battery][1]

    def set_frequency(self, frequency):
        # /rx{*}/frequency
        # 470_200 - 1_999_000 kHz
        super().set_frequency(frequency)

    def set_rf_levels(self, rf_level):
        # /m/rx{*}/rssi
        # -107.0 - 0 dBm
        # This is actually the formula for dBfs, but ah well.
        self.rf_levels[0] = round(100 * 10 ** (rf_level / 20))

    def set_tx_offset(self, tx_offset):
        # /mates/tx{*}/trim
        # -12 - 6 dB
        self.tx_offset = int(tx_offset)
