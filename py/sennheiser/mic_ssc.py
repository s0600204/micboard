# ~ import time

# ~ from channel import ChannelDeviceReportEnum
# ~ from mic import BATTERY_TIMEOUT, WirelessMicBatteryStatus, WirelessMicReportEnum
from sennheiser.mic import (
    # ~ SennheiserMicReportEnum,
    WirelessSennheiserMic,
)
# ~ from util import WIRELESS_QUERY_QUEUE_INTERVAL


class WirelessSSCMic(WirelessSennheiserMic):

    def translate_from_json(self, json_string):
        py_repr = json.loads(json_string)
        elem_list = []
        # todo: walk object
        osc_path = f"/{ '/'.join(elem_list) }"
        osc_value = None
        return (osc_path, osc_value)

    def translate_to_json(self, osc_path, osc_value=None):
        return json.dumps(self.translate_to_dict(osc_path, osc_value))

    def translate_to_dict(self, osc_path, osc_value=None):
        split_path = osc_path.split('/')[1:]
        split_path.reverse()
        output = osc_value
        for elem in split_path:
            output = { elem: output }
        return output
