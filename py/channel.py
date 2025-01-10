import time
import re
from collections import defaultdict
import logging

import config
from device_config import BASE_CONST

chart_update_list = []
data_update_list = []


class ChannelDevice:
    def __init__(self, rx, cfg):
        self.rx = rx
        self.cfg = cfg
        self.chan_name_raw = 'SLOT {}'.format(cfg['slot'])
        self.channel = cfg['channel']
        self.timestamp = time.time() - 60
        self.frequency = '000000'
        self.slot = cfg['slot']
        self.raw = defaultdict(dict)
        self.CHCONST = BASE_CONST[self.rx.type]['ch_const']

    def monitoring_disable(self):
        return None

    def monitoring_enable(self, interval):
        return None

    def set_frequency(self, frequency):
        self.frequency = frequency[:3] + '.' + frequency[3:]

    def set_chan_name_raw(self, chan_name):
        chan_name = chan_name.replace('_', ' ')
        self.chan_name_raw = chan_name

    def get_chan_name(self):
        name = self.chan_name_raw.split()
        prefix = re.match("([A-Za-z]+)?([-]?)([0-9])+", name[0])

        chan_id = ''
        chan_name = ''

        if prefix:
            chan_id = name[0]
            chan_name = ' '.join(name[1:])
        elif name[0] == 'IEM' and len(name[1]) == 1:
            chan_id = ' '.join(name[:2])
            chan_name = ' '.join(name[2:])
        else:
            chan_name = self.chan_name_raw

        if 'chan_name_raw' in self.cfg:
            if self.cfg['chan_name_raw'] == self.chan_name_raw:
                if 'extended_id' in self.cfg:
                    if self.cfg['extended_id']:
                        chan_id = self.cfg['extended_id']

                if 'extended_name' in self.cfg:
                    if self.cfg['extended_name']:
                        chan_name = self.cfg['extended_name']

            elif 'SLOT' not in self.chan_name_raw:
                if 'extended_id' in self.cfg:
                    self.cfg.pop('extended_id')
                if 'extended_name' in self.cfg:
                    self.cfg.pop('extended_name')
                self.cfg.pop('chan_name_raw')
                config.save_current_config()

        return (chan_id, chan_name)

    def ch_json(self):
        name = self.get_chan_name()
        return {
            'channel': self.channel,
            'frequency': self.frequency,
            'id': name[0],
            'name': name[1],
            'name_raw': self.chan_name_raw,
            'raw': self.raw,
            'slot': self.slot,
            'type': self.rx.type,
        }

    def parse_raw_ch(self, data):
        split = data.split()
        self.raw[split[2]] = ' '.join(split[3:])

        try:
            if split[0] == 'SAMPLE' and split[2] == 'ALL':
                self.parse_sample(split)
                chart_update_list.append(self.chart_json())

            if split[0] in ['REP', 'REPLY', 'REPORT']:
                self.parse_report(split[2], split[3:])

                if self not in data_update_list:
                    data_update_list.append(self)

        except Exception as e:
            print("Index Error(TX): {}".format(data.split()))
            print(e)

    def parse_report(self, key, values):
        if key not in self.REPORT_MAPPING or self.REPORT_MAPPING[key] not in self.report_map:
            return
        self.report_map[self.REPORT_MAPPING[key]](*values)
