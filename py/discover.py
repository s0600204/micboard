import logging
import platform
import time


discovered = []


def add_rx_to_dlist(ip, rx_type, model, channels):
    rx = next((x for x in discovered if x['ip'] == ip), None)

    if rx:
        rx['timestamp'] = time.time()

    else:
        discovered.append({
            'ip' : ip,
            'type': rx_type,
            'model': model,
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


class DeviceDiscovery:

    IGNORED_ADDRS = ['127.0.0.1']


    def handle_binding_error(self, error, adapter, address):
        if error.errno == 10049 and address.ip.startswith("169.254."):
            # Windows (10) assigns a link-local address to unconnected adapters,
            # despite them being, y'know, *not connected* to anything.
            message = "Skipping unbindable address %s on unconnected interface %s"

        else:
            message = f"[{error.errno}] {error.strerror} (%s on %s)"

        self.register_ignored_address(adapter, address, message)

    def is_ignored_address(self, address):
        return address in self.IGNORED_ADDRS

    def register_ignored_address(self, adapter, address, message):
        if address.ip in self.IGNORED_ADDRS:
            return
        self.IGNORED_ADDRS.append(address.ip)

        if platform.system() == "Windows":
            interface = f"'{adapter.nice_name}' (aka '{address.nice_name}')"
        else:
            interface = f"'{adapter.nice_name}'"
        logging.debug(message, address.ip, interface)
