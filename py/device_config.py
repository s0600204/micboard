BASE_CONST = {}


BASE_CONST['uhfr'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'WirelessMic',
    'CHANNEL_CLASS' : 'WirelessUHFRMic',
    'PROTOCOL': 'UDP',
    'DCID_MODEL' : {
        'UR4S' : 1,
        'UR4D' : 2,
    }
}

BASE_CONST['qlxd'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'WirelessMic',
    'CHANNEL_CLASS' : 'WirelessQULXDMic',
    'PROTOCOL' : 'TCP',
    'DCID_MODEL' : {
        'QLX-DSingle' : 1,
        'QLX-D1GSingle' : 1,
        'QLX-DIsmSingle' : 1,
    }

}

BASE_CONST['ulxd'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'WirelessMic',
    'CHANNEL_CLASS' : 'WirelessQULXDMic',
    'PROTOCOL': 'TCP',
    'DCID_MODEL' : {
        'ULX-DSingle': 1,
        'ULX-D1GSingle' : 1,
        'ULX-DIsmSingle' : 1,
        'ULX-DDual': 2,
        'ULX-D1GDual' : 2,
        'ULX-DIsmDual' : 2,
        'ULX-DQuad': 4,
        'ULX-D1GQuad' : 4,
        'ULX-DIsmQuad' : 4,
    }
}

BASE_CONST['axtd'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'WirelessMic',
    'CHANNEL_CLASS' : 'WirelessAXTDMic',
    'PROTOCOL': 'TCP',
    'DCID_MODEL' : {
        'AD4D': 2,
        'AD4Q': 4,
    }
}

BASE_CONST['p10t'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'IEM',
    'CHANNEL_CLASS' : 'WirelessP10tIEM',
    'PROTOCOL': 'TCP',
    'DCID_MODEL' : {
        'PSM1KTx': 2,
    }
}
