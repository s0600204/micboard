from datetime import timedelta
import enum
import time

from mic import BATTERY_TIMEOUT, PEAK_TIMEOUT, WirelessMic, WirelessMicBatteryStatus


class ShureMicReportEnum(enum.Enum):
    PowerLock = enum.auto()
    Runtime = enum.auto()
    TXQuality = enum.auto()


class WirelessShureMic(WirelessMic):

    BATTERY_LEVEL_MAP = {
        '001': (1, WirelessMicBatteryStatus.Critical),
        '002': (2, WirelessMicBatteryStatus.Critical),
        '003': (3, WirelessMicBatteryStatus.Replace),
        '004': (4, WirelessMicBatteryStatus.Good),
        '005': (5, WirelessMicBatteryStatus.Good),
        '255': (0, WirelessMicBatteryStatus.Unknown),
    }
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

    def build_get_all_strings(self):
        return [
            f'< GET {self.channel} ALL >',
        ]

    def monitoring_disable(self):
        return f'< SET {self.channel} METER_RATE 0 >'

    def monitoring_enable(self, interval):
        return f'< SET {self.channel} METER_RATE {int(interval * 1000):05d} >'

    def parse_sample(self, split):
        pass

    def process_audio_bitmap(self, bitmap):
        bitmap = int(bitmap)
        if bitmap >> 7:
            self.set_peak_flag()

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

        if self.battery == 255:
            if (time.time() - self.timestamp) > BATTERY_TIMEOUT:
                return 'TX_COM_ERROR'

            return 'TX_OFF'

        return 'OK'
