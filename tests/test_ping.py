### Created with the help of AI ###

# test for joystick
"""
COPY this section to files in test folder, to reference parent folder
files
use command:
pytest test_files\test_etcosc.py
In this file, or anytime need to use input() command add -s
pytest -s test_files\test_etcosc.py
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
##################################################################################

import logging
from osc.etcosc import etcosc
from osc.logging_config import setup_logging

# Constants, change for your test environment
RX_PORT = 8001
TX_PORT = 8000
TX_IP = '127.0.0.1'

# Setup logging to file
setup_logging()
logger = logging.getLogger(__name__)

osc_manager = etcosc(
    mode='txrx',
    tx_udp_ip=TX_IP,
    tx_port=TX_PORT,
    rx_port=RX_PORT
)


def my_handler(address, *args):
    print("Received:", address, args)
    logger.info("received OSC message: %s %s", address, args)


# osc_manager.start_receiving()
# logger.info("receiver started")
testmode = 'txrx'
if testmode in 'txrx':
    print('txrx passed')

while True:
    # user_input = input(" q + enter for quit: \n")
    # if user_input == 'q':
    #     break
    time.sleep(0.5)