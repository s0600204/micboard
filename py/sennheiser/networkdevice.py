import json

from channel import chart_update_list, data_update_list
from networkdevice import NetworkDevice
from util import NetworkProtocol

# ~ from sennheiser.charger_l6000 import L6000Charger
from sennheiser.mic_mcp import WirelessMCPMic
from sennheiser.mic_ewdx import WirelessEWDXMic


# Sennheiser receivers (broadly) use one of two protocols:
#
# * Media Control Protocol (MCP)
# * Sennheiser Sound Control Protocol (SSC)
class SennheiserMCPNetworkDevice(NetworkDevice):

    PORT = 53212
    ENCODING = 'ascii'
    DEVICE_CLASS_MAP = {
        'mcp_mic': WirelessMCPMic,
    }
    NETWORK_PROTOCOL = NetworkProtocol.UDP
    NETWORK_SHARED_PORT = True

    def parse_raw_rx(self, data):
        msg = data.split()
        # There is always only ever one channel on an MCP device.
        ch = self.channels[0]
        ch.parse_report(msg[0], msg[1:])

        if msg[0] in ch.CYCLIC_ATTRS:
            if msg[0] == 'Config':
                # The `Config` cyclic attribute is always the last to be received,
                # and so can be used to trigger the appending of chart data
                chart_update_list.append(self.channels[0].chart_json())
        else:
            if ch not in data_update_list:
                data_update_list.append(ch)

    def split_raw_rx(self, data):
        # A message from an MCP device will always start with
        # an uppercase ASCII letter. Thus, ignore anything else.
        payload = data.strip()
        if 64 < payload[0] < 91:
            return str(payload, self.ENCODING).split('\r')
        return []


class SennheiserSSCNetworkDevice(NetworkDevice):

    PORT = 45
    DEVICE_CLASS_MAP = {
        'ewdx_mic': WirelessEWDXMic,
        # ~ 'l6000_charger': L6000Charger,
    }
    NETWORK_PROTOCOL = NetworkProtocol.UDP
    # ~ NETWORK_SHARED_PORT = True

    def parse_raw_rx(self, data: tuple):
        osc_path, osc_value = data

        ch_pos = None
        if osc_path.startswith('/rx'):
            ch_pos = 3
        elif osc_path.startswith('/m/rx') or osc_path.startswith('/slot'):
            ch_pos = 5
        elif osc_path.startswith('/mates/tx'):
            ch_pos = 9

        if ch_pos:
            ch_pos_to = osc_path.index('/', ch_pos)
            ch = get_device_by_channel(osc_path[ch_pos:ch_pos_to])
            osc_path = osc_path[:ch_pos] + osc_path[ch_pos_to:]
            ch.parse_report(osc_path, osc_value)


    def split_raw_rx(self, data: str):
        try:
            py_repr = json.loads(data)
        except json.decoder.JSONDecodeError:
            return []

        breadcrumbs = []
        lines = []

        def walk(node):
            for key, value in node.items():
                breadcrumbs.append(key)
                if isinstance(value, dict):
                    walk(value)
                else:
                    lines.append((f"/{ '/'.join(breadcrumbs) }", value))
                breadcrumbs.pop()

        walk(py_repr)
        return lines
