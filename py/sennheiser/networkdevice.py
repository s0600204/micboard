from channel import chart_update_list, data_update_list
from networkdevice import NetworkDevice


# Sennheiser receivers (broadly) use one of two protocols:
#
# * Media Control Protocol (MCP)
# * Sennheiser Sound Control Protocol (SSCP)
#
# For now, we only support the former.
class SennheiserNetworkDevice(NetworkDevice):

    PORT = 53212
    ENCODING = 'ascii'


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
        

    
