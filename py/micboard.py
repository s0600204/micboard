import logging
import threading
import time


import config
import tornado_server
import device_manager
from sennheiser import discover as sennheiser_discover
from shure import discover as shure_discover


def main():
    version = config.config()
    config.logging_init()
    logging.info(f'Starting Micboard {version}')

    time.sleep(.1)
    rxquery_t = threading.Thread(target=device_manager.WirelessQueryQueue)
    rxcom_t = threading.Thread(target=device_manager.SocketService)
    web_t = threading.Thread(target=tornado_server.twisted)
    discover_sennheiser_t = threading.Thread(target=sennheiser_discover.discover)
    discover_shure_t = threading.Thread(target=shure_discover.discover)
    rxparse_t = threading.Thread(target=device_manager.ProcessRXMessageQueue)

    rxquery_t.start()
    rxcom_t.start()
    web_t.start()
    discover_sennheiser_t.start()
    discover_shure_t.start()
    rxparse_t.start()


if __name__ == '__main__':
    main()
