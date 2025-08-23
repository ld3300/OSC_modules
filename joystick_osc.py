"""
This script was created with the help of AI.
"""

#### TODO: NEXT Have code reviewed, then have sendAxis output to EOS
####        FIX remap to constrain to the min and max values

import logging
import pygame
# from collections import namedtuple

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
    ('osc', '/gobo_select/next', ('')), # button 2
    ('osc', '/gobo/wheel/1/steporsomething', ('')), # button 3
    ('osc', '/gobo/wheel/1/steporsomething', ('')), # button 4
    ('osc', '/gobo/wheel/1/steporsomething', ('')), # button 5
    ('none', '', ''), # button 6
    ('none', '', ''), # button 7
    ('none', '', ''), # button 8
    ('none', '', ''), # button 9
    ('none', '', ''), # button 10
    ('none', '', '')  # button 11
)
# /eos/cmd/gobo_select/next, gobo_select_2, color_select, color_select_2

# Hat operations, probably edge, diffusion

# Logitech Extreme 3d - Axes range -1.0 to 1.0
# Deadzone is the minimum amount stick must move to register as valid
# Ticks is the tick value sent to the ETC console, range 0.000 to *#.###
# The OSC tick value will be mapped from axis input of deadzone to +-1.0
# to the range +-0.000 to Ticks max value
# These will apply to x, y, z axes and modes unless defined explicitly
# below:
DEADZONE_DEFAULT = 0.2
TICKS_COARSE_MAX_DEFAULT = 4.0
TICKS_FINE_MAX_DEFAULT = 4.0

# If an axis needs different values, or control parameters need to be 
# separated, make the change here. Parameter names must match the string
# for the OSC wheel command. Use 'none' to disable Parameters.

# Axis Calibration:
# Set the actual min and max values in case controller doesn't output
# all the way to +-1.0. Tuple with min and max
AXIS_CALIBRATION = (
    (-1.0,0.999),
    (-1.0,0.999),
    (-0.968,0.90),
    (-1.0,1.0),
)
# Amount stick must move from center to be considered valid
# not applying to slider due to physical functionality
AXIS_DEADZONE = (
    DEADZONE_DEFAULT,
    DEADZONE_DEFAULT,
    0.4,
    2.0 # greater than 1 essentially disables axis
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

# State for joystick when locked, not currently tracking the slider axis
# Shouldn't need to change this unless specific use case
JOYSTICK_LOCK_STATE = (True, True, True, False)

### End User Defined Globals ###########################################


# Reference: partial events list:
# QUIT              none
# JOYAXISMOTION     instance_id, axis, value
# JOYBALLMOTION     instance_id, ball, rel
# JOYHATMOTION      instance_id, hat, value
# JOYBUTTONUP       instance_id, button
# JOYBUTTONDOWN     instance_id, button
# USEREVENT         code

# For module use only
_QUIT = pygame.QUIT
_AXIS = pygame.JOYAXISMOTION
_BALL = pygame.JOYBALLMOTION
_HAT = pygame.JOYHATMOTION
_BUTTONDOWN = pygame.JOYBUTTONDOWN
_BUTTONUP = pygame.JOYBUTTONUP
_USER = pygame.USEREVENT

# Items for pygame event filter:
_JOYSTICK_EVENTS = (_QUIT, _AXIS, _BALL, _HAT, _BUTTONDOWN, _BUTTONUP, _USER)

class JoystickOSC:
    """
    Handles joystick pygame calls and modes:
    """
    def __init__(self, joystick_index=0):
        """
        initialize variables for controller. May add functions later
        to change these values programatically
        arguments:
            joystick_index, assumes only 1 connected, but could change
            the index value on init
        """
        # setup initial class input type state holders
        self.joystick = None
        self.axes = None
        self.button_state = [False]
        self.hats = None
        # sets which axes are outside of deadzone to prevent streaming zeros
        self.axis_active = [False]
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
        self.event.set_allowed(_JOYSTICK_EVENTS)

            # Get a list of connected Joysticks
        joysticks = [stick.Joystick(x) for x in range (stick.get_count())]

        if not joysticks:
            logger.error("No joysticks found")
        else:
            self.joystick = stick.Joystick(joystick_index) # Logitech Extreme 3D
            if not self.joystick.get_init():
                self.joystick.init()
            j_id = self.joystick.get_guid() # 0300eb976d04000015c2000000000000
            # get what the joystick has
            axes = self.joystick.get_numaxes() # 4
            buttons = self.joystick.get_numbuttons() # 12
            hats = self.joystick.get_numhats() # 1
            balls = self.joystick.get_numballs() # 0
            power = self.joystick.get_power_level() # NA

            self.axes = [0.0] * axes
            self.axis_active = [False] * axes
            self.button_state = [False] * buttons
            self.hats =  [(0, 0)] * hats

            logger.info(
                f"joystick: {self.joystick.get_name()} "
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
    
    # Main callable function
    def poll(self, events=None):
        """
        Call this in a loop to continuously query for joystick events
        The events argument is provided mostly for special cases or
        testing. Should not be needed for most applicaitons.
        """
        if not events:
            # If any axis are active we want to get their values and force
            # an event for it
            self._probe_axes()
            events = self.event.get(pump=True)
        if events:
            self._readEvents(events)
        

    # Sample single event list item, for reference:
    # <Event(1536-JoyAxisMotion {'joy': 0, 'instance_id': 0,
    #  'axis': 0, 'value': 0.2882473220007935})>
    def _readEvents(self, events):
        """
        Polling will pass events to this function
        """
        for event in events:
            # if event == _AXIS:
            #     print(event)
            if event and hasattr(event, 'instance_id'):
                if event.instance_id == 0:
                    if event.type == _AXIS:
                        self._handleAxes(event.axis, event.value)
                    elif event.type == _BUTTONDOWN:
                        self._handleButton(event.button, True)
                    elif event.type == _BUTTONUP:
                        self._handleButton(event.button, False)
                    elif event.type == _HAT:
                        self._handleHat(event.hat, event.value)
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
        result = (to_min + (float(value - from_min) / 
                        (from_max - from_min)) * (to_max - to_min))
        return round(result, 3)

    def _handleAxes(self, axis, value):
        """
        Gets called when an axis event is read from pygame.
        maps the axis value to range we want.
        If any axes have not been homed since last lock, nothing will be
        sent.
        args:
            axis, int
            value, float
        """
        # if any items in lock are true, unlocked becomes false
        self.axes[axis] = value
        unlocked = self._check_unlock()
        # use max and min values from calibration
        axis_max = AXIS_CALIBRATION[axis][1]
        axis_min = AXIS_CALIBRATION[axis][0]
        # We will use the deadzone value as our map minimum
        dead = AXIS_DEADZONE[axis]
        # Set map maximum to coarse, the if statement checks for fine
        map_max = TICKS_MAX_COARSE[axis]
        if self.wheel_fine:
            map_max = TICKS_MAX_FINE[axis]
        # Check if our value is above or below the deadzone
        # Enables axis if so
        # print(f"{axis} {self.axis_active[axis]} {value}")
        if value > dead:
            if unlocked:
                self.axis_active[axis] = True
                mapped = self._remap(value, dead, axis_max, 0.0, map_max)
        elif value < -dead:
            if unlocked:
                self.axis_active[axis] = True
                mapped = self._remap(value, -dead, axis_min, 0.0, -map_max)
        else:
            mapped = 0
            # if axis is zero turn off active status
            self.axis_active[axis] = False
            # Check total lock status again in case this was the last
            # locked axis
            unlocked = self._check_unlock()
        # Only send our output if there are no axis locks
        if unlocked and self.axis_active[axis]:
            self._sendAxis(axis, mapped)
        # print(f"{axis} {self.axis_active[axis]} {self.joystick_lock[axis]}")

    def _probe_axes(self):
        """
        Get axis values and add them to the event queue if they are
        already outside of the deadzone. This enables continual wheel
        ticks streaming even if axis held at a single value
        """
        num_axes = len(self.axes)
        for axis in range(num_axes):
            if self.axis_active[axis]:
                axis_value = self.joystick.get_axis(axis)
                self._handleAxes(axis, axis_value)
                # I was using pygame events, but seems I was flooding the queue
                # axis_event = self.event.Event(
                #     _USER,{'instance_id': 0, 'axis': axis, 'value': axis_value})
                # self.event.post(axis_event)
                # print(f"{axis} {self.axis_active[axis]} {axis_value}")


    # When event handler receives a button press, send it here
    def _handleButton(self, button, state):
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
                    self._lock_axes()
            # if button for ptz/hs is pressed
            elif button_function == 'hue_sat':
                # set mode param2 (hue/sat) is true
                self.wheel_param2 = state
                # check if we lock the controls between param states
                if(
                    (state and PARAM1_TO_PARAM2_LOCK) or
                    ((not state) and PARAM2_TO_PARAM1_LOCK)
                ):
                    self._lock_axes()
        # Buttons intended to fire specific osc commands
        elif op_mode == 'osc':
            # Generate string and send osc
            return #temporary filler
        else:
            logging.error(f"button function: {op_mode} not valid")
            return
    
    def _lock_axes(self):
        """
        Sets axis lock if by checking if an axis global lock state is
        true and if the axis is not already in a homed position
        (within deadzone).
        """
        self.joystick_lock = [
            lock and active
            for lock, active in
            zip(JOYSTICK_LOCK_STATE, self.axis_active)
        ]
        if not self._check_unlock():
            logging.info("Joystick Locked, home axes")

    def _check_unlock(self):
        """
        Make sure all axes are at a homes state simultaneously before
        allowing joystick unlock. Go through last reported value for
        each axis, and return true if all axes are within deadzone.
        Will relock any axis that goes out of deadzone while any other
        axis is locked
        """
        unlocked = False
        log_unlock = False
        if not any(self.joystick_lock):
            unlocked = True
        else:
            log_unlock = True
            for axis in range(len(self.axes)):
                # If axis is intended to determine lock state
                if JOYSTICK_LOCK_STATE[axis]:
                    dead = AXIS_DEADZONE[axis]
                    if abs(self.axes[axis]) > dead:
                        self.joystick_lock[axis] = True
                    else:
                        self.joystick_lock[axis] = False
                # Safety catch, clears irrelevant axis possible lock
                else:
                    self.joystick_lock[axis] = False
        if not any(self.joystick_lock):
            unlocked = True
            # Need to prevent continual streaming to log, so only log
            # when going from locked to unlocked
            if log_unlock:
                logger.info("Axes unlocked")
        return unlocked

    def _handleHat(self, hat, value):
        return

    def _sendAxis(self,
                axis,
                ticks,
                coarse_fine='coarse',
                axis_mode='PTZ'):
        """
        Send Axis values to defined ETC OSC Wheel parameter.
        """
        coarse_fine = self.wheel_fine
        axis_mode = self.wheel_param2
        print(
            f"axis:{axis:<2} "
            f"ticks:{ticks:<6} "
            f"mode:{coarse_fine:<2} "
            f"control:{axis_mode:<2} "
            f"active:{self.axis_active[axis]} "
            f"lock:{self.joystick_lock} "
            f"joy:{self.axes[axis]:<4} "
        )
        return

