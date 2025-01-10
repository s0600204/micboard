import logging

from channel import ChannelDeviceReportEnum
from mic.mic import MSB, WirelessMicReportEnum
from shure.mic import ShureMicReportEnum, WirelessShureMic


class WirelessUHFRMic(WirelessShureMic):

    ANTENNA_COUNT = 2
    REPORT_MAPPING = {
        'CHAN_NAME' : ChannelDeviceReportEnum.Name,
        'FREQUENCY' : ChannelDeviceReportEnum.Frequency,
        'TX_BAT'    : WirelessMicReportEnum.Battery,
    }

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def build_get_all_strings(self):
        return [
            f'* GET {self.channel} CHAN_NAME *',
            f'* GET {self.channel} TX_BAT *',
            f'* GET {self.channel} GROUP_CHAN *',
        ]

    def build_query_strings(self):
        return [
            f'* GET {self.channel} CHAN_NAME *',
            f'* GET {self.channel} TX_BAT *',
            f'* GET {self.channel} GROUP_CHAN *',
        ]

    def monitoring_disable(self):
        return f'* METER {self.channel} ALL STOP *'

    def monitoring_enable(self, interval):
        return f'* METER {self.channel} ALL {int(interval / 30 * 1000):03d} *'

    def parse_sample(self, split):
        self.set_antenna(split[3])
        self.set_rf_levels(0, split[4])
        self.set_rf_levels(1, split[5])
        self.set_battery(split[6])
        self.set_audio_level(split[7])
        # TO TEST
        self.process_audio_bitmap(split[7])

    def set_audio_level(self, audio_level):
        self.audio_level = int(ceil(MSB(int(audio_level)) * (100./8)))

    def set_rf_levels(self, antenna):
        self.rf_levels[antenna] = int(100 * ((100 - float(rf_level)) / 80))
