import enum

from channel import ChannelDevice


class WirelessIEMReportEnum(enum.Enum):
    AFLevelL = enum.auto()
    AFLevelR = enum.auto()


class WirelessIEM(ChannelDevice):

    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self.audio_level_l = 0
        self.audio_level_r = 0

        self.report_map = {
            **self.report_map,
            WirelessIEMReportEnum.AFLevelL: self.set_audio_level_left,
            WirelessIEMReportEnum.AFLevelR: self.set_audio_level_right,
        }

    def set_audio_level_left(self, level):
        pass

    def set_audio_level_right(self, level):
        pass

    def parse_sample(self, split):
        pass
