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
from etcosc import etcosc
from joystick_osc import JoystickOSC

# Constants, change for your test environment
LOG_FILE = 'test_oschandler.log'
RX_PORT = 8001
TX_PORT = 8000
TX_IP = '127.0.0.1'

# Setup logging to file with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

osc_manager = etcosc(
    mode='tx',
    tx_udp_ip=TX_IP,
    tx_port=TX_PORT,
    rx_port=RX_PORT
)

joystick = JoystickOSC(osc=osc_manager)

def my_handler(address, *args):
    print("Received:", address, args)
    logging.info("received OSC message: %s %s", address, args)


# osc_manager.start_receiving()
# logging.info("receiver started")
testmode = 'txrx'
if testmode in 'txrx':
    print('txrx passed')

while True:
    # user_input = input(" q + enter for quit: \n")
    # if user_input == 'q':
    #     break
    joystick.poll()
    time.sleep(0.1)