import time

from channel import ChannelDeviceReportEnum
from iem.iem import WirelessIEMReportEnum
from shure.iem import ShureIEMReportEnum, WirelessShureIEM


class WirelessP10tIEM(WirelessShureIEM):

    REPORT_MAPPING = {
        'AUDIO_IN_LVL_L' : WirelessIEMReportEnum.AFLevelL,
        'AUDIO_IN_LVL_R' : WirelessIEMReportEnum.AFLevelR,
        'CHAN_NAME'      : ChannelDeviceReportEnum.Name,
        'FREQUENCY'      : ChannelDeviceReportEnum.Frequency,
    }

    def build_get_all_strings(self):
        return [
            f'< GET {self.slot} CHAN_NAME >\r\n',
            f'< GET {self.slot} FREQUENCY >\r\n',
        ]

    def build_query_strings(self):
        return [
            f'< GET {self.slot} CHAN_NAME >\r\n',
        ]

    def chart_json(self):
        return {
            'audio_level_l': self.audio_level_l,
            'audio_level_r': self.audio_level_r,
            'slot': self.slot,
            'type': self.rx.type,
            'timestamp': time.time()
        }

    def ch_json(self):
        return {
            **super().ch_json(),
            'status': self.ch_state(),
            'audio_level_l' : self.audio_level_l,
            'audio_level_r' : self.audio_level_r,
        }

    def ch_json_mini(self):
        data = self.ch_json()
        data['timestamp'] = time.time()
        del data['raw']
        return data

    def ch_state(self):
        if self.rx.rx_com_status in ['DISCONNECTED', 'CONNECTING']:
            return 'RX_COM_ERROR'

        if self.rx.rx_com_status == 'CONNECTED':
            return 'UNASSIGNED'

        return 'TX_COM_ERROR'

    def monitoring_disable(self):
        return f'< SET {self.slot} METER_RATE 0 >'

    def monitoring_enable(self, interval):
        return f'< SET {self.slot} METER_RATE {int(interval * 1000):05d} >'

    def parse_audio_level(self, audio_level):
        audio_level = int(audio_level)
        if audio_level < 10272:
            return 0
        if audio_level < 23728:
            return 10
        if audio_level < 85488:
            return 20
        if audio_level < 246260:
            return 30
        if audio_level < 641928:
            return 40
        if audio_level < 1588744:
            return 50
        if audio_level < 2157767:
            return 60
        if audio_level < 2502970:
            return 70
        return 80

    def set_audio_level_left(self, audio_level):
        self.audio_level_l = self.parse_audio_level(audio_level)

    def set_audio_level_right(self, audio_level):
        self.audio_level_r = self.parse_audio_level(audio_level)
        chart_update_list.append(self.chart_json())
