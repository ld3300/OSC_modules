# test scripts to/from ETC EOS
"""
COPY this section to files in test folder, to reference parent folder
files
use command:
pytest test_files\test_oschandler_eos.py
In this file, or anytime need to use input() command add -s
pytest -s test_files\test_oschandler_eos.py
"""

import logging
from osc.logging_config import setup_logging
from osc.oschandler import OSCHandler

# Constants, change for your test environment
RX_PORT = 8001
TX_PORT = 8000
TX_IP = '127.0.0.1'
OSC_RX_STRING = '/eos/cmd/Chan/1/At/%1#'
OSC_RX_SUBSTRING = '/user/1'
OSC_TX_STRING = '/eos/cmd/gobo_select/next'
OSC_TX_ARGS = ['next']

# Setup logging to file with UTF-8 encoding
setup_logging()
logger = logging.getLogger(__name__)

osc_manager = OSCHandler(mode='txrx', tx_udp_ip=TX_IP, tx_port=TX_PORT, rx_port=RX_PORT)

def my_handler(address, *args):
    print("Received:", address, args)
    logger.info("received OSC message: %s %s", address, args)

osc_manager.register_osc_listener(OSC_RX_STRING, my_handler)
osc_manager.register_osc_substring(OSC_RX_SUBSTRING, my_handler)

osc_manager.start_receiving()

logger.info("receiver started")

while True:
    user_input = input("number plus enter for send, q for quit: \n")
    if user_input == 'q':
        break
    elif user_input == 'm':
        print("sending OSC message")
        osc_manager.send_message(OSC_TX_STRING, OSC_TX_ARGS)
    else:
        my_args = [float(user_input)]
        print("sending OSC message")
        osc_manager.send_message(OSC_TX_STRING, my_args)