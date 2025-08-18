"""
This script was created with the help of AI.
"""

import logging
import pygame
# from etcosc import etcosc

# start with init before being able to assign a joystick instance to
# read

logger = logging.getLogger(__name__)


### User defined global variables ######################################
# Logitech Extreme 3d - Axes x 4 - range -1.0 to 1.0
# 12 x buttons
# 1 x hat

# Button usage:
# function, button changes script behavior
#   ('function', 'name', '')
# OSC command, osc_string will be appended to /eos(/user/#), with tuple
#   of arguments
#   ('osc', 'osc_string', (args))
# Unused: ('none', '', '')
BUTTON_OPERATION = (
    ('function', 'fine_mode', ''),  # button 0, trigger
    ('function', 'hue_sat', ''),    # button 1 thumb
    ('osc', '/gobo/wheel/1/steporsomething' ('')), # button 2
    ('osc', '/gobo/wheel/1/steporsomething' ('')), # button 3
    ('osc', '/gobo/wheel/1/steporsomething' ('')), # button 4
    ('osc', '/gobo/wheel/1/steporsomething' ('')), # button 5
    ('none', '', ''), # button 6
    ('none', '', ''), # button 7
    ('none', '', ''), # button 8
    ('none', '', ''), # button 9
    ('none', '', ''), # button 10
    ('none', '', '')  # button 11
)

# Hat operations, probably edge, diffusion

# Logitech Extreme 3d - Axes range -1.0 to 1.0
# Deadzone is the minimum amount stick must move to register as valid
# Ticks is the tick value sent to the ETC console, range 0.000 to *#.###
# The OSC tick value will be mapped from axis input of deadzone to +-1.0
# to the range +-0.000 to Ticks max value
# These will apply to x, y, z axes and modes unless defined explicitly
# below:
DEADZONE_DEFAULT = 0.3
TICKS_COARSE_MAX_DEFAULT = 4.0
TICKS_FINE_MAX_DEFAULT = 4.0

# If an axis needs different values, or control parameters need to be 
# separated, make the change here. Parameter names must match the string
# for the OSC wheel command. Use 'none' to disable Parameters.

# Amount stick must move from center to be considered valid
# not applying to slider due to physical functionality
AXIS_DEADZONE = (
    DEADZONE_DEFAULT,
    DEADZONE_DEFAULT,
    DEADZONE_DEFAULT,
    0.0
)
# Parameters to use based on state, default is first, second is other
AXIS_PARAMETERS = (
    ('pan','hue'),                  # X axis
    ('tilt','saturation'),          # Y axis
    ('zoom','color_temperature'),   # Z axis
    ('none','none')                 # Slider
)
# Max tick counts for each axis, if need tuning from default
TICKS_MAX_COARSE = (
    TICKS_COARSE_MAX_DEFAULT,       # X axis
    TICKS_COARSE_MAX_DEFAULT,       # Y axis
    TICKS_COARSE_MAX_DEFAULT,       # Z axis
    TICKS_COARSE_MAX_DEFAULT        # Slider
)
TICKS_MAX_FINE = (
    TICKS_FINE_MAX_DEFAULT,         # X axis
    TICKS_FINE_MAX_DEFAULT,         # Y axis
    TICKS_FINE_MAX_DEFAULT,         # Z axis
    TICKS_FINE_MAX_DEFAULT          # Slider
)

# Axis Locks - set if axis values are ignored until axis returned to
# zero for following scenarios. Not currently locking state from coarse
# to fine, assuming that it is part of same motion.
PARAM1_TO_PARAM2_LOCK = True
PARAM2_TO_PARAM1_LOCK = True
COARSE_TO_FINE_LOCK = False
FINE_TO_COARSE_LOCK = True

### End User Defined Globals ###########################################


# Reference: partial events list:
# QUIT              none
# JOYAXISMOTION     instance_id, axis, value
# JOYBALLMOTION     instance_id, ball, rel
# JOYHATMOTION      instance_id, hat, value
# JOYBUTTONUP       instance_id, button
# JOYBUTTONDOWN     instance_id, button
# USEREVENT         code

QUIT = pygame.QUIT
AXIS = pygame.JOYAXISMOTION
BALL = pygame.JOYBALLMOTION
HAT = pygame.JOYHATMOTION
BUTTONDOWN = pygame.JOYBUTTONDOWN
BUTTONUP = pygame.JOYBUTTONUP
USER = pygame.USEREVENT

# Items for pygame event filter:
JOYSTICK_EVENTS = (QUIT, AXIS, BALL, HAT, BUTTONDOWN, BUTTONUP, USER)
# State for joystick when locked, not currently tracking the slider axis
JOYSTICK_LOCK_STATE = (True, True, True, False)

class JoystickOSC:
    """
    Handles joystick pygame calls and modes:
    """
    def __init__(self, joystick_index=0):
        """
        itinalize variables for controller. May add functions later
        to change these values programatically
        arguments:
            joystick_index, assumes only 1 connected, but could change
            the index value on init
        """
        # setup initial class input type state holders
        self.axes = None
        self.button_state = [False]
        self.hats = None
        # Will use a button to change between Coarse/Fine
        self.wheel_fine = False
        # Will use a button to change axes from param 1 to param 2
        self.wheel_param2 = False
        # Used to make sure all axes are returned to zero when mode change
        self.joystick_lock = [False,False,False,False]

        pygame.init()
        stick = pygame.joystick
        stick.init()
        self.event = pygame.event
        # Sets which event types the pygame library is allowed to place
        # in the events list
        self.event.set_allowed(JOYSTICK_EVENTS)

            # Get a list of connected Joysticks
        joysticks = [stick.Joystick(x) for x in range (stick.get_count())]

        if not joysticks:
            logger.error("No joysticks found")
        else:
            joystick = stick.Joystick(joystick_index) # Logitech Extreme 3D
            if not joystick.get_init():
                joystick.init()
            j_id = joystick.get_guid() # 0300eb976d04000015c2000000000000
            # get what the joystick has
            axes = joystick.get_numaxes() # 4
            buttons = joystick.get_numbuttons() # 12
            hats = joystick.get_numhats() # 1
            balls = joystick.get_numballs() # 0
            power = joystick.get_power_level() # NA

            self.axes = [0.0] * axes
            self.button_state = [False] * buttons
            self.hats =  [(0, 0)] * hats

            logger.info(
                f"joystick: {joystick.get_name()} "
                f"ID:{j_id}\n"
                f"axes:{axes} - "
                f"buttons:{buttons} - "
                f"hats:{hats} - "
                f"trackballs:{balls} - "
                f"power:{power} "
            )
            # checking that it inialized properly
            logger.info(f"pygame.init() = {pygame.get_init()}\n"
                f"pygame.joystick.init() = {stick.get_init()}")

    # Sample single event list item, for reference:
    # <Event(1536-JoyAxisMotion {'joy': 0, 'instance_id': 0,
    #  'axis': 0, 'value': 0.2882473220007935})>
    def readEvents(self, events):
        """
        When pygame has events, send them here
        """
        for event in events:
            if event:
                if event.instance_id == 0:
                    if event.type == AXIS:
                        self.handleAxes(event.axis, event.value)
                    elif event.type == BUTTONDOWN:
                        self.handleButton(event.button, True)
                    elif event.type == BUTTONUP:
                        self.handleButton(event.button, False)
                    elif event.type == HAT:
                        self.handleHat(event.hat, event.value)
                    else:
                        return

    # For mapping axes range to the Coarse/Fine ranges
    def _remap(self, value, from_min, from_max, to_min, to_max):
        """
        Simple remapping to intended output range:
        
        Args:
            value (flot)
            minimum input value (floate)
            maximum input value (float).  Usually 1.0
            to_min (float), minimum output value (usually 0)
            to_max (float), maximum value we ant to send to OSC
        """
        # Map value from [from_min, from_max] to [to_min, to_max]
        return (to_min + (float(value - from_min) / 
                        (from_max - from_min)) * (to_max - to_min))

    def handleAxes(self, axis, value):
        """
        Gets called when an axis event is read from pygame.
        maps the axis value to range we want.
        If any axes have not been homed since last lock, nothing will be
        sent.
        """
        # if any items in lock are true, unlocked becomes false
        unlocked = not any(self.joystick_lock)
        # We will use the deadzone value as our map minimum
        dead = AXIS_DEADZONE[axis]
        # Set map maximum to coarse, the if statement checks for fine
        map_max = TICKS_MAX_COARSE[axis]
        if self.wheel_fine:
            map_max = TICKS_MAX_FINE[axis]
        # Check if our value is above or below the deadzone
        if value > dead and unlocked:
            mapped = self._remap(value, dead, 1.0, 0.0, map_max)
        elif value < -dead and unlocked:
            mapped = self._remap(value, -dead, -1.0, 0.0, -map_max)
        else:
            mapped = 0
            self.joystick_lock[axis] = False  # if axis is zero unlock
        # Only send our output if there are no axis locks
        if unlocked:
            self.sendAxis(axis, mapped)

    def sendAxis(self,
                axis,
                ticks,
                coarse_fine='coarse',
                axis_mode='PTZ',
                lock_state = False):
        """
        Send Axis values to defined ETC OSC Wheel parameter.
        
        """
        return

    # When event handler receives a button press, send it here
    def handleButton(self, button, state):
        """
        Receives button presses and changes a state or sends an OSC
        command
        args: button index (0-11)
            state bool
        """
        op_mode = BUTTON_OPERATION[button][0]
        if op_mode == 'function':
            button_function = BUTTON_OPERATION[button][1]
            # If Coarse/Fine mode button
            if button_function == 'fine_mode':
                # Coarse/fine mode, True is fine
                self.wheel_fine = state
                logging.info(f"Coarse/Fine mode set to {state}")
                # Check if we are locking controls when going from
                # Coarse to fine
                if(
                    (state and COARSE_TO_FINE_LOCK) or
                    ((not state) and FINE_TO_COARSE_LOCK)
                ):
                    self.joystick_lock = list(JOYSTICK_LOCK_STATE)
                    logging.info("Joystick Locked, home axes")
            # if button for ptz/hs is pressed
            elif button_function == 'hue_sat':
                # set mode param2 (hue/sat) is true
                self.wheel_param2 == state
                # check if we lock the controls between param states
                if(
                    (state and PARAM1_TO_PARAM2_LOCK) or
                    ((not state) and PARAM2_TO_PARAM1_LOCK)
                ):
                    self.joystick_lock = list(JOYSTICK_LOCK_STATE)
                    logging.info("Joystick Locked, home axes")
        # Buttons intended to fire specific osc commands
        elif op_mode == 'osc':
            # Generate string and send osc
            return #temporary filler
        else:
            logging.error(f"button function: {op_mode} not valid")
            return

    # def handleHat(_hat, _value):


# Old execution code, before built class, need new test method now
        # while True:
        #     user_input = input(" q + enter for quit: \n")
        #     if user_input == 'q':
        #         break
        #     events = self.event.get(pump=True)
        #     self.readEvents(events)

