BASE_CONST = {}


BASE_CONST['uhfr'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'WirelessMic',
    'CHANNEL_CLASS' : 'WirelessUHFRMic',
    'PROTOCOL': 'UDP',
    'ch_const' : {},
    'base_const': {
        'getAll' : [
            '* GET {} CHAN_NAME *',
            '* GET {} BATT_BARS *',
            '* GET {} GROUP_CHAN *'
        ],
        'query' : [
            '* GET {} CHAN_NAME *',
            '* GET {} TX_BAT *',
            '* GET {} GROUP_CHAN *'
        ],
    },
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
    'ch_const' : {},
    'base_const' : {
        'getAll' : ['< GET {} ALL >'],
        'query' : [
            '< GET {} CHAN_NAME >',
            '< GET {} BATT_BARS >'
        ],
    },
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
    'ch_const' : {},
    'base_const': {
        'getAll' : ['< GET {} ALL >'],
        'query' : [
            '< GET {} CHAN_NAME >',
            '< GET {} BATT_BARS >'
        ],
    },
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
    'ch_const' : {},
    'base_const' : {
        'getAll' : ['< GET {} ALL >'],
        'query' : [
            '< GET {} CHAN_NAME >',
            '< GET {} TX_BATT_BARS >'
        ],
    },
    'DCID_MODEL' : {
        'AD4D': 2,
        'AD4Q': 4,
    }
}

BASE_CONST['p10t'] = {
    'MANUFACTURER' : 'Shure',
    'DEVICE_CLASS' : 'IEM',
    'PROTOCOL': 'TCP',
    'ch_const' : {
        'frequency': 'FREQUENCY',
        'audio_level_l': 'AUDIO_IN_LVL_L',
        'audio_level_r': 'AUDIO_IN_LVL_R',
        'name': 'CHAN_NAME',
        'tx_offset': 'TX_OFFSET'
    },
    'base_const' : {
        'getAll' : [
            '< GET {} CHAN_NAME >\r\n',
            '< GET {} FREQUENCY >\r\n'
        ],
        'query' : ['< GET {} CHAN_NAME >\r\n'],
    },
    'DCID_MODEL' : {
        'PSM1KTx': 2,
    }
}
