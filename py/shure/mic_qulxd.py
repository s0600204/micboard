import logging

from shure.mic import WirelessShureMic


PEAK_LEVEL = {
    'qlxd': 80,
    'ulxd': 80
}

class WirelessQULXDMic(WirelessShureMic):
    
    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def parse_sample(self, split):
        self.set_antenna(split[3])
        self.set_rf_level(split[4])
        self.set_audio_level(split[5])

    def set_audio_level(self, audio_level):
        audio_level = 2 * int(audio_level)

        if audio_level >= PEAK_LEVEL[self.rx.type]:
            self.set_peak_flag()

        self.audio_level = audio_level

    def set_rf_level(self, rf_level):
        self.rf_level = int(100 * (float(rf_level) / 115))

    def set_tx_offset(self, tx_offset):
        if tx_offset != '255':
            self.tx_offset = int(tx_offset)
