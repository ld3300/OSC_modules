# This script was created with the help of AI.

"""
A wrapper for the OSCHandler module to provide high-level, 
ETC EOS-specific OSC functionality for use in future EOS-related 
projects.

EOS:
Numeric arguments with a decimal are treated as 32-bit floating point
Without a decimal are 32-bit integer
Non-numeric arguments are treated as strings
"""

# TODO: - refactor lower oschandler to make sure it can only be
#           initialized once per tx port
#       - consider adding the etc filter command
#       - method for etc subscribe command
#       - determine differences in the different console OSC address
#           formats

import logging
import threading
import time
from collections import deque
from osc.logging_config import setup_logging
from osc.oschandler import OSCHandler


# How often to send ping command to the console
PING_FREQUENCY = 1.0

# Logger
setup_logging()
logger = logging.getLogger(__name__)


class etcosc:
    """
    This class is specifically defined to provide OSC methods and data
    parsing for ETC Consoles
    """
    def __init__(self,
        mode='txrx',
        tx_udp_ip=None,
        tx_port=None,
        rx_udp_ip='0.0.0.0',
        rx_port=None,
        ping=True,
        ping_frequency=PING_FREQUENCY
    ):
        """
        When initialized, set following:
        mode, sets if transmitting 'tx', receiving 'rx', 'txrx'
        If TX enabled:
            transmit udp ip address for receiving device, can be a
            broadcast address transmit port, should be same as receive
            port on end device
        If RX enabled:
            receive port.
        Examples:
            myosc = etcosc(
                mode='txrx',
                tx_udp_ip='10.101.100.101',
                tx_port=8000,
                rx_port=8001
            )
            Can omit arguments not needed for chosen mode (rx or tx)
        rx_udp_ip is optional, the default will receive from any device
        network interface. Use if expressly need to control which
        interface is listening. This should rarely be needed.
        ping argument requires txrx, it will send ping command every 
        ping_frequency seconds and calculate latency. Shouldn't need to
        disable for most cases. Calling script can receive latency.
        """
        self.mode=mode
        self.tx_udp_ip=tx_udp_ip
        self.tx_port=tx_port
        self.rx_udp_ip=rx_udp_ip
        self.rx_port=rx_port
        self.console='eos' # can be changed with define_console method
        self.user=None # see change_user method
        self.base_address=f"/{self.console}"
        self.last_send_interval = -1.0
        self.ping_queue = deque(maxlen=10)
        self.ping_latency = 0
        # How often we should send a ping message
        self.ping_timer = ping_frequency
        self.ping_started = False

        self.osc_handler = OSCHandler(
            mode=self.mode,
            tx_udp_ip=self.tx_udp_ip,
            tx_port=self.tx_port,
            rx_udp_ip=self.rx_udp_ip,
            rx_port=self.rx_port
        )
        logger.info(
            f"OSCHandler sent with ,mode={self.mode}"
            f"tx_udp_ip={self.tx_udp_ip}"
            f"tx_port={self.tx_port}"
            f"rx_udp_ip={self.rx_udp_ip}"
            f"rx_port={self.rx_port}"
        )
        if self.mode == "txrx" and ping and self.ping_timer > 0:
            self._start_ping()

    # Send message directly to oschandler
    def osc_send_raw(self, address, *args, send_interval=0.0):
        """
        Send message straight to lower oschandler module.
        args don't apply to all messages
        """
        if send_interval != self.last_send_interval:
            self.osc_handler.set_tx_rate_limit(min_send_interval=send_interval,
                                               rate_limit_mode='buffer')
            self.last_send_interval = send_interval
        self.osc_handler.send_message(address, args)
        logger.info(f"sent {address} {args}")

    def define_console(self, console='eos'):
        """
        ## COMMANDS HAVE NOT YET BEEN ADAPTED TO COBALT AND CS FORMAT!
        Change the Console type which sets the OSC string start. 
        EOS line set ='eos' osc start '/eos/'
        Cobalt line, set ='cobalt' osc start '/cobalt/'
        ColorSource line, set ='colorsource' osc start '/cs/'
        """
        if(console.lower() not in ['eos', 'cobalt', 'colorsource', 'cs']):
            logger.error(f"{console} not valid. Must be eos, cobalt, "
                          f"colorsource")
        else:
            self.console = console.lower()
            if 'colorsource' in self.console:
                self.console = 'cs'
            _segments = self.base_address.strip('/').split('/')
            _segments[0] = self.console
            self.base_address = '/' + '/'.join(_segments)
            logger.info(f"New OSC address {self.base_address}...")

    def change_user(self, user=None, OSC_persist=False):
        """
        Set the user commands will be issued by. Options:
        None will remove /user/# from address string
        0 will set as background user for certain commands (ie. macros)
        Positive number will set user, make sure valid on console
        'reset' will set the on-console OSC user to same as console,
        clearing OSC_persist user
        OSC_persist will set the OSC command user at the console,
        instead of including it in address command. (The Console will
        be configured to accept all OSC commands not including
        /user/# as the OSC persist user.)
        """
        _user_int = -1
        _old_user = self.user
        self.user = str(user)
        _old_address = self.base_address
        self.base_address = f"/{self.console}"
        try:
            _user_int = int(self.user)
        except ValueError:
            if not self.user or self.user.lower() == 'none':
                logger.info(f"OSC address {self.base_address}...")
                return
            elif self.user.lower() == 'reset':
                self.user = '-1'
                OSC_persist = True
            else:
                # Bad user variable, restore previous settings:
                self.user = _old_user
                self.base_address = _old_address
                logger.error("invalid user value. Must be integer, None, or"
                    "'reset'"
                )
                return
        if OSC_persist:
                _address = self.base_address + '/user'
                self.osc_handler.send_message(_address, [self.user])
                logger.info(
                    f"Console sent configuration: "
                    f"OSC user = {self.user}"
                )
        elif _user_int >= 0:
            self.base_address = f"{self.base_address}/user/{self.user}"
        else:
            return
        logger.info(f"OSC address {self.base_address}...")

    # eos tx command line
    # There are 2 command line methods, one as a string, one with all commands
    # as part of the address /eos/cmd/chan/1/at...
    def eos_send_cmd(self, *args, send_interval=0.0):
        """
        To send a command line OSC address
        *args should be a list of strings comprising the command line
        prompt.
        example: ['chan','1','at','50','enter']
        """
        if send_interval != self.last_send_interval:
            self.osc_handler.set_tx_rate_limit(min_send_interval=send_interval,
                                               rate_limit_mode='buffer')
            self.last_send_interval = send_interval
        command_string = '/'.join(self.base_address,args)
        self.osc_handler.send_message(command_string, '')
        logger.info(f"sent: {command_string})")

    # eos out wheel
    def eos_send_wheel(self,
        wheel_type='param',
        param=None,
        index=None,
        ticks=0.0,
        fine=False,
        coarse_explicit=False,
        send_interval=0.05
    ):
        """
        Sends the OSC Wheel command.
        If wheel_type is 'param', param must be provided
        If wheel_type is 'index', an index positive integer must be
        provided.
        Coarse is default (unless set 'fine' to True). If not defined
        console assumes coarse unless /eos/wheel {mode} has been set to
        1.0(fine).
        'coarse' will not be in string unless coarse_explicit is set to
        True.
        If sending a wheel as an index, must include /active in address
        or it is actually sending OSC config to the console instead of
        controlling the associated parameter.
        Argument: float, up to 3 decimal places, positive value to
        increment, negative value to decrement
        Format reference:
        index: /eos/active/wheel/(coarse|fine/)<index> <(float)>
        param: /eos/wheel/(coarse|fine/)<param> <(float)>
        send_interval: sets number of seconds between packets,
            prevents console lag. set to 0 to disable.
        returns: /eos/out/active/wheel/2 "Red  [78]"(s), 3(i), 77.900(f) 
            "Red [78]" param name and rounded value
            3(int) = I believe this is param class - color is 3
            77.900(float), actual value in range
        Also returns hue and saturation:
            /eos/out/color/hs, 293.308(f), 49.211(f)
        """
        _ticks = 0.0
        try:
            _ticks = float(ticks)
        except ValueError:
            logger.error(f"ticks={ticks} must be a number")
            return
        _wheel_address = self.base_address
        _mode = ''
        if fine:
            _mode = '/fine'
        elif coarse_explicit:
            _mode = '/coarse'
        if wheel_type.lower() == 'param':
            if not param:
                logger.error("wheel_type='param' requires param='parameter'")
            else:
                _wheel_address = f"{_wheel_address}/wheel{_mode}/{param}"
        elif wheel_type.lower() == 'index':
            try:
                _index = int(index)
                _wheel_address = (
                    f"{_wheel_address}/active/wheel{_mode}/{_index}")
            except ValueError:
                logger.error(f"index={index} not a valid number")
                return
        else:
            logger.error(f"wheel_type={wheel_type} not recognized")
            return
        if send_interval != self.last_send_interval:
            self.osc_handler.set_tx_rate_limit(min_send_interval=send_interval,
                                               rate_limit_mode='drop')
            self.last_send_interval = send_interval
        self.osc_handler.send_message(_wheel_address, _ticks)

    def get_latency(self):
        """
        Will return a float of the latency in seconds being calculated
        via the /eos/ping command.
        """
        return self.ping_latency

    def _start_ping(self):
        """
        Will start the ping process in a thread
        """
        if not self.ping_started:
            self._ping_send_thread = threading.Thread(
                target=self._ping_send, daemon=True
            )
            self._ping_send_thread.start()
            self._ping_receive_thread = threading.Thread(
                target=self._ping_receive, daemon=True
            )
            self._ping_receive_thread.start()
            logger.info("ping started")
            self.ping_started = True

    def _ping_send(self):
        """
        Sends a ping as with time as an arg. Uses
        response to determine latency. Should return an error if no
        response.
        Timecode float must be sent as a string, EOS cannot handle 
        floats that large, and returns the wrong args
        """
        ping_base = f"/{self.console}"
        ping_address = f"{ping_base}/ping"
        while True:
            ping_time = str(time.time())
            self.ping_queue.append(ping_time)
            self.osc_handler.send_message(ping_address, ping_time)
            time.sleep(self.ping_timer)
            # Next will be receiving ping time


    def _ping_receive(self):
        """
        Handle ETC ping receive messages, Passes response to the
        _ping_handler
        """
        ping_base = f"/{self.console}"
        ping_address = f"{ping_base}/out/ping"
        self.osc_handler.register_osc_listener(ping_address,
                                               self._ping_handler)
        self.osc_handler.start_receiving()

    def _ping_handler(self, address, *args):
        """
        When console returns a ping (/eos/out/ping args) it gets passed
        here. Checks for lost pings and calculates the latency from
        the sent timestamp to the current time when console returns
        that same timestamp
        """
        try:
            ping_return = float(args[0])
        except Exception:
            logger.warning(f"Could not parse ping_return: {args[0]}")
            return
        # Search through queue for ping match
        matched = False
        while self.ping_queue:
            ping_sent = float(self.ping_queue.popleft())
            if ping_return == ping_sent:
                matched = True
                self.ping_latency = round(time.time() - ping_return, 6)
                logger.info(
                    f"Rx: {address} {ping_return} Latency:{self.ping_latency}"
                )
                break
            else:
                logger.info(f"Ping Lost: sent {ping_sent} return {ping_return}")
        # If no match in the ping queue
        if not matched:
            logger.warning(f"Returned ping {ping_return} had no match in queue")


#         Example C code filter and subscribe
#           // Add a filter so we don't get spammed with unwanted OSC
#  messages
# from Eos
#   OSCMessage filter("/eos/filter/add");
#   filter.add("/eos/out/param/*");
#   filter.add("/eos/out/ping");
#   SLIPSerial.beginPacket();
#   filter.send(SLIPSerial);
#   SLIPSerial.endPacket();

#   // subscribe to Eos pan & tilt updates
#   OSCMessage subPan("/eos/subscribe/param/pan");
#   subPan.add(SUBSCRIBE);
#   SLIPSerial.beginPacket();
#   subPan.send(SLIPSerial);
#   SLIPSerial.endPacket();

#   OSCMessage subTilt("/eos/subscribe/param/tilt");
#   subTilt.add(SUBSCRIBE);
#   SLIPSerial.beginPacket();
#   subTilt.send(SLIPSerial);
#   SLIPSerial.endPacket();

    # eos out switch, with option for timeout to set to 0 (so parameter
    #  doesn't move forever)

    # ability to set single or multiple parameter values. Structured as
    #  /eos/.../param with
    # lists or tuples providing parameters and values, parameters would
    #  be concat onto string
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