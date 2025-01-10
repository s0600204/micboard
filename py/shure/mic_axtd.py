import logging

from channel import ChannelDeviceReportEnum
from mic.mic import WirelessMicReportEnum
from shure.mic import ShureMicReportEnum, WirelessShureMic


class WirelessAXTDMic(WirelessShureMic):
    
    ANTENNA_COUNT = 4
    REPORT_MAPPING = {
        'ANTENNA_STATUS'  : WirelessMicReportEnum.Antenna,
        'AUDIO_LEVEL_RMS' : WirelessMicReportEnum.AFLevel,
        'CHAN_NAME'       : ChannelDeviceReportEnum.Name,
        'CHAN_QUALITY'    : ShureMicReportEnum.TXQuality,
        'FREQUENCY'       : ChannelDeviceReportEnum.Frequency,
        'RSSI'            : WirelessMicReportEnum.RFLevels,
        'TX_BATT_BARS'    : WirelessMicReportEnum.Battery,
        'TX_BATT_MINS'    : ShureMicReportEnum.Runtime,
        'TX_LOCK'         : ShureMicReportEnum.PowerLock,
        'TX_OFFSET'       : WirelessMicReportEnum.TXOffset,
    }

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def build_query_strings(self):
        return [
            f'< GET {self.channel} CHAN_NAME >',
            f'< GET {self.channel} TX_BATT_BARS >',
        ]

    def parse_sample(self, split):
        self.set_antenna(split[7])
        self.set_rf_levels(0, split[9])
        self.set_rf_levels(1, split[11])
        # If in "Quadversity" mode:
        #self.set_rf_levels(2, split[13])
        #self.set_rf_levels(3, split[15])
        self.set_audio_level(split[6])
        self.set_tx_quality(split[3])
        # TO TEST
        self.process_audio_bitmap(split[4])

    def set_audio_level(self, audio_level):
        self.audio_level = int(audio_level) - 20

    def set_frequency(self, frequency):
        super().set_frequency(frequency.lstrip('0'))

    def set_rf_levels(self, antenna, rf_level):
        self.rf_levels[antenna] = int(100 * (float(rf_level) / 115))

    def set_tx_offset(self, tx_offset):
        if tx_offset != '255':
            self.tx_offset = int(tx_offset) - 12
