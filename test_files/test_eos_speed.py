# test scripts to/from ETC EOS
import logging
import time
from oschandler import OSCHandler

# Constants, change for your test environment
LOG_FILE = 'test_oschandler.log'
RX_PORT = 8001
TX_PORT = 8000
TX_IP = '127.0.0.1'
OSC_RX_STRING = '/eos/out/cmd'
OSC_RX_SUBSTRING = '/user/1'
OSC_TX_STRING = '/eos/chan/1/at/'
OSC_TX_ARGS = [75]
# Setup logging to file with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

osc_manager = OSCHandler(mode='txrx', tx_udp_ip=TX_IP, tx_port=TX_PORT, rx_port=RX_PORT)

# def my_handler(address, *args):
#     print("Received:", address, args)
#     logging.info("received OSC message: %s %s", address, args)

# osc_manager.register_osc_listener(OSC_RX_STRING, my_handler)
# osc_manager.register_osc_substring(OSC_RX_SUBSTRING, my_handler)

# osc_manager.start_receiving()

# logging.info("receiver started")

while True:
    for i in range(0, 101):
        my_args = [i]
        osc_manager.send_message(OSC_TX_STRING, my_args)
        # time.sleep(0.01)