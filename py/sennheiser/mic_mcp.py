import time

from channel import ChannelDeviceReportEnum
from mic import BATTERY_TIMEOUT, WirelessMicBatteryStatus, WirelessMicReportEnum
from sennheiser.mic import SennheiserMicReportEnum, WirelessSennheiserMic
from util import NetworkProtocol, WIRELESS_QUERY_QUEUE_INTERVAL


class WirelessMCPMic(WirelessSennheiserMic):

    NAME = 'Evolution Wireless'

    BATTERY_LEVEL_MAP = {
        '0':   (0, WirelessMicBatteryStatus.Critical),
        '30':  (1, WirelessMicBatteryStatus.Replace),
        '70':  (2, WirelessMicBatteryStatus.Good),
        '100': (3, WirelessMicBatteryStatus.Good),
        '?':   (0, WirelessMicBatteryStatus.Unknown),
    }
    CYCLIC_ATTRS = ['AF', 'Bat', 'Config', 'Msg', 'States', 'RF', 'RF1', 'RF2']
    MODELS = {
        'EM300G3'    : { 'channels': 1, 'name': 'EM 300 G3', },
        'EM500G3'    : { 'channels': 1, 'name': 'EM 500 G3', },
        'EM300500G4' : { 'channels': 1, 'name': 'EM 300-500 G4', },
        'EM2000'     : { 'channels': 1, 'name': 'EM 2000', },
        'EM2050'     : { 'channels': 1, 'name': 'EM 2050', },
    }
    REPORT_MAPPING = {
        'AF'        : WirelessMicReportEnum.AFLevel,
        'AfOut'     : WirelessMicReportEnum.TXOffset,
        'Bat'       : WirelessMicReportEnum.Battery,
        'Frequency' : ChannelDeviceReportEnum.Frequency,
        'Msg'       : SennheiserMicReportEnum.Msg,
        'Name'      : ChannelDeviceReportEnum.Name,
        'RF1'       : SennheiserMicReportEnum.RFLevel1,
        'RF2'       : SennheiserMicReportEnum.RFLevel2,
        'Squelch'   : WirelessMicReportEnum.Squelch,
    }
 
    MCP_MODEL_NAMES = {
        'EM300G3' : 'EM300G3',
        'EM500G3' : 'EM500G3',
        'EMProG4' : 'EM300500G4',
    }

    def build_get_all_strings(self):
        return [
            'Push 0 0 1\r',
            *self.build_query_strings(),
        ]

    def build_query_strings(self):
        metering_interval = self.rx.METERING_INTERVAL * 1000
        return [
            f'Push {int(WIRELESS_QUERY_QUEUE_INTERVAL)} {int(metering_interval)} 1\r',
        ]

    def monitoring_disable(self):
        return 'Push 0 0 0\r'

    def set_audio_level(self, audio_level, peak_level, mute_state):
        self.audio_level = min(int(audio_level), 100)
        self.peak_level = min(int(peak_level), 100)
        if self.audio_level == 100 or self.peak_level == 100:
            self.set_peak_flag()

    def set_frequency(self, frequency, bank, channel):
        super().set_frequency(frequency)

    def set_msg(self, *messages):
        if messages == ['OK']:
            return
        self.mute_statuses['RF'] = 'RF_Mute' in messages
        self.mute_statuses['RX'] = 'RX_Mute' in messages
        self.mute_statuses['TX'] = 'TX_Mute' in messages
        """
        Other messages:
        * 'AF_Peak'
            From exploration, this is only emitted if audio
            is too loud for at least 3 contiguous seconds.
        * 'Low_Battery'
        * 'Low_RF_Signal'
            If RF is only just above Squelch.
        """

    def set_rf_level_1(self, rf_level, peak_level, is_active):
        self.rf_levels[0] = min(int(rf_level), 100)
        self.rf_peaks[0] = min(int(peak_level), 100)
        self.antenna = ('B' if int(is_active) else 'X') + self.antenna[1]

    def set_rf_level_2(self, rf_level, peak_level, is_active):
        self.rf_levels[1] = min(int(rf_level), 100)
        self.rf_peaks[1] = min(int(peak_level), 100)
        self.antenna = self.antenna[0] + ('B' if int(is_active) else 'X')

    def set_squelch(self, squelch_level):
        # squelch --> 0,5-25; dB in 3dB steps
        # rf --> 0-100; percentage, equiv. 0-40dBuV
        self.squelch['db'] = int(squelch_level)
        if self.squelch['db'] == 0:
            self.squelch['perc'] = None
            self.squelch['str'] = 'squelch off'
        else:
            self.squelch['perc'] = int(self.squelch['db'] / 40 * 100),
            self.squelch['str'] = f'{self.squelch['db']} dB'

    def set_tx_offset(self, tx_offset):
        self.tx_offset = int(tx_offset)
