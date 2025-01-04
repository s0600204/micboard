import logging

from shure.mic import WirelessShureMic


class WirelessAXTDMic(WirelessShureMic):
    
    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def parse_sample(self, split):
        self.set_antenna(split[7])
        self.set_rf_level(split[9])
        self.set_audio_level(split[6])
        self.set_tx_quality(split[3])
        # TO TEST
        self.process_audio_bitmap(split[4])

    def set_audio_level(self, audio_level):
        self.audio_level = int(audio_level) - 20

    def set_frequency(self, frequency):
        super().set_frequency(frequency.lstrip('0'))

    def set_rf_level(self, rf_level):
        self.rf_level = int(100 * (float(rf_level) / 115))

    def set_tx_offset(self, tx_offset):
        if tx_offset != '255':
            self.tx_offset = int(tx_offset) - 12
