import logging

from mic.mic import MSB
from shure.mic import WirelessShureMic


class WirelessUHFRMic(WirelessShureMic):
    
    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

    def parse_sample(self, split):
        self.set_antenna(split[3])
        self.set_rf_level(split[4])
        self.set_battery(split[6])
        self.set_audio_level(split[7])
        # TO TEST
        self.process_audio_bitmap(split[7])

    def set_audio_level(self, audio_level):
        self.audio_level = int(ceil(MSB(int(audio_level)) * (100./8)))

    def set_rf_level(self, rf_level):
        self.rf_level = int(100 * ((100 - float(rf_level)) / 80))
