import enum
from math import ceil

from channel import ChannelDeviceReportEnum
from mic import MSB, WirelessMicBatteryStatus, WirelessMicReportEnum
from shure.mic import ShureMicReportEnum, WirelessShureMic
from util import NetworkProtocol


class UHFRReportEnum(enum.Enum):
    TXTrim = enum.auto()


class WirelessUHFRMic(WirelessShureMic):

    NAME = 'UHF-R'

    ANTENNA_COUNT = 2
    BATTERY_LEVEL_MAP = {
        '1': (1, WirelessMicBatteryStatus.Critical),
        '2': (2, WirelessMicBatteryStatus.Critical),
        '3': (3, WirelessMicBatteryStatus.Replace),
        '4': (4, WirelessMicBatteryStatus.Good),
        '5': (5, WirelessMicBatteryStatus.Good),
        'U': (0, WirelessMicBatteryStatus.Unknown),
    }
    MODELS = {
        'UR4S' : { 'channels': 1, },
        'UR4D' : { 'channels': 2, },
    }
    REPORT_MAPPING = {
        'AUDIO_GAIN' : WirelessMicReportEnum.RXGain,
        # 'AUDIO_INDICATOR'
        'CHAN_NAME'  : ChannelDeviceReportEnum.Name,
        'FREQUENCY'  : ChannelDeviceReportEnum.Frequency,
        # 'FRONT_PANEL_LOCK'
        # 'GROUP_CHAN'       # Frequency Group and Channel designation
        # 'MUTE'             # Audio Mute (on receiver)
        'SQUELCH'    : WirelessMicReportEnum.Squelch,
        'TX_BAT'     : WirelessMicReportEnum.Battery,
        # 'TX_BAT_MINS'      # {UNKNOWN}
        # 'TX_BAT_TYPE'      # {UNKNOWN, ALKALINE, NIMH, LITHIUM}
        'TX_GAIN'    : WirelessMicReportEnum.TXGain,
        'TX_LOCK'    : ShureMicReportEnum.PowerLock,
        # 'TX_IR_BAT_TYPE'   # TX battery type to set on sync
        # 'TX_IR_CUSTOM_GPS' # Whether to copy custom frequency groups from RX to TX
        # 'TX_IR_GAIN'       # TX gain level to set on sync
        # 'TX_IR_LOCK'       # TX lock setting to set on sync
        # 'TX_IR_POWER'      # TX power setting to set on sync
        # 'TX_IR_TRIM'       # TX trim to set on sync
        # 'TX_POWER'         # TX power {NORM [10mW], HIGH [50mW]}
        'TX_TRIM'    : UHFRReportEnum.TXTrim,
    }

    DCID_NAME_MAPPING = {
        'UR4S' : 'UR4S',
        'UR4D' : 'UR4D',
    }

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self.__tx_gain = None
        self.__tx_trim = None

        self.report_map = {
            **self.report_map,
            UHFRReportEnum.TXTrim: self.set_tx_trim,
        }

    def build_get_all_strings(self) -> list[str]:
        return self.build_query_strings()

    def build_query_strings(self):
        return [
            f'* GET {self.channel} CHAN_NAME *',
            f'* GET {self.channel} SQUELCH *',
            f'* GET {self.channel} TX_BAT *',
            f'* GET {self.channel} TX_GAIN *',
            f'* GET {self.channel} TX_LOCK *',
            f'* GET {self.channel} TX_TRIM *',
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

    def set_power_lock(self, power_lock):
        if power_lock in ['UNKNOWN', 'UNLOCK', 'FREQ']:
            self.power_lock = 'OFF'
        elif power_lock in ['POWER', 'FREQ_AND_POWER']:
            self.power_lock = 'ON'

    def set_rf_levels(self, antenna, rf_level):
        self.rf_levels[antenna] = int(100 * ((100 - float(rf_level)) / 80))

    def set_rx_gain(self, rx_gain):
        self.rx_gain = -int(rx_gain)

    def set_squelch(self, squelch_level):
        # value from device:     0 - 20
        # value on TX display: -10 - 10 (no unit stated)
        squelch = int(squelch_level) - 10
        if squelch != 0:
            self.squelch['str'] = f'squelch: {squelch}'
        else:
            self.squelch['str'] = None

    def set_tx_gain(self, tx_gain):
        if tx_gain == 'UNKNOWN':
            self.__tx_gain = None
            self.tx_gain = None
        else:
            # value from device:     0 - 30
            # value on TX display: -10 - 20 dB
            self.__tx_gain = int(tx_gain) - 10
            if self.__tx_trim:
                self.tx_gain = self.__tx_gain + self.__tx_trim

    def set_tx_trim(self, tx_trim):
        if tx_trim == 'UNKNOWN':
            self.__tx_trim = None
            self.tx_gain = None
        else:
            # values from device: -10, 0, 15
            self.__tx_trim = int(tx_trim)
            if self.__tx_gain:
                self.tx_gain = self.__tx_gain + self.__tx_trim
