from shure.mic_qulxd import WirelessQULXDMic


class WirelessQLXDMic(WirelessQULXDMic):

    MODELS = {
        'QLXD4S' : { 'channels': 1, },
    }

    DCID_NAME_MAPPING = {
        'QLX-DSingle'    : 'QLXD4S',
        'QLX-D1GSingle'  : 'QLXD4S',
        'QLX-DIsmSingle' : 'QLXD4S',
    }
    FCTN_NAME_MAPPING = {
        'QLXD4' : 'QLXD4S',
    }
