import time
import queue
import socket
from collections import defaultdict
import logging

from device_config import BASE_CONST
from iem import IEM
import mic


class NetworkDevice:

    PORT = None
    ENCODING = 'UTF-8'
    METERING_INTERVAL = 0.1 # seconds

    def __init__(self, ip, type):
        self.ip = ip
        self.type = type
        self.channels = []
        self.rx_com_status = 'DISCONNECTED'
        self.writeQueue = queue.Queue()
        self.f = None
        self.socket_watchdog = int(time.perf_counter())
        self.raw = defaultdict(dict)

    def socket_connect(self):
        try:
            if BASE_CONST[self.type]['PROTOCOL'] == 'TCP':
                self.f = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
                self.f.settimeout(.2)
                self.f.connect((self.ip, self.PORT))


            elif BASE_CONST[self.type]['PROTOCOL'] == 'UDP':
                self.f = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP

            self.set_rx_com_status('CONNECTING')
            self.enable_metering(self.METERING_INTERVAL)

            for string in self.get_all():
                self.writeQueue.put(string)
        except socket.error as e:
            self.set_rx_com_status('DISCONNECTED')

        self.socket_watchdog = int(time.perf_counter())


    def socket_disconnect(self):
        self.f.close()
        self.set_rx_com_status('DISCONNECTED')
        self.socket_watchdog = int(time.perf_counter())

    def socket_send(self, message):
        if BASE_CONST[self.type]['PROTOCOL'] == 'TCP':
            self.f.sendall(bytearray(message, self.ENCODING))

        elif BASE_CONST[self.type]['PROTOCOL'] == 'UDP':
            self.f.sendto(bytearray(message, self.ENCODING), (self.ip, self.PORT))

    def fileno(self):
        return self.f.fileno()

    def set_rx_com_status(self, status):
        self.rx_com_status = status
        # if status == 'CONNECTED':
        #     print("Connected to {} at {}".format(self.ip,datetime.datetime.now()))
        # elif status == 'DISCONNECTED':
        #     print("Disconnected from {} at {}".format(self.ip,datetime.datetime.now()))

    def add_channel_device(self, cfg):
        if 'CHANNEL_CLASS' in BASE_CONST[self.type]:
            py_class = getattr(mic, BASE_CONST[self.type]['CHANNEL_CLASS'])
            self.channels.append(py_class(self, cfg))
        elif BASE_CONST[self.type]['DEVICE_CLASS'] == 'WirelessMic':
            self.channels.append(mic.WirelessMic(self, cfg))
        elif BASE_CONST[self.type]['DEVICE_CLASS'] == 'IEM':
            self.channels.append(IEM(self, cfg))

    def get_device_by_channel(self, channel):
        return next((x for x in self.channels if x.channel == int(channel)), None)

    def split_raw_rx(self, data):
        """Split a raw stream of bytes received into the various message stanzas it contains.
        Dealing with what each line means is begun in the `parse_raw_rx()` method.
        """
        return data.split("\n")

    def parse_raw_rx(self, data):
        """Deal with what each line means."""
        pass

    def get_channels(self):
        channels = []
        for channel in self.channels:
            channels.append(channel.channel)
        return channels

    def get_all(self):
        ret = []
        for channel in self.channels:
            ret = ret + channel.build_get_all_strings()
        return ret

    def get_query_strings(self):
        ret = []
        for channel in self.channels:
            ret = ret + channel.build_query_strings()
        return ret


    def enable_metering(self, interval):
        for channel in self.channels:
            msg = channel.monitoring_enable(interval)
            if msg:
                self.writeQueue.put(msg)

    def disable_metering(self):
        for channel in self.channels:
            msg = channel.monitoring_disable()
            if msg:
                self.writeQueue.put(msg)

    def net_json(self):
        ch_data = []
        for channel in self.channels:
            data = channel.ch_json()
            if self.rx_com_status == 'DISCONNECTED':
                data['status'] = 'RX_COM_ERROR'
            ch_data.append(data)
        data = {
            'ip': self.ip, 'type': self.type, 'status': self.rx_com_status,
            'raw': self.raw, 'tx': ch_data
        }
        return data
