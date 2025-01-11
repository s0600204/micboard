import socket
import threading


class SharedUDPSocket:
    '''
    Upon receiving a command from a given IP Address and Port number, Sennheiser devices (at
    least those using MCP over UDP) will send replies to the given IP Address, but not to the
    given Port number, preferring instead to send it to a specific hardcoded Port.

    It is thus necessary for there to be a way for multiple device representations (our
    `NetworkDevice` class, and those that inherit from it) to all listen on the same local port
    number for the responses from their respective real-world hardware.

    On *nix systems this is possible via use of the `SO_REUSEPORT` socket option; however this
    option does not exist on all systems (e.g. Windows), and attempting to use the similar
    `SO_REUSEADDR` socket option instead doesn't work (responses from one of the devices is
    received reliably, but responses for the rest are lost).

    Hence this ugly bit of code, which permits sharing of a single local socket.
    '''

    __SHARED_SOCKETS = {}

    def __init__(self, port):
        self.client_list = {}
        self.lock = threading.Lock()
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.settimeout(0.2)

    def add_client(self, client):
        if self.has_client(client):
            return
        self.client_list[client.ip] = client

    def close(self):
        with self.lock:
            if self.socket and len(self.client_list) == 0:
                self.socket.close()
                self.socket = None
                del SharedUDPSocket.__SHARED_SOCKETS[self.port]

    def fileno(self):
        if self.socket:
            return self.socket.fileno()
        return -1

    def has_client(self, client):
        return client.ip in self.client_list and self.client_list[client.ip] is client

    def recvfrom(self, buffer_length, flags=0):
        '''
        Like `<socket>.recvfrom()`, but returns the relevant `NetworkDevice` instance instead of an address tuple.
        '''
        data, (ip4_addr, port) = self.socket.recvfrom(buffer_length, flags)
        if ip4_addr not in self.client_list or port != self.port:
            return b'', None
        return data, self.client_list[ip4_addr]

    def remove_client(self, client):
        if not self.has_client(client):
            return
        del self.client_list[client.ip]

    def sendto(self, message, address):
        self.socket.sendto(message, (address[0], self.port))

    @staticmethod
    def socket(port):
        if port not in SharedUDPSocket.__SHARED_SOCKETS:
            SharedUDPSocket.__SHARED_SOCKETS[port] = SharedUDPSocket(port)
        return SharedUDPSocket.__SHARED_SOCKETS[port]
