
import logging

from zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceListener,
    Zeroconf,
)

# ~ from discover import add_rx_to_dlist


class SennheiserSSCDiscovery:

    SERVICE_TYPE = "_ssc._udp.local."

    def __init__(self):
        self._zc = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info:
            return

        logging.warning("Discovered new device:")
        print(info)
        addresses = ["%s:%d" % (addr, int(info.port)) for addr in info.parsed_addresses()]
        print("  Addresses: %s" % ", ".join(addresses))
        print("  Weight: %d, priority: %d" % (info.weight, info.priority))
        print(f"  Server: {info.server}")
        if info.properties:
            print("  Properties are:")
            for key, value in info.properties.items():
                print(f"    {key}: {value}")
        else:
            print("  No properties")

        '''
        @todo:
        * Get Device model (should be in properties)
        * Derive channel counts
        '''

        # ~ add_rx_to_dlist(ip_v4, model, channels)

    def start(self) -> None:
        self._zc = Zeroconf(ip_version=IPVersion.V4Only)
        ServiceBrowser(self._zc, self.SERVICE_TYPE, self)

    def stop(self) -> None:
        self._zc.close()

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logging.warning(f"Device {name} disappeared")

    # update_service(self, zc: Zeroconf, type_: str, name: str)
    def update_service(self, *_) -> None:
        pass
