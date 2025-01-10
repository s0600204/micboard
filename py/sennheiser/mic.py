import enum
import logging
import time

from mic.mic import BATTERY_TIMEOUT, PEAK_TIMEOUT, WirelessMic


class SennheiserMicReportEnum(enum.Enum):
    AfOut = enum.auto()
    Config = enum.auto()
    Equalizer = enum.auto()
    Message = enum.auto()
    Msg = enum.auto()
    Mute = enum.auto()
    RF = enum.auto()
    RFLevel1 = enum.auto()
    RFLevel2 = enum.auto()
    Squelch = enum.auto()
    Status = enum.auto()


class WirelessSennheiserMic(WirelessMic):

    ANTENNA_COUNT = 2
    BATTERY_SEGMENTS = 3

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self.prev_battery = '0'
        self.peak_level = 0
        self.mute_statuses = {
            'RF': False,
            'RX': False,
            'TX': False,
        }
        self.squelch = 0
        self.rf_peaks = [0] * self.ANTENNA_COUNT
        self.tx_offset = 0
        
        self.report_map = {
            **self.report_map,
            SennheiserMicReportEnum.Msg: self.set_msg,
            SennheiserMicReportEnum.RFLevel1: self.set_rf_level_1,
            SennheiserMicReportEnum.RFLevel2: self.set_rf_level_2,
            SennheiserMicReportEnum.Squelch: self.set_squelch,
        }

    def ch_json(self):
        return {
            **super().ch_json(),
            'squelch': self.squelch,
            'status': self.tx_state(),
        }

    def set_msg(self, *messages):
        pass

    def set_rf_level_1(self, rf_level, peak_level):
        pass

    def set_rf_level_2(self, rf_level, peak_level):
        pass

    def set_squelch(self, squelch_level):
        pass

    def tx_state(self):
        # WCCC Specific State for unassigned microphones
        if self.rx.rx_com_status in ['DISCONNECTED', 'CONNECTING']:
            return 'RX_COM_ERROR'

        if (time.time() - self.peakstamp) < PEAK_TIMEOUT:
            return 'AUDIO_PEAK'

        if (self.mute_statuses['RF']):
            if (time.time() - self.timestamp) > BATTERY_TIMEOUT:
                return 'TX_COM_ERROR'

            return 'TX_OFF'

        return 'OK'

    
