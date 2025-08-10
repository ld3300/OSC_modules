"""
This script was created with the help of AI.
"""

""" OSC Handler for sending and receiving messages."""

"""
To Do:
- Change to async from threading
- REFACTOR handle singleton patterns, basically make it so that if the
    module has already been initialized, running another high level
    module doesn't reinitialize it.
- Consider making sending device IP available in receive methods
"""

# may need to do the following:
# pip install python-osc

import logging
import time
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import BlockingOSCUDPServer
from collections import deque

# Constants
"""
Declutter: If set true, when osc message is received, any messages
within declutter time will count num messages. Log will print the first
message and show a count of total
"""
OSC_RECEIVE_DECLUTTER_TIME = 0.5
OSC_RECEIVE_DECLUTTER = True

# Logger
logger = logging.getLogger(__name__)

class OSCHandler:
    """
    Handles sending and receiving OSC messages. Can be configured for
    send only, receive only or both. Provide appropriate port numbers.
    When sending osc needs the IP address, a global broadcast address,
    or a subnet broadcast address.
    """

    def __init__(self,
        mode='txrx',
        tx_udp_ip=None,
        tx_port=None,
        rx_udp_ip='0.0.0.0',
        rx_port=None
        ):
        """
        When initialized, set following:
        mode, sets if transmitting 'tx', receiving 'rx', or both 'txrx'
        If TX enabled:
            transmit udp ip address for receiving device, can be a
            broadcast address transmit port, should be same as receive
            port on end device
        If RX enabled:
            receive port.
        Examples:
            myosc = OSCHandler(mode='txrx', tx_udp_ip='10.101.100.101',
            tx_port=8000, rx_port=8001)
        If mode is set to only tx or rx, then you can omit the other
        parameters.
        rx_udp_ip is optional, the default will receive from any device
        network interface. Use if expressly need to control which
        interface is listening. This should rarely be needed.
        """
        self.mode = mode
        self.tx_udp_ip = tx_udp_ip
        self.tx_port = tx_port
        self.rx_udp_ip = rx_udp_ip
        self.rx_port = rx_port
        self.min_send_interval = 0.00
        self.rate_limit_mode = 'buffer'
        self.message_queue = deque(maxlen=50)
        self.last_send_time = 0
        self._osc_address = None
        self._osc_args = None
        # OSC Message Batch Logging vars, see declutter constants:
        self.batch = None
        self.batch_timer = None
        self.tx_buffer_timer = None
        # Get this thing started:
        logger.info(
            f"OSChandler initialized with mode='{self.mode}' "
            f"tx_udp_ip='{self.tx_udp_ip}' tx_port={self.tx_port} "
            f"rx_port={self.rx_port}"
        )
        # This segment checks that the necessary parameters are set and
        # will send an error message about what needs fixing
        if(self.mode not in ['tx', 'rx', 'txrx']):
            raise ValueError("mode must be: 'tx', 'rx', or 'txrx'")
        else:
            self.error_list = []
            if 'tx' in self.mode:
                if self.tx_udp_ip is None or self.tx_port is None:
                    self.error_list.append("tx_udp_ip='x.x.x.x' and "
                        "tx_port=#### must be set for transmitting"
                    )
            if 'rx' in self.mode:
                if self.rx_port is None:
                    self.error_list.append("rx_port=#### must be set for "
                        "receiving"
                    )
        if self.error_list:
            error_string = ""
            for error in self.error_list:
                error_string += f"{error}\n"
            logger.error(error_string.strip())
            raise ValueError(error_string)

        # Initialize UDP client for sending OSC messages if mode is set
        # to transmit or txrx
        if 'tx' in self.mode:
            self.udp_client = SimpleUDPClient(self.tx_udp_ip, self.tx_port)

        # Initialize Dispatcher to handle OSC inputs OSC UDP client and
        # server as necessary
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.default_handler)

    # set up or change the rate limit handling in case the receiving
    # device cannot keep up with data stream
    def set_tx_rate_limit(self,
        min_send_interval=0.00,
        rate_limit_mode='buffer',
        buffer_max_size=50
        ):
        """
        The min_send_interval sets the required time between tx
            messages.  This may be necessary if working with interfaces
            that output complicated messages, or messages faster than
            the receiving device can process them.
        min_send_interval # default is 0.00. Seconds, set this if issues
            sending messages faster than receiver can handle. 0.00 is
            the same as disabled.
        rate_limit_mode # 'buffer' or 'drop' default is 'buffer'. When
            rate is limited do you want to buffer messages, or drop any
            messages that are sent faster than min_send_interval.
        buffer_max_size # default is 50. When buffer is used, how many
            messages to store. If the buffer gets full the oldest
            messages will be dropped to make room for new messages.
        """
        self.min_send_interval = min_send_interval
        self.rate_limit_mode = rate_limit_mode
        if(min_send_interval == 0.00):
            self.message_queue.clear()
        else:
            self.message_queue = deque(maxlen=buffer_max_size)

    # Send OSC Message
    def send_message(self, osc_address, osc_args=None):
        """
        Send an osc command, arguments should be a list
            (surrounded by []),
            Strings need to be surrounded by '' inside the list.
            example myosc.send_message('/eos/chan/1/at', [50])
                    myosc.send_message('/eos/param/red/green', [50, 60])
                    myosc.send_message('/eos/cmd', 
                        ['Chan 1 At 50 Enter']) # string example
                should contain the correct number of arguments in
                    correct types
        """
        if 'tx' not in self.mode:
            logger.error("OSCHandler is not set to transmit, cannot "
                "send message."
            )
        else:
            # the following converts inputs to a list, to be a little
            # more flexible and robust
            self._osc_address = osc_address
            if osc_args is None:
                self._osc_args = []
            elif isinstance(osc_args, (list, tuple)):
                self._osc_args = list(osc_args)
            else:
                self._osc_args = [osc_args]
            # if rate limiting is set we will manage queue and wait time
            if self.min_send_interval > 0:
                if(self.rate_limit_mode == 'buffer'):
                    self.message_queue.append([osc_address, osc_args])
                current_time = time.time()
                if current_time - self.last_send_time < self.min_send_interval:
                    if (not self.tx_buffer_timer and 
                        self.rate_limit_mode == 'buffer'
                    ):
                        self._start_tx_timer()
                    self._osc_address = None
                    return
                else:
                    self.last_send_time = current_time
            self._send_message()

    # This message wil be called from either send message, or when the
    # rate limiter times out
    def _send_message(self):
        if (self.min_send_interval > 0 and self.rate_limit_mode == 'buffer' and
            len(self.message_queue) > 0
        ):
            # take oldest message from queue and prep to send
            next_message = self.message_queue.popleft()
            self._osc_address = next_message[0]
            self._osc_args = next_message[1]
            if len(self.message_queue) > 0:
                if self.tx_buffer_timer:
                    self.tx_buffer_timer.cancel()
                self._start_tx_timer()
            else:
                if self.tx_buffer_timer:
                    self.tx_buffer_timer.cancel()
                self.tx_buffer_timer = None
        # Check _osc_address again, as it might have been cleared by a
        # rate-limit return
        if self._osc_address is not None:
            self.udp_client.send_message(self._osc_address, self._osc_args)
            logger.info(
                f"Sent OSC message '{self._osc_address}', '{self._osc_args}' "
                f"to {self.tx_udp_ip}:{self.tx_port}"
            )
            self._osc_address = None

    # starts the timer for managing min_send_interval if set
    def _start_tx_timer(self):
        if not self.tx_buffer_timer:
            self.tx_buffer_timer = threading.Timer(
                self.min_send_interval,
                self._send_message
            )
            self.tx_buffer_timer.start()

    # Start the server
    def _run_server(self):
        self.osc_receiver.serve_forever()

    def _rx_batch(self, address, *args, enable=OSC_RECEIVE_DECLUTTER):
        """
        Collects OSC messages for batch logging and sets timer
        Items sent to log individually if disabled, or with batch when
        timer expires. usage within this module:
        self._rx_batch(address, *args)
        """
        # If batch is Empty, load with first message, and count 1
        if self.batch is None:
            self.batch = [address, args, 1]
        else:
            self.batch[2] += 1 # We've already logged the first message,
                               # so we will just increment the counter
        # If timer isn't enabled we will send the message to be logged
        if not enable:
            self._OSC_rx_batch_logging()
            return
        if not self.batch_timer:
            self.batch_timer = threading.Timer(
                OSC_RECEIVE_DECLUTTER_TIME,
                self._OSC_rx_batch_logging
            )
            self.batch_timer.start()

    def _OSC_rx_batch_logging(self):
        """
        This method is intended to prevent filling the log file when
        large number of OSC messages are received in a short period of
        time. It will give a count of messages, and print the first
        message and arguments.
        """        
        if self.batch:
            logger.info(
                f"Handler received {self.batch[2]} messages. "
                f"First Msg: '{self.batch[0]}' args: {self.batch[1]}."
            )
        self.batch = None
        if self.batch_timer:
            self.batch_timer.cancel()

    # default when no OSC handler for a message
    def default_handler(self, address, *args):
        """
        Default handler for OSC messages, can be overridden by
        registering a specific handler
        Starts with check for substring listeners, if any registered
        """
        # Add received messages to log
        self._rx_batch(address, *args)
        # Check if any registered substring listeners match the address
        if hasattr(self, 'substring_listeners'):
            for substring, handler in self.substring_listeners:
                if substring in address:
                    handler(address, *args)

    def register_osc_listener(self, address, handler):
        """
        Handle incoming OSC messages
        Requires specific OSC Address (can use wildcards), and a handler
            tp receive message
        To include all address sub-paths, use register_osc_substring
        example:
        def my_handler(address, *args):
            print("Received:", address, args)
        osc = OSCHandler(mode='rx', rx_port=8000) # 'txrx' also valid
        osc.register_osc_listener('/eos/out/chan/*', my_handler)
        osc.start_receiving()
        Wildcards:
        * matches any sequence of characters
        ? matches any single character
        [abc] matches any one character in brackets
        {foo, bar} matches either foo or bar
        """
        # Add received messages to log
        # self._rx_batch(address, *args)
        # Send to user message handler
        self.dispatcher.map(address, handler)
        logger.info(
            f"Registered rx address '{address}' with handler "
            f"'{handler.__name__}'"
        )

    def register_osc_substring(self, substring, handler):
        """
        register OSC listener for all OSC paths that contrain address
        '/eos/out' will include all sub-paths like '/eos/out/wheel/1'
        example is same as above except function name:
        osc.register_osc_substring('/eos/out', my_handler)
        Wildcards:
        * matches any sequence of characters
        ? matches any single character
        [abc] matches any one character in brackets
        {foo, bar} matches either foo or bar
        """
        # Creates a list to store tuples of declarations and handlers.
        # Is used in default handler to check any starts with
        if not hasattr(self, 'substring_listeners'):
            self.substring_listeners = []
        self.substring_listeners.append((substring, handler))
        logger.info(
            f"Registered rx address substring '{substring}' with handler "
            f"'{handler.__name__}'"
        )

    def start_receiving(self):
        """
        Start server to receive OSC messages if mode set to rx or txrx.
        """
        if 'rx' not in self.mode:
            logger.error(
                "OSCHandler is not set to receive, cannot start server."
            )
            return
        # Create the server if it doesn't exist yet
        if not hasattr(self, 'osc_receiver'):
            self.osc_receiver = BlockingOSCUDPServer(
                (self.rx_udp_ip,
                 self.rx_port),
                 self.dispatcher
            )
        # Start the server in a background thread to be non-blocking
        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self._server_thread.start()
        logger.info("OSC server started in background thread.")
