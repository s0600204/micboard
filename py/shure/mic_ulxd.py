from shure.mic_qulxd import WirelessQULXDMic


class WirelessULXDMic(WirelessQULXDMic):

    MODELS = {
        'ULXD4S' : { 'channels': 1, },
        'ULXD4D' : { 'channels': 2, },
        'ULXD4Q' : { 'channels': 4, },
    }

    DCID_NAME_MAPPING = {
        'ULX-DSingle'    : 'ULXD4S',
        'ULX-D1GSingle'  : 'ULXD4S',
        'ULX-DIsmSingle' : 'ULXD4S',

        'ULX-DDual'      : 'ULXD4D',
        'ULX-D1GDual'    : 'ULXD4D',
        'ULX-DIsmDual'   : 'ULXD4D',

        'ULX-DQuad'      : 'ULXD4Q',
        'ULX-D1GQuad'    : 'ULXD4Q',
        'ULX-DIsmQuad'   : 'ULXD4Q',
    }
