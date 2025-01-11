import time
import select
import queue
import atexit
import sys
import socket
import logging


from channel import chart_update_list, data_update_list
from iem import WirelessIEM
from mic import WirelessMic
from shure.networkdevice import ShureNetworkDevice, ShureNetworkUDPDevice
from util import WIRELESS_QUERY_QUEUE_INTERVAL


NETWORK_DEVICE_CLASSES = [
    ShureNetworkDevice,
    ShureNetworkUDPDevice,
]

NetworkDevices = []
DeviceMessageQueue = queue.Queue()


def get_network_device_by_ip(ip):
    return next((x for x in NetworkDevices if x.ip == ip), None)

def get_network_device_by_slot(slot):
    for networkdevice in NetworkDevices:
        for channel in networkdevice.channels:
            if channel.slot == slot:
                return channel

def check_add_network_device(ip, type):
    net = get_network_device_by_ip(ip)
    if net:
        return net

    for net_device_class in NETWORK_DEVICE_CLASSES:
        if type in net_device_class.DEVICE_CLASS_MAP:
            net = net_device_class(ip, type)
            NetworkDevices.append(net)
            return net

    logging.critical(f"Unrecognised Device type {type}")
    return None

def get_supported_device_model_info():
    device_info = {}

    for net_device_class in NETWORK_DEVICE_CLASSES:
        for device_type, device_class in net_device_class.DEVICE_CLASS_MAP.items():
            device_info[device_type] = {
                'name': device_class.NAME,
                'models': {},
            }
            models = getattr(device_class, 'MODELS', {}).items()
            for model_id, model_definition in models:
                device_info[device_type]['models'][model_id] = {
                    'name': model_definition.get('name', model_id),
                    'channels': model_definition['channels'],
                }
    return device_info

def get_supported_device_model_types():
    models = {
        'all': [],
        'mic': [],
        'iem': [],
    }

    for net_device_class in NETWORK_DEVICE_CLASSES:
        for devtype, devclass in net_device_class.DEVICE_CLASS_MAP.items():
            if issubclass(devclass, WirelessIEM):
                models['iem'].append(devtype)
            elif issubclass(devclass, WirelessMic):
                models['mic'].append(devtype)

    models['all'] = models['mic'] + models['iem']

    models['all'].sort()
    models['mic'].sort()
    models['iem'].sort()
    return models

def get_supported_device_models():
    models = {
        'all': [],
        'mic': [],
        'iem': [],
    }

    for devtype, devclass in ShureNetworkDevice.DEVICE_CLASS_MAP.items():
        if issubclass(devclass, WirelessIEM):
            models['iem'].append(devtype)
        elif issubclass(devclass, WirelessMic):
            models['mic'].append(devtype)

    models['all'] = models['mic'] + models['iem']

    models['all'].sort()
    models['mic'].sort()
    models['iem'].sort()
    return models

def watchdog_monitor():
    for rx in (rx for rx in NetworkDevices if rx.rx_com_status == 'CONNECTED'):
        if (int(time.perf_counter()) - rx.socket_watchdog) > 5:
            logging.debug('disconnected from: %s', rx.ip)
            rx.socket_disconnect()

    for rx in (rx for rx in NetworkDevices if rx.rx_com_status == 'CONNECTING'):
        if (int(time.perf_counter()) - rx.socket_watchdog) > 2:
            rx.socket_disconnect()


    for rx in (rx for rx in NetworkDevices if rx.rx_com_status == 'DISCONNECTED'):
        if (int(time.perf_counter()) - rx.socket_watchdog) > 20:
            rx.socket_connect()

def WirelessQueryQueue():
    while True:
        for rx in (rx for rx in NetworkDevices if rx.rx_com_status == 'CONNECTED'):
            strings = rx.get_query_strings()
            for string in strings:
                rx.writeQueue.put(string)
        time.sleep(WIRELESS_QUERY_QUEUE_INTERVAL)

def ProcessRXMessageQueue():
    while True:
        rx, msg = DeviceMessageQueue.get()
        rx.parse_raw_rx(msg)


def SocketService():
    for rx in NetworkDevices:
        rx.socket_connect()

    while True:
        watchdog_monitor()
        readrx = [rx for rx in NetworkDevices if rx.rx_com_status in ['CONNECTING', 'CONNECTED']]
        writerx = [rx for rx in readrx if not rx.writeQueue.empty()]

        read_socks, write_socks, error_socks = select.select(readrx, writerx, readrx, .2)

        for rx in read_socks:
            try:
                data, address = rx.f.recvfrom(1024)
                rx = get_network_device_by_ip(address[0])
            except:
                rx.socket_disconnect()
                break

            for line in rx.split_raw_rx(data):
                DeviceMessageQueue.put((rx, line))

            rx.socket_watchdog = int(time.perf_counter())
            rx.set_rx_com_status('CONNECTED')


        for rx in write_socks:
            string = rx.writeQueue.get()
            logging.debug("write: %s data: %s", rx.ip, string)
            try:
                rx.socket_send(string)
            except:
                logging.warning("TX ERROR IP: %s String: %s", rx.ip, string)


        for rx in error_socks:
            rx.set_rx_com_status('DISCONNECTED')



# @atexit.register
def on_exit():
    connected = [rx for rx in NetworkDevices if rx.rx_com_status == 'CONNECTED']
    for rx in connected:
        rx.disable_metering()
    time.sleep(50)
    print("IT DONE!")
    sys.exit(0)

# atexit.register(on_exit)
# signal.signal(signal.SIGTERM, on_exit)
# signal.signal(signal.SIGINT, on_exit)
