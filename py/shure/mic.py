import enum
import logging

from mic.mic import BATTERY_TIMEOUT, PEAK_TIMEOUT, WirelessMic, WirelessMicBatteryStatus


class ShureMicReportEnum(enum.Enum):
    PowerLock = enum.auto()
    Runtime = enum.auto()
    TXQuality = enum.auto()


class WirelessShureMic(WirelessMic):

    BATTERY_SEGMENTS = 5

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self.power_lock = ''
        self.quality = 255
        self.runtime = ''
        self.tx_offset = 255

        self.report_map = {
            **self.report_map,
            ShureMicReportEnum.PowerLock: self.set_power_lock,
            ShureMicReportEnum.Runtime: self.set_runtime,
            ShureMicReportEnum.TXQuality: self.set_tx_quality,
        }

    def ch_json(self):
        return {
            **super().ch_json(),
            'power_lock': self.power_lock,
            'quality': self.quality,
            'runtime': self.runtime,
            'status': self.tx_state(),
        }

    def monitoring_disable(self):
        return f'< SET {self.channel} METER_RATE 0 >'

    def monitoring_enable(self, interval):
        return f'< SET {self.channel} METER_RATE {int(interval * 1000):05d} >'

    def process_audio_bitmap(self, bitmap):
        bitmap = int(bitmap)
        if bitmap >> 7:
            self.set_peak_flag()

    def set_battery(self, level):
        if level == 'U':
            level = 255
        level = int(level)
        self.battery = level

        if 1 <= level <= 5:
            self.prev_battery = level
            self.timestamp = time.time()

        if (time.time() - self.timestamp) < BATTERY_TIMEOUT:
            if 4 <= self.battery <= 5 or self.battery == 255 and 4 <= self.prev_battery <= 5:
                self.battery_status = WirelessMicBatteryStatus.Good
            elif self.battery == 3 or self.battery == 255 and self.prev_battery == 3:
                self.battery_status = WirelessMicBatteryStatus.Replace
            elif 0 <= self.battery <= 2 or self.battery == 255 and 0 <= self.prev_battery <= 2:
                self.battery_status = WirelessMicBatteryStatus.Critical

    def set_chan_name_raw(self, *new_name):
        super().set_chan_name_raw(' '.join(new_name))

    def set_power_lock(self, power_lock):
        if power_lock in ['OFF', 'UNKN', 'UNKNOWN', 'NONE']:
            self.power_lock = 'OFF'
        elif power_lock in ['ON', 'ALL', 'POWER']:
            self.power_lock = 'ON'

    # https://stackoverflow.com/questions/1784952/how-get-hoursminutes
    def set_runtime(self, runtime):
        runtime = int(runtime)
        if 0 <= runtime <= 65532:
            self.runtime = str(timedelta(minutes=runtime))[:-3]
        else:
            self.runtime = ''

    def set_tx_quality(self, quality):
        self.quality = int(quality)

    def tx_state(self):
        # WCCC Specific State for unassigned microphones
        if self.rx.rx_com_status in ['DISCONNECTED', 'CONNECTING']:
            return 'RX_COM_ERROR'

        if (time.time() - self.peakstamp) < PEAK_TIMEOUT:
            return 'AUDIO_PEAK'
        # uncomment to ignore mic status of unassigned microphones
        # if not self.get_chan_name()[1]:
        #     return 'UNASSIGNED'

        if (self.battery == 255):
            if (time.time() - self.timestamp) > BATTERY_TIMEOUT:
                return 'TX_COM_ERROR'

            return 'TX_OFF'

        return 'OK'
