My OSC GUIDE:

# FROM APPENDIX GET OSC LIST CONVENTIONS DOCUMENTED



# ######################################################################################################################
# To Test:
/eos/chan/<chan num>/param/<param(s)>/<level command> - out, home, remdim, level, full, min, max, +%, -%


# ######################################################################################################################
# Basic Notes

Arguments:
Numeric arguments with a decimal are treated as 32-bit floating point numbers. Numeric arguments without a
decimal are treated as 32-bit integer numbers. Non-numeric arguments are treated as strings.

- All commands must begin with /eos/
- user commands must begin with /eos/user/<number>/

/eos/subscribe - if set to 1, eos will output /eos/out/notify if any targets change that need to be re-synced with external application

-- setable and resetable (persistance) commands
- user number - 
- OSC Global Wheel Mode - /eos/wheel <0=coarse|1=fine> - generates /eos/out return
- /eos/reset - clears presistent osc settings like OSC user ID and wheel mode

# ##example filter and subscribe from C code in etc lighthack github, use to generate description and examples
  // Add a filter so we don't get spammed with unwanted OSC messages from Eos
  OSCMessage filter("/eos/filter/add");
  filter.add("/eos/out/param/*");
  filter.add("/eos/out/ping");
  SLIPSerial.beginPacket();
  filter.send(SLIPSerial);
  SLIPSerial.endPacket();

  // subscribe to Eos pan & tilt updates
  OSCMessage subPan("/eos/subscribe/param/pan");
  subPan.add(SUBSCRIBE);
  SLIPSerial.beginPacket();
  subPan.send(SLIPSerial);
  SLIPSerial.endPacket();

  OSCMessage subTilt("/eos/subscribe/param/tilt");
  subTilt.add(SUBSCRIBE);
  SLIPSerial.beginPacket();
  subTilt.send(SLIPSerial);
  SLIPSerial.endPacket();

  Parameter Subscriptions:
After subscribing to one or more parameters using /eos/subscribe/param/<parameter> (see above), Eos will send out an OSC packet
for each parameter as they change
"/eos/out/param/<parameter>", <float argument: level>, <float argument: range min>, <float argument: range max>
o NOTE: if channel selection does not contain the parameter, the command is still sent, but with no arguments


# ######################################################################################################################
# EOS OUTPUTS to Parse or verify

Chan -  /eos/out/active/chan <string - range active channels and first channel current values>
        /eos/out/active/wheel/<number>, <string with paramater name and value from first active chan>
**** GET OTHER OUTPUTS THAT COME WITH ACTIVE CHAN, LIKE WHEELS

Direct Selects - /eos/out/ds/<index> <string> - contains "target name (chan, group, etc) [<page number> - <mode (flexi)>]" eg "Groups[1-Flexi]"
                 /eos/out/ds/<indes>/<button index> - contains "name[<number>]"

Fader - /eos/out/fader/<index>/<fader>/name <"Fader label for OSC fader">
        /eos/out/fader/<index>/<fader> <float fader percentage>
        /eos/out/fader/<index> <"descriptive text for OSC fader bank">

# ######################
# OSC Receive Global user number
User - /eos/user <user> - sets OSC receiving user number at the console,
    as opposed to including it in the command. -1 will set it to current
    console user (usually 1), 0 will set background user (this works
    for macros etc), or set to other valid user number
       /eos/out/user <user>
# #####################

Command -   /eos/out/user/<number>/cmd - <string from user command line entry>
            /eos/out/cmd <string with current command line text>

Cue -       /eos/out/active/cue --- fill these in later multiple responses see show control manual
            /eos/out/pending/cue --- see control manual

# ######################################################################################################################
# EOS KEYS AND COMMAND LINE

/eos/key/<name> <(optional) 1.0=down|0.0=up> see supported key names
    For slash key use backslash /eos/key/\

Command line can include string substitution with arguments
/eos/cmd <string> - example /eos/cmd "Chan 1 At 75#" (# or Enter)
                            /eos/cmd "Chan %1 At %2#", 1, 75 (sets channel 1 to 75%)
                            /eos/cmd/<text>/<text>/<text>/... - optional method to do in-line command arguments
/eos/newcmd - same as /eos/cmd, but resets command line first
/eos/event - same as /eos/cmd but as console event
/eos/newevent - same, but rests command line first

# ######################################################################################################################
# EOS CHANNEL COMMANDS - ADDRESS COMMANDS - GROUPS
# ## Active commands are when there is an existing target for current user

EOS CHANNEL COMMANDS:
    /eos/chan <chan num> - selects channel
INTENSITY (0-100):
    /eos/chan/<chan num> <intensity>
    /eos/at <intensity> - for active target
CHAN SET PARAM OR DMX INFO (NUM OF PARAMS IS VARIABLE):
    /eos/chan/<chan num>/dmx <dmx512 decimal value>
    /eos/chan/<chan num>/param/<param>/<param 2>/<param 3>/... <value> # Set all params to same value
    /eos/chan/<chan num>/param/<param>/<param 2>/<param 3>/... <value>,<value 2>, <value 3>, ... Set each param to own leve
    /eos/chan/<chan num>/param/<param>/<param 2>/.../dmx <values(s)>  # same as above, but sending DMX decimal values instead of param specifi
    ACTIVE TARGET PARAMS:
        Same as above, but /eos/param/<param(s)>/...

SET LEVEL COMMANDS (can optionally set button edge with 1.0-down 0.0-up):
    SPECIFIC TARGET: /eos/chan/<chan num>/x <command>
    ACTIVE TARGET:   /eos/at/<level command> - or /eos/param/<param(s)>/<level command>
        *Level commands:* out, home, remdim, level, full, min, max, +%, -%
        *It's not documented, but /eos/chan/<chan num>/param/<param(s)>/<level command> may work

ADDRESS:
    /eos/addr <addr> - select address
    /eos/addr/<address> - <0-100>
    /eos/addr/<address>/dmx - <0-255>

GROUPS:
    almost identical to channel, including Level Commands.  Only "at" method is not available


# ######################################################################################################################
# WHEEL AND SWITCH (ENCODERS) - 
# Complete: basic level documentation
# #### ETC DOCUMENTATION ERROR, coarse, is erroneously spelled course in some examples
- Wheel and Switch are variants:
    Wheel must continually send values
    Switch allows sending a single value, and it will keep inc/decr that value until set to 0. BE CAREFUL, CAN BE DISRUPTIVE IF NOT RESET TO 0
    "wheel" can be replaced with "switch" in all following examples, though the tick values are not necessarily equal

Wheel/switch modes are 0=coarse|1=fine, general default is coarse.  If not included in OSC address will use default
float values are the number of ticks for current mode, ie. -1.0 decrease value, 1.0 increase value.
Tick float values can be 3 significant digits 1.000
Params can also take level commands i.e. full/level/out - see channel control section

An index is a 1-based index reference for list of current channel parameters, for example 2 might be "red"
all /eos/wheel can be replaced with /eos/switch. return values will still be /eos/out/(active/)wheel, though
/eos/wheel <0.0|1.0>(f) sets OSC command global wheel mode
    returns /eos/out/wheel (float)
/eos/wheel/level = <positive|negative(float)> sets the global OSC positive and negative movement speeds for active mode
/eos/wheel/<index> <0.0|1.0>(f) sets OSC coarse/fine mode for specific index
/eos/wheel/<index>/level (float), same as /eos/wheel/level, but specific to index, OSC user setting
/eos/active/wheel/(coarse|fine/)<index> (float), move index by positive or negative float ticks
/eos/wheel/(coarse|fine/)<param>(/param2/...) <float> can have more than one param in address, but only a single argument
    moves active chan param(s) by argument wheel ticks.

    returns: /eos/out/active/wheel/2, Red  [78](s), 3(i), 77.900(f) 
                "Red [78]" = param name and rounded value, 3(int) = I believe this is param class-color is 3, 77.900(float), is actual value in range
    Also returns hue and saturation: /eos/out/color/hs, 293.308(f), 49.211(f)

# ######################################################################################################################
# DIRECT SELECTS - Must first send creation command
# ## EOS will send description and button labels for all OSC direct selects
- Target types, Chan, Group, Macro, Sub, Preset, IP, FP, CP, BP, MS, Curve, Snap, FX, Pixmap, Scene

# ######################################################################################################################
# FADER BANKS - Must first send creation command
# index of 0 references master fader

# ######################################################################################################################
# PALETTES

PALETTE (1 OF 3):
/eos/get/<palette type>/<palette number>/list/<list index>/<list count> =
<uint32: index>
<string: OSC UID>
<string: label>
<bool: absolute>
<bool: locked>
For Example:
/eos/out/get/ip/1/list/0/5 = 0, “00000000-0000-0000-0000-000000000000”, “My IP One Label”, False, False
PALETTE (2 OF 3):
/eos/get/<palette type>/<palette number>/channels/list/<list index>/<list count> =
<uint32: index>
<string: OSC UID>
<OSC Number Range: channel list>
For Example:
/eos/out/get/ip/1/channels/list/0/3 = 0, “00000000-0000-0000-0000-000000000000”, 1-5(s)
PALETTE (3 OF 3):
/eos/get/<palette type>/<palette number>/byType/list/<list index>/<list count> =
<uint32: index>
<string: OSC UID>
<OSC Number Range: by type channel list>
For Example:
/eos/out/get/ip/1/byType/list/0/2 = 0, “00000000-0000-0000-0000-000000000000”

# ######################################################################################################################
# Magic Sheets

# ######################################################################################################################
# MACROS

# ######################################################################################################################
# SUBS

# ######################################################################################################################
# CUES

# ######################################################################################################################
# OTHER - curve, effects, snapshots, pixel maps

# ######################################################################################################################

osc.send_message('/eos/chan/1/at/', 75)
osc.send_message('/eos/chan', 31) # success
osc.send_message('/eos/param/red/green', 50, 60)
osc.send_message('/eos/cmd', 'Chan 31 At 60 Enter')
/eos/cmd/Chan/%1/At/%2#, [1, 75]  #example of how to insert vars into command line argument

# ######################################################################################################################
# IMPLICIT OUTPUTS

Command Line:
“/eos/out/user/<number>/cmd”, <string argument with current command line text for the current console user>
“/eos/out/cmd”, <string argument with current command line text>

Active Channels and Parameters:
“/eos/out/active/chan”, <string argument with active channels and current value from the 1st channel>
“/eos/out/active/wheel/<number>, <string argument with parameter name and current value from the 1st channel>

OSC Settings:
“/eos/out/user”, <integer argument with current OSC user ID>
“/eos/out/wheel”, <float argument with current OSC wheel mode: 0.0=Coarse, 1.0=Fine>
“/eos/out/switch”, <float argument with current OSC switch mode: 0.0=Coarse, 1.0=Fine>

Active Cue (updated once per second while changing):
“/eos/out/active/cue/<cue list number>/<cue number>”, <float argument with percent complete (0.0-1.0)>
“/eos/out/active/cue”, <float argument with percent complete (0.0-1.0)>
“/eos/out/active/cue/text”, <string argument with descriptive text about the active cue, ex: “1/2.3 Label 0:05 75%”>
“/eos/out/pending/cue/<cue list number>/<cue number>”
“/eos/out/pending/cue/text”, <string argument with descriptive text about the pending cue, ex: “1/2.4 Label 0:30”>



# ######################################################################################################################
# RESPONSE OUTPUTS

OSC Fader Banks (When a fader is moved via OSC, the return /eos/fader value will be delayed for 3 seconds, presumably to 
avoid large OSC output buffer trying to output every step along the fader move):
# Add later if needed

OSC Show Control Events:

Show File Information:

Miscellaneous Console Events:
“/eos/out/event/state”, <integer argument, 0=Blind, 1=Live>
"/eos/out/ping", <return arguments>
    Note: When Eos receives the command “/eos/ping” it will reply with “/eos/out/ping”. You may
    optionally add any number of arguments and Eos will reply with the same arguments. This may be
    useful for testing latency.

# ######################################################################################################################
# RESPONSE OUTPUTS

---- see wheel switch section for better description
- /eos/wheel <0=course|1=fine>
    - /eos/out/wheel <mode>
- /eos/active/<wheel|switch>/<index> <float>
    - /eos/out/active/wheel/<index> <"wheel index name"> <first active chan value>
    - NOTE: response will always be wheel, even if send uses switch


# ######################################################################################################################
# OSC Show Control Events

Show control events are fired as the console executes the corresponding action, much like MIDI Show Control
output events.
“/eos/out/event/cue/<cue list number>/<cue number>/fire”
“/eos/out/event/cue/<cue list number>/<cue number>/stop”
“/eos/out/event/sub/<sub number>”, <integer argument, 0=Bump Off, 1=Bump On>
“/eos/out/event/macro/<macro number>”
“/eos/out/event/relay/<relay number>/<group number>”, <integer argument, 0=On, 1=Off>
“/eos/out/event” (used for time code learn)
Show File Information
“/eos/out/show/name”, <string argument with show title>
“/eos/out/event/show/saved”, <string argument with file path>
“/eos/out/event/show/loaded”, <string argument with file path>
“/eos/out/event/show/cleared”
Miscellaneous Console Events:
“/eos/out/event/state”, <integer argument, 0=Blind, 1=Live>