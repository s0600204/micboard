import logging
import time

from channel import ChannelDeviceReportEnum
from mic.mic import BATTERY_TIMEOUT, WirelessMicBatteryStatus, WirelessMicReportEnum
from sennheiser.mic import SennheiserMicReportEnum, WirelessSennheiserMic
from util import WIRELESS_QUERY_QUEUE_INTERVAL


class WirelessMCPMic(WirelessSennheiserMic):

    CYCLIC_ATTRS = ['AF', 'Bat', 'Config', 'Msg', 'States', 'RF', 'RF1', 'RF2']
    REPORT_MAPPING = {
        'AF'        : WirelessMicReportEnum.AFLevel,
        'AfOut'     : WirelessMicReportEnum.TXOffset,
        'Bat'       : WirelessMicReportEnum.Battery,
        'Frequency' : ChannelDeviceReportEnum.Frequency,
        'Msg'       : SennheiserMicReportEnum.Msg,
        'Name'      : ChannelDeviceReportEnum.Name,
        'RF1'       : SennheiserMicReportEnum.RFLevel1,
        'RF2'       : SennheiserMicReportEnum.RFLevel2,
        'Squelch'   : SennheiserMicReportEnum.Squelch,
    }

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def build_get_all_strings(self):
        return [
            f'Push 0 0 1\r',
            *self.build_query_strings(),
        ]

    def build_query_strings(self):
        return [
            f'Push {int(WIRELESS_QUERY_QUEUE_INTERVAL)} {int(self.rx.METERING_INTERVAL * 1000)} 1\r',
        ]

    def monitoring_disable(self):
        return f'Push 0 0 0\r'

    def set_audio_level(self, audio_level, peak_level, mute_state):
        self.audio_level = min(int(audio_level), 100)
        self.peak_level = min(int(peak_level), 100)
        if self.audio_level == 100 or self.peak_level == 100:
            self.set_peak_flag()

    def set_battery(self, level):
        level_dict = {
            '0':   (0, WirelessMicBatteryStatus.Critical),
            '30':  (1, WirelessMicBatteryStatus.Replace),
            '70':  (2, WirelessMicBatteryStatus.Good),
            '100': (3, WirelessMicBatteryStatus.Good),
            '?':   (0, WirelessMicBatteryStatus.Unknown),
        }
        self.battery = level_dict[level][0]
        self.battery_status = level_dict[level][1]

        if self.battery_status != WirelessMicBatteryStatus.Unknown:
            self.prev_battery = level
            self.timestamp = time.time()
        elif (time.time() - self.timestamp) < BATTERY_TIMEOUT:
            self.battery_status = level_dict[self.prev_battery][1]

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
        self.squelch = squelch_level

    def set_tx_offset(self, tx_offset):
        self.tx_offset = int(tx_offset)
