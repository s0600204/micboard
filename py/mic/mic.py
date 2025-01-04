import time
import logging
from math import ceil
from datetime import timedelta

from device_config import BASE_CONST
from channel import ChannelDevice, data_update_list


BATTERY_TIMEOUT = 30*60
PEAK_TIMEOUT = 10


# https://stackoverflow.com/questions/17027878/algorithm-to-find-the-most-significant-bit
def MSB(audio_level):
    bitpos = 0
    while audio_level != 0:
        bitpos = bitpos + 1
        audio_level = audio_level >> 1
    return bitpos

class WirelessMic(ChannelDevice):
    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)
        self.battery = 255
        self.prev_battery = 255
        self.audio_level = 0
        self.rf_level = 0
        self.antenna = 'XX'
        self.peakstamp = time.time() - 60
        self.tx_offset = 255

    def set_antenna(self, antenna):
        self.antenna = antenna

    def set_peak_flag(self):
        self.peakstamp = time.time()
        if self not in data_update_list:
            data_update_list.append(self)

    def set_audio_level(self, audio_level):
        pass

    def set_rf_level(self, rf_level):
        pass

    def set_battery(self, level):
        pass

    def set_tx_offset(self, tx_offset):
        pass

    def ch_json(self):
        return {
            **super().ch_json(),
            'antenna': self.antenna,
            'audio_level': self.audio_level,
            'battery': self.battery,
            'rf_level': self.rf_level,
            'tx_offset': self.tx_offset,
        }

    def ch_json_mini(self):
        data = self.ch_json()
        data['timestamp'] = time.time()
        del data['raw']
        return data

    def chart_json(self):
        return {
            'audio_level': self.audio_level,
            'rf_level': self.rf_level,
            'slot': self.slot,
            'type': self.rx.type,
            'timestamp': time.time()
        }

    def parse_sample(self, split):
        pass

    def parse_report(self, split):
        pass
