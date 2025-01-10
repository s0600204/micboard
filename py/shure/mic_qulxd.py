import logging

from channel import ChannelDeviceReportEnum
from mic.mic import WirelessMicReportEnum
from shure.mic import ShureMicReportEnum, WirelessShureMic


PEAK_LEVEL = {
    'qlxd': 80,
    'ulxd': 80
}

class WirelessQULXDMic(WirelessShureMic):

    ANTENNA_COUNT = 1
    REPORT_MAPPING = {
        'BATT_BARS'     : WirelessMicReportEnum.Battery,
        'BATT_RUN_TIME' : ShureMicReportEnum.Runtime,
        'CHAN_NAME'     : ChannelDeviceReportEnum.Name,
        'FREQUENCY'     : ChannelDeviceReportEnum.Frequency,
        'TX_OFFSET'     : WirelessMicReportEnum.TXOffset,
        'TX_PWR_LOCK'   : ShureMicReportEnum.PowerLock,
    }

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def build_query_strings(self):
        return [
            f'< GET {self.channel} CHAN_NAME >',
            f'< GET {self.channel} BATT_BARS >',
        ]

    def parse_sample(self, split):
        self.set_antenna(split[3])
        self.set_rf_levels(0, split[4])
        self.set_audio_level(split[5])

    def set_audio_level(self, audio_level):
        audio_level = 2 * int(audio_level)

        if audio_level >= PEAK_LEVEL[self.rx.type]:
            self.set_peak_flag()

        self.audio_level = audio_level

    def set_rf_levels(self, antenna, rf_level):
        self.rf_levels[antenna] = int(100 * (float(rf_level) / 115))

    def set_tx_offset(self, tx_offset):
        if tx_offset != '255':
            self.tx_offset = int(tx_offset)
