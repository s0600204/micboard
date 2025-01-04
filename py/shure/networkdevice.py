
from networkdevice import NetworkDevice

from shure.mic_axtd import WirelessAXTDMic
from shure.mic_qulxd import WirelessQULXDMic
from shure.mic_uhfr import WirelessUHFRMic


class ShureNetworkDevice(NetworkDevice):

    PORT = 2202
    DEVICE_CLASS_MAP = {
        'axtd': WirelessAXTDMic,
        'qlxd': WirelessQULXDMic,
        'uhfr': WirelessUHFRMic,
        'ulxd': WirelessQULXDMic,
    }
