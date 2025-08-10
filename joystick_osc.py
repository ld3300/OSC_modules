"""
This script was created with the help of AI.
"""

import logging
import pygame
# from etcosc import etcosc

# start with init before being able to assign a joystick instance to
# read

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

JOYSTICK_EVENTS = [QUIT, AXIS, BALL, HAT, BUTTONDOWN, BUTTONUP, USER]

AXES = None
BUTTONS = None
HATS = None

# define, for each axis, the dinstance it has to move from center before
# sending any output, to account for imperfections
# Logitech Extreme 3d
AXES_DEADZONE = [0.3, 0.3, 0.3, 0.0]
# These will be tuned to reflect how the EOS system responds
AXES_MAX_COARSE = [4.0, 4.0, 4.0, 4.0]
AXES_MAX_FINE = [4.0, 4.0, 4.0, 4.0]


# Will use a button to change between Coarse/Fine
WHEEL_FINE = False
# Will use a button to change axes from x/y to Hue/Sat
WHEEL_HS = False

pygame.init()
stick = pygame.joystick
stick.init()
event = pygame.event
event.set_allowed(JOYSTICK_EVENTS)


# checking that it inialized properly
print(f"pygame.init() = {pygame.get_init()}\n"
      f"pygame.joystick.init() = {stick.get_init()}")

joysticks = [stick.Joystick(x) for x in range (stick.get_count())]


# A single event list item, for reference:
# <Event(1536-JoyAxisMotion {'joy': 0, 'instance_id': 0,
#  'axis': 0, 'value': 0.2882473220007935})>

def readEvents(events):
    """
    When pygame has events, send them here
    """
    for event in events:
        if event:
            if event.instance_id == 0:
                if event.type == AXIS:
                    handleAxes(event.axis, event.value)
                elif event.type == BUTTONDOWN:
                    handleButton(event.button, True)
                elif event.type == BUTTONUP:
                    handleButton(event.button, False)
                elif event.type == HAT:
                    handleHat(event.hat, event.value)
                else:
                    return

# For mapping axes range to the Coarse/Fine ranges
def _remap(value, from_min, from_max, to_min, to_max):
    # Map value from [from_min, from_max] to [to_min, to_max]
    return (to_min + (float(value - from_min) / 
                     (from_max - from_min)) * (to_max - to_min))

def handleAxes(_axis, _value):
    _value = _value
    # We will use the deadzone value as our map minimum
    _dead = AXES_DEADZONE[_axis]
    # Set map maximum to coarse, the if statement checks for fine
    _map_max = AXES_MAX_COARSE[_axis]
    if WHEEL_FINE:
        _map_max = AXES_MAX_FINE[_axis]
    # Check if our value is above or below the deadzone
    if _value > AXES_DEADZONE[_axis]:
        _mapped = _remap(_value, _dead, 1.0, 0.0, _map_max)
    elif _value < -AXES_DEADZONE[_axis]:
        _mapped = _remap(_value, -_dead, -1.0, 0.0, -_map_max)
    else:
        _mapped = 0
    sendAxis(_axis, _mapped) ### USE THIS FUNCTION TO SEND OUTPUT

def sendAxis(axis, ticks):
    return

# def handelButton(_button, _state):

# def handleHat(_hat, _value):

if not joysticks:
    print("No joysticks found")
else:
    joystick = stick.Joystick(0) # joystick: Logitech Extreme 3D
    if not joystick.get_init():
        joystick.init()
    j_id = joystick.get_guid() # 0300eb976d04000015c2000000000000
    # get what the joystick has
    axes = joystick.get_numaxes() # 4
    buttons = joystick.get_numbuttons() # 12
    hats = joystick.get_numhats() # 1
    balls = joystick.get_numballs() # 0
    power = joystick.get_power_level() # NA

    AXES = [0.0] * axes
    BUTTONS = [False] * buttons
    HATS =  [(0, 0)] * hats

    print(
        f"joystick: {joystick.get_name()} "
        f"ID:{j_id}\n"
        f"axes:{axes} - "
        f"buttons:{buttons} - "
        f"hats:{hats} - "
        f"trackballs:{balls} - "
        f"power:{power} "
    )

    while True:
        user_input = input(" q + enter for quit: \n")
        if user_input == 'q':
            break
        events = event.get(pump=True)
        readEvents(events)

