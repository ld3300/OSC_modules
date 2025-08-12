"""
This script was created with the help of AI.
"""

import logging
import pygame
# from etcosc import etcosc

# start with init before being able to assign a joystick instance to
# read

logger = logging.getLogger(__name__)

# Reference: partial events list:
# QUIT              none
# JOYAXISMOTION     joy (deprecated), instance_id, axis, value
# JOYBALLMOTION     joy (deprecated), instance_id, ball, rel
# JOYHATMOTION      joy (deprecated), instance_id, hat, value
# JOYBUTTONUP       joy (deprecated), instance_id, button
# JOYBUTTONDOWN     joy (deprecated), instance_id, button
# USEREVENT         code

QUIT = pygame.QUIT
AXIS = pygame.JOYAXISMOTION
BALL = pygame.JOYBALLMOTION
HAT = pygame.JOYHATMOTION
BUTTONDOWN = pygame.JOYBUTTONDOWN
BUTTONUP = pygame.JOYBUTTONUP
USER = pygame.USEREVENT

# Items for pygame event filter:
JOYSTICK_EVENTS = [QUIT, AXIS, BALL, HAT, BUTTONDOWN, BUTTONUP, USER]

class joystickosc:
    """
    Handles joystick pygame calls and modes:
    """
    def __init__(joystick_index=0):
        """
        itinalize variables for controller. May add functions later
        to change these values programatically
        arguments:
            joystick_index, assumes only 1 connected, but could change
            the index value on init
        """
        # setup initial class input type state holders
        axes = None
        buttons = [False]
        hats = None

        # define, for each axis, the dinstance it has to move from center before
        # sending any output, to account for imperfections
        # Logitech Extreme 3d
        axes_deadzones = [0.3, 0.3, 0.3, 0.0]
        # These will be tuned to reflect how the EOS system responds
        axes_max_coarse = [4.0, 4.0, 4.0, 4.0]
        axes_max_fine = [4.0, 4.0, 4.0, 4.0]
        # Modes based on button press, list of lists, for X, Y, Z, Slider
        axes_modes = [['pan', 'hue'],
                      ['tilt', 'saturation'],
                      ['zoom', 'none'],
                      ['none', 'none']]


        # Will use a button to change between Coarse/Fine
        wheel_fine = False
        # Will use a button to change axes from x/y to Hue/Sat
        wheel_hs = False
        # This mode lock prevents switching from fine to course or
        # between ptz/hs modes until stick is returned to zero
        joystick_lock = False

        pygame.init()
        stick = pygame.joystick
        stick.init()
        event = pygame.event
        # Sets which event types the pygame library is allowed to place
        # in the events list
        event.set_allowed(JOYSTICK_EVENTS)

        
            # Get a list of connected Joysticks
        joysticks = [stick.Joystick(x) for x in range (stick.get_count())]

        if not joysticks:
            logger.error("No joysticks found")
        else:
            joystick = stick.Joystick(joystick_index) # joystick: Logitech Extreme 3D
            if not joystick.get_init():
                joystick.init()
            j_id = joystick.get_guid() # 0300eb976d04000015c2000000000000
            # get what the joystick has
            axes = joystick.get_numaxes() # 4
            buttons = joystick.get_numbuttons() # 12
            hats = joystick.get_numhats() # 1
            balls = joystick.get_numballs() # 0
            power = joystick.get_power_level() # NA

            axes = [0.0] * axes
            buttons = [False] * buttons
            hats =  [(0, 0)] * hats

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



    # A single event list item, for reference:
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
        maps the axis value to range we want"""
        value = value
        # We will use the deadzone value as our map minimum
        dead = AXES_DEADZONE[axis]
        # Set map maximum to coarse, the if statement checks for fine
        map_max = AXES_MAX_COARSE[axis]
        if WHEEL_FINE:
            map_max = AXES_MAX_FINE[axis]
        # Check if our value is above or below the deadzone
        if value > AXES_DEADZONE[axis]:
            mapped = _remap(value, dead, 1.0, 0.0, map_max)
        elif value < -AXES_DEADZONE[axis]:        mapped = _remap(value, -dead, -1.0, 0.0, -map_max)
        else:
            mapped = 0
        sendAxis(axis, mapped) ### USE THIS FUNCTION TO SEND OUTPUT

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

    # def handelButton(_button, _state):

    # def handleHat(_hat, _value):

    

        while True:
            user_input = input(" q + enter for quit: \n")
            if user_input == 'q':
                break
            events = event.get(pump=True)
            readEvents(events)

