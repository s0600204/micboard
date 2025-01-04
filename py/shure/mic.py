import logging

from mic.mic import BATTERY_TIMEOUT, PEAK_TIMEOUT, WirelessMic


class WirelessShureMic(WirelessMic):

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self.power_lock = ''
        self.quality = 255
        self.runtime = ''
        self.tx_offset = 255

    def parse_report(self, split):
        if split[2] == self.CHCONST['battery']:
            self.set_battery(split[3])
        elif split[2] == self.CHCONST['runtime']:
            self.set_runtime(split[3])
        elif split[2] == self.CHCONST['name']:
            self.set_chan_name_raw(' '.join(split[3:]))
        elif split[2] == self.CHCONST['quality']:
            self.set_tx_quality(split[3])
        elif split[2] == self.CHCONST['frequency']:
            self.set_frequency(split[3])
        elif split[2] == self.CHCONST['tx_offset']:
            self.set_tx_offset(split[3])
        elif split[2] == self.CHCONST['power_lock']:
            self.set_power_lock(split[3])

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

        if (time.time() - self.timestamp) < BATTERY_TIMEOUT:
            if 4 <= self.battery <= 5:
                return 'GOOD'
            elif self.battery == 255 and 4 <= self.prev_battery <= 5:
                return 'PREV_GOOD'
            elif self.battery == 3:
                return 'REPLACE'
            elif self.battery == 255 and self.prev_battery == 3:
                return 'PREV_REPLACE'
                # return 'UNASSIGNED'
            elif 0 <= self.battery <= 2:
                return 'CRITICAL'
            elif self.battery == 255 and 0 <= self.prev_battery <= 2:
                return 'PREV_CRITICAL'

        return 'TX_COM_ERROR'



