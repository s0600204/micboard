import time


discovered = []


def add_rx_to_dlist(ip, rx_type, channels):
    rx = next((x for x in discovered if x['ip'] == ip), None)

    if rx:
        rx['timestamp'] = time.time()

    else:
        discovered.append({
            'ip' : ip,
            'type': rx_type,
            'channels': channels,
            'timestamp': time.time()
        })

    discovered.sort(key=lambda x: x['ip'])


def time_filterd_discovered_list():
    out = []
    for i in discovered:
        if (time.time() - i['timestamp']) < 30:
            out.append(i)
    return out

