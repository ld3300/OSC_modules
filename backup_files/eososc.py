"""
This script was created with the help of AI.
"""

"""
A wrapper for the OSCHandler module to provide high-level, 
ETC EOS-specific OSC functionality for use in future EOS-related 
projects.

EOS:
Numeric arguments with a decimal are treated as 32-bit floating point
Without a decimal are 32-bit integer
Non-numeric arguments are treated as strings
"""

import logging
import time
import threading
from oschandler import OSCHandler

# Constants
LOG_FILE = 'EOSOSC.log'

# THIS WILL BE REMOVED WHEN HIGHER LEVEL SCRIPT IS CREATED, swith to 
# eoslogger = logging.getLogger(__name__)
# Setup logging to file with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class eosOSC:
    """
    This class is specifically defined to provide methods and data
    parsing for ETC Console commands
    """
    def __init__(self, mode='both',
                 tx_udp_ip=None,
                 tx_port=None,
                 rx_udp_ip='0.0.0.0',
                 rx_port=None
        ):
        """
        When initialized, set following:
        mode, sets if transmitting 'tx', receiving 'rx', or 'both'
        If TX enabled:
            transmit udp ip address for receiving device, can be a
            broadcast address transmit port, should be same as receive
            port on end device
        If RX enabled:
            receive port.
        Examples:
            myosc = OSCHandler(mode='both', tx_udp_ip='10.101.100.101',
                tx_port=8000, rx_port=8001)
            if mode is set to only tx or rx, then you can omit the
            other parameters.
        rx_udp_ip is optional, the default will receive from any device
        network interface. Use if expressly need to control which
        interface is listening. This should rarely be needed.
        """
        self.mode=mode
        self.tx_udp_ip=tx_udp_ip
        self.tx_port=tx_port
        self.rx_udp_ip=rx_udp_ip
        self.rx_port=rx_port
        self.console='eos' # can be changed with ETC_console method

        self.osc_handler = OSCHandler(
            mode=self.mode,
            tx_udp_ip=self.tx_udp_ip,
            tx_port=self.tx_port,
            rx_udp_ip=self.rx_udp_ip,
            rx_port=self.rx_port
        )

    # TO DO: determine which methods later implemented work with each console
    def ETC_Console(self, console='eos'):
        """
        Change the Console type which sets the OSC string start. 
        EOS line set ='eos' osc start '/eos/'
        Cobalt line, set ='cobalt' osc start '/cobalt/'
        ColorSource line, set ='colorsource' osc start '/cs/'
        """
        self.console=console

    # Send message directly to oschandler
    def osc_send_raw(self, address, *args):
        """
        Send message straight to lower oschandler module.
        args don't apply to all messages
        """
        self.osc_handler.send_message(address, args)

    # eos tx command line
    # There are 2 command line methods, one as a string, one with all commands as part of the address /eos/cmd/chan/1/at...

    # eos tx chan and value (percentage or decimal)

    # maybe have tx commands have option for as user, that way it could be set as a variable or const in higher level script:, which would insert /user/*

    # eos out wheel
    def eos_send_wheel(self, )

    # eos out switch, with option for timeout to set to 0 (so parameter doesn't move forever)

    # ability to set single or multiple parameter values. Structured as /eos/.../param with
    # lists or tuples providing parameters and values, parameters would be concat onto string
    # TEST THIS

    # Set up a thread to start receiving messages
    def osc_rx_listener(self, address, handler, mode='loose'):
        """
        MORE DESCRIPTION HERE DESCRIBE HANDLER?
        address is the full or partial OSC string to listen for
        mode: 'loose'(default) or 'strict'. determins if address is
        considered a partial of a full address
        Example:
            /eos/out when loose will return all messages containing
                /eos/out, like /eos/out/chan/active
            or /chan/active, will also return /eos/out/chan/active
        In strict mode the address must be the full path 
            i.e. /eos/out/chan/active
        In both strict and loose modes wildcards are supported
        for example /eos/out/user/*/cmd would return with any user id
        Wildcards:
            * matches any sequence of characters
            ? matches any single character
            [abc] matches any one character in brackets
            {foo, bar} matches either foo or bar
        """
        # call correct register osc method based on mode
        return #placeholder

    # IS THERE A WAY TO CHECK IF A USER EXISTS BEFORE SENDING AS THAT USER,
    # TEST A FALSE USER TO SEE WHAT EOS RETURNS

    # def eos_ping, must be txrx, send timestamp as arg to determine latency
    # eos will send the same arg back

    # parse string for /eos/out/cmd and /eos/out/user/*/cmd

    # get wheel names and classes? make it so user can select a certain wheel or wheel class, and values

    # parse current and pending cue return strings

    # eos out event state 0=blind 1=live


    # parse palette strings
    # using docs divide the return strings into components

    # parse color palette chan select string
    # try to determine what missing value is in the return string, maybe gel?
    # this is the large string when in palette edit and a chan is selected

    # get patch

    # FIGURE OUT WHICH TYPES OF TX MESSAGES HAVE A RETURN MESSAGE
    # THAT CAN BE USED TO VERIFY SEND
    # /eos/chan/1/at 75 does not seem to return, but I may have done the string wrong the first time
    # that command also doesn't set the channel as active, so that is probably why it didn't return values
    # MAY NEED TO PROVIDE ABILITY TO CHOOSE BETWEEN SENDING ACTIVE CHANNEL DATA AND BACKGROUND DATA

    # Later: Add some magic sheet functions