import logging
import threading
import time


import config
import tornado_server
import device_manager
from sennheiser.discover_mcp import SennheiserMCPDiscovery
from sennheiser.discover_ssc import SennheiserSSCDiscovery
from shure.discover import ShureDiscovery


def main():
    version = config.config()
    config.logging_init()
    logging.info(f'Starting Micboard {version}')

    time.sleep(.1)
    rxquery_t = threading.Thread(target=device_manager.WirelessQueryQueue)
    rxcom_t = threading.Thread(target=device_manager.SocketService)
    web_t = threading.Thread(target=tornado_server.twisted)
    rxparse_t = threading.Thread(target=device_manager.ProcessRXMessageQueue)

    sennheiser_mcp_discovery = SennheiserMCPDiscovery()
    sennheiser_ssc_discovery = SennheiserSSCDiscovery()
    shure_discovery = ShureDiscovery()

    rxquery_t.start()
    rxcom_t.start()
    web_t.start()
    sennheiser_mcp_discovery.start()
    sennheiser_ssc_discovery.start()
    shure_discovery.start()
    rxparse_t.start()


if __name__ == '__main__':
    main()
