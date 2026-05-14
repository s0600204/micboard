import enum

from channel import ChannelDeviceReportEnum,
from sennheiser.charger_ssc import SSCCharger


class L6000ChargerReportEnum(enum.Enum):
    Accu1Detect = enum.auto()
    Accu2Detect = enum.auto()
    Accu1Status = enum.auto()
    Accu2Status = enum.auto()


battery_template = {
    'is_present': False,
}


class L6000Charger(SSCCharger):

    NAME = 'L 6000'

    BATTERY_COUNT = 2
    REPORT_MAPPING = {
        '/slot/subslot1/accu_detection' : L6000ChargerReportEnum.Accu1Detect,
        '/slot/subslot2/accu_detection' : L6000ChargerReportEnum.Accu2Detect,
        '/slot/subslot1/accu_parameter' : L6000ChargerReportEnum.Accu1Status,
        '/slot/subslot2/accu_parameter' : L6000ChargerReportEnum.Accu2Status,
        '/device/name'                  : ChannelDeviceReportEnum.Name,
    }
    MODELS = {
        'l6000': { 'channels': 4, 'name': 'L 6000' },
    }


    def __init__(self, rx, cfg):
        super().__init__(rx, cfg)

        self._batteries = [battery_template, battery_template]

        self.report_map = {
            **self.report_map,
            L6000ChargerReportEnum.Accu1Detect: lambda data: self.set_accu_detect(0, data),
            L6000ChargerReportEnum.Accu2Detect: lambda data: self.set_accu_detect(1, data),
            L6000ChargerReportEnum.Accu1Status: lambda data: self.set_accu_status(0, data),
            L6000ChargerReportEnum.Accu2Status: lambda data: self.set_accu_status(1, data),
        }

    def build_monitoring_request(self):
        return json.dumps({
            'osc': {
                'state': {
                    'subscribe': [{
                        "#": {
                            # ~ 'count': 100_000, # default: 1000,
                            'lifetime': WIRELESS_QUERY_QUEUE_INTERVAL, # seconds; default: 10
                            # ~ 'max': 0, # milliseconds; default: 0
                            # ~ 'min': 0, # milliseconds; default: 0
                        },
                        'device': {
                            'name': None,
                        },
                        f'slot{self.channel}': {
                            'subslot1': {
                                'accu_detection': None, # Is there a battery present?
                                'accu_parameter': None, # Battery status
                            },
                            'subslot2': {
                                'accu_detection': None,
                                'accu_parameter': None,
                            },
                        },
                    }]
                }
            }
        })

    def build_get_all_strings(self):
        return [
            # ~ self.translate_to_json('/device/identity/version'),
            # ~ self.translate_to_json('/device/identity/product'),
            *self.build_query_strings(),
        ]

    def build_query_strings(self):
        return [
            self.build_monitoring_request(),
        ]

    def set_accu_detect(self, battery, is_present):
        self._batteries[battery]['is_present'] = bool(is_present)

    def set_accu_status(self, battery, status):
        current_status = self._batteries[battery]

        current_status['temperature']    = status[0] # [°C]
        current_status['voltage']        = status[1] # [mV]
        current_status['capacity']       = status[2] # [mAh]
        current_status['current']        = status[3] # [mA]
        current_status['energy']         = status[4] # [mWh]
        current_status['operating_time'] = (*status[5:7],) # [hr], [min]
        current_status['charge_level']   = status[7] # [%]
        current_status['cycle count']    = status[8] # [-]
        current_status['battery_health'] = status[9] # [%]
        current_status['time_to_full']   = (*status[10:12],) # [h], [min]

        self._batteries[battery] = current_status

    def set_name(self, chan_name):
        # Name is returned with the device's MAC Address appended.
        # e.g.: "Digital6000-001b66xxxxxx"
        chan_name = chan_name.rsplit('-', 1)[0]
        self.chan_name_raw = chan_name
        
