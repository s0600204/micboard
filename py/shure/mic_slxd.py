from channel import ChannelDeviceReportEnum
from mic import WirelessMicReportEnum
from shure.mic import ShureMicReportEnum, WirelessShureMic


class WirelessSLXDMic(WirelessShureMic):

    NAME = 'SLX-D'

    ANTENNA_COUNT = 1
    MODELS = {
        'SLXD4S'       : { 'channels': 1, 'name': 'SLXD4', },
        'SLXD4S+'      : { 'channels': 1, 'name': 'SLXD4+', },
        'SLXD4D'       : { 'channels': 2, },
        'SLXD4D+'      : { 'channels': 2, },
        'SLXD4Q+'      : { 'channels': 4, 'name': 'SLXD4Q+', },
        'SLXD4QDante+' : { 'channels': 4, 'name': 'SLXD4QDAN+', },
    }
    REPORT_MAPPING = {
        'AUDIO_LEVEL_RMS' : WirelessMicReportEnum.AFLevel,
        'CHAN_NAME'       : ChannelDeviceReportEnum.Name,
        'FREQUENCY'       : ChannelDeviceReportEnum.Frequency,
        'LOCK_STATUS'     : ShureMicReportEnum.PowerLock,
        'RSSI'            : WirelessMicReportEnum.RFLevels,
        'TX_BATT_BARS'    : WirelessMicReportEnum.Battery,
        'TX_BATT_MINS'    : ShureMicReportEnum.Runtime,
    }

    DCID_NAME_MAPPING = {
        'SLX-DRxS': 'SLXD4D',
    }

    def build_query_strings(self):
        return [
            f'< GET {self.channel} CHAN_NAME >',
            f'< GET {self.channel} TX_BATT_BARS >',
        ]

    def parse_sample(self, split):
        # 3 : audio peak
        # 4 : audio rms
        # 5 : rssi
        self.set_audio_level(split[4])
        self.set_rf_levels(0, split[5])

    def set_audio_level(self, audio_level):
        self.audio_level = int(audio_level) - 20

    def set_frequency(self, frequency):
        super().set_frequency(frequency.lstrip('0'))

    def set_rf_levels(self, antenna, rf_level):
        self.rf_levels[antenna] = int(100 * (float(rf_level) / 120))
