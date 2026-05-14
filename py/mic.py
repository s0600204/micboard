import enum
import time

from channel import ChannelDevice, data_update_list


BATTERY_TIMEOUT = 30*60
PEAK_TIMEOUT = 10


# Keep values in sync with the keys of `BatteryStates` in js/channelview.js
class WirelessMicBatteryStatus(enum.Enum):
    Good = 'good'
    Replace = 'replace'
    Critical = 'critical'
    Unknown = 'off'

class WirelessMicReportEnum(enum.Enum):
    AFLevel = enum.auto()
    Antenna = enum.auto()
    Battery = enum.auto()
    RFLevels = enum.auto()
    RXGain = enum.auto()
    Squelch = enum.auto()
    TXGain = enum.auto()

# https://stackoverflow.com/questions/17027878/algorithm-to-find-the-most-significant-bit
def MSB(audio_level):
    bitpos = 0
    while audio_level != 0:
        bitpos = bitpos + 1
        audio_level = audio_level >> 1
    return bitpos

class WirelessMic(ChannelDevice):

    ANTENNA_COUNT = 2
    BATTERY_LEVEL_MAP = {}
    BATTERY_SEGMENTS = 5

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)
        self.battery = 0
        self.battery_status = WirelessMicBatteryStatus.Unknown
        self.prev_battery = 0
        self.audio_level = 0
        self.rf_levels = [0] * self.ANTENNA_COUNT
        self.squelch = {'db': None, 'perc': None, 'str': None}
        self.antenna = 'XX'
        self.peakstamp = time.time() - 60
        self.rx_gain = None
        self.tx_gain = None

        self.report_map = {
            **self.report_map,
            WirelessMicReportEnum.AFLevel: self.set_audio_level,
            WirelessMicReportEnum.Antenna: self.set_antenna,
            WirelessMicReportEnum.Battery: self.set_battery,
            WirelessMicReportEnum.RFLevels: self.set_rf_levels,
            WirelessMicReportEnum.RXGain: self.set_rx_gain,
            WirelessMicReportEnum.Squelch: self.set_squelch,
            WirelessMicReportEnum.TXGain: self.set_tx_gain,
        }

    def set_antenna(self, antenna):
        self.antenna = antenna

    def set_peak_flag(self):
        self.peakstamp = time.time()
        if self not in data_update_list:
            data_update_list.append(self)

    def set_audio_level(self, audio_level):
        pass

    def set_battery(self, level):
        if level not in self.BATTERY_LEVEL_MAP:
            return

        self.battery = self.BATTERY_LEVEL_MAP[level][0]
        self.battery_status = self.BATTERY_LEVEL_MAP[level][1]

        if self.battery_status != WirelessMicBatteryStatus.Unknown:
            self.prev_battery = level
            self.timestamp = time.time()
        elif (time.time() - self.timestamp) < BATTERY_TIMEOUT:
            self.battery_status = self.BATTERY_LEVEL_MAP[self.prev_battery][1]

    def set_rf_levels(self, antenna, rf_level):
        pass

    def set_rx_gain(self, rx_gain):
        pass

    def set_squelch(self, squelch_level):
        pass

    def set_tx_gain(self, tx_gain):
        pass

    def ch_json(self):
        return {
            **super().ch_json(),
            'antenna': self.antenna,
            'audio_level': self.audio_level,
            'battery': self.battery,
            'battery_segments': self.BATTERY_SEGMENTS,
            'battery_status': self.battery_status.value,
            'rf_levels': self.rf_levels,
            'rx_gain': self.rx_gain,
            'squelch': self.squelch['str'],
            'tx_gain': self.tx_gain,
        }

    def ch_json_mini(self):
        data = self.ch_json()
        data['timestamp'] = time.time()
        del data['raw']
        return data

    def chart_json(self):
        return {
            'audio_level': self.audio_level,
            'rf_levels': self.rf_levels,
            'slot': self.slot,
            'squelch_level': self.squelch['perc'],
            'type': self.rx.type,
            'timestamp': time.time()
        }
