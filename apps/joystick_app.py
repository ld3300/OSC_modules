### Created with the help of AI ###

"""
Will Run the joystick app for ETC OSC.  Currently configured for
Logitech Extreme 3d. Configuration and tuning variables can be changed
by editing joystick_osc.py in the User Defined Global Variables section
"""

import time
import logging
from osc.etcosc import etcosc
from apps.joystick_osc import JoystickOSC
from osc.logging_config import setup_logging

# Constants, change for your test environment
LOG_FILE = 'test_oschandler.log'
RX_PORT = 8001
TX_PORT = 8000
TX_IP = '127.0.0.1'

# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

osc_manager = etcosc(
    mode='tx',
    tx_udp_ip=TX_IP,
    tx_port=TX_PORT,
    rx_port=RX_PORT
)

joystick = JoystickOSC(osc=osc_manager)

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
    joystick.poll()
    time.sleep(0.05)