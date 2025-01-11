import enum
import socket


WIRELESS_QUERY_QUEUE_INTERVAL = 10 # seconds


class NetworkProtocol(enum.Enum):
    TCP = socket.IPPROTO_TCP
    UDP = socket.IPPROTO_UDP


def TVLookup(frequency):
    frequency = float(frequency)
    return int((frequency - 470) / 6 + 14)
