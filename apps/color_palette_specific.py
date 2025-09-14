"""
This script was created with the help of AI.
Specific project for recording all color palette details.
Will automatically change any color palettes channel ranges to by type if all channels
of same manufacturer and model have the same values
"""

import json
import logging
import os
import re
import threading
from functools import partial
import time
from platformdirs import user_documents_dir
from osc.logging_config import setup_logging, helper_logger
from osc.etcosc import etcosc


TX_IP = "127.0.0.1"
TX_PORT = 8000
RX_PORT = 8001

OUTPUT_DIR = user_documents_dir()
PALETTE_DIR = os.path.join(OUTPUT_DIR, "color_palettes")
os.makedirs(PALETTE_DIR, exist_ok=True)
json_path = os.path.join(PALETTE_DIR, "palette_results.json")

setup_logging()
logger = logging.getLogger(__name__)

osc_manager = etcosc(
    mode='txrx',
    tx_udp_ip=TX_IP,
    tx_port=TX_PORT,
    rx_port=RX_PORT,
    ping=False      # Turn off ping since this isn't a live update script
)

# Regex pattern to pull data from the string returned when color palette edit
# Example usage:
# match = EOS_CHANNEL_PATTERN(string_to_regex)
# ranges = match.group('ranges')
EOS_CHAN_PATTERN = re.compile(
    r"^(?P<ranges>[\d,-]+)\s+"          # Capture channel ranges
    r"(?P<unknown_field>\S*)\s*"        # Capture the optional status field
    r"\[(?P<intensity>[^\]]+)\]\s+"     # Capture intensity
    r"(?P<label>.*?)\s*"                # Capture optional label
    r"(?P<manufacturer>\S+)\s+"         # Capture manufacturer
    r"(?P<model>\S+)\s+@\s+"            # Capture model
    r"(?P<dmx>\d+)$"                     # Capture DMX address
)

# Set up threading event to wait for each palette response before sending next one
# Otherwise all get/CP are sent at once, and not all replies may happen

def get_all_cp():       # Should these all be separate calls, or one call with type as an argument?
    """ 
    Check txrx
    returns an uint32 with a count of the item sent
    /eos/get/<item>/count
    Can be patch, cuelist, /cue/<clue list number>, group, macro,
    sub, preset, ip(intensity palette), fp(focus palette),
    cp(color palette), bp(beam palette), curve, fx, snap(snapshot),
    pixmap, ms(magic sheet)
    """
    count_string = "/eos/get/cp/count"
    count_rx_string = "/eos/out/get/cp/count"
    osc_manager.osc_receiver_raw(count_rx_string, _count_handler)
    osc_manager.osc_send_raw(count_string)

def _count_handler(address, *args):
    """
    Receive and store the count, it'll be first item in arg list.
    arg will be a one item list of ints
    """
    global CP_COUNT
    global cp_present_flag
    CP_COUNT = args[0]
    logger.info(f"hander {address} received {CP_COUNT}")
    if CP_COUNT > 0:
        # Let details methods know there are CPs
        cp_present_flag = True
        # Setup CP osc Receiver
        address = "/eos/out/get/cp"
        osc_manager.osc_receiver_raw(address, _detail_handler, partial_string=True)
        logger.info("Getting all Color Palette Details")
        # First call to function
        _get_details_by_count()


# Lazy Globals
cp_present_flag = False
cp_send_counter = 0
current_color_palette = {}
color_palette_output = {}
def _get_details_by_count():   # again, should this be separate methods?
    """
    all start with /eos/get example: /eos/get/cp/index/<index #>
    Args for each response will be:
        <uint32: list index><string: UID>...See show control user
        guide starting end page 70 for information about each type
    Response will start with /eos/out/get/cp/<cp#>/list/<list index>/<list count>
    Recall from handler when received messages are done being processed to 
    continue iteration.
    """
    global cp_present_flag
    global cp_send_counter
    global CP_COUNT
    if cp_present_flag:
        if (cp_send_counter < CP_COUNT):
            osc_manager.osc_send_raw(f"/eos/get/cp/index/{cp_send_counter}")
            cp_send_counter += 1
        else:
            _write_json_details()
            cp_present_flag = 0

def _detail_handler(address, *args):
    """
    Record details of each Color Palette
    """
    print(f"{address:<35}: {args}")
    logger.log(helper_logger(), f"{address:<35}: {args}")
    # Tell _get_details_by_count we are ready for next request
    _build_palette_json(address, args)

def _build_palette_json(address, args):
    """
    We will build the base json structure for the color palettes with the details
    of get/cp/index. We will later fill in more details concerning actual stored values
    in the palette.
    """
    # We will start palette structure. 
    # Response from /eos/get/cp/index/1 list count seems to be number of args
    # In the first output the last argument (int) is not defined in the documentation
    # explanation for everything after /eos/out/get/cp/
    # /eos/out/get/cp/2/list/0/6, 1(i), 4992522F-2884-4DF1-BFF2-C72FC3CDDD16(s), Blue(s), False(F), False(F), 0(i)
    #   /<CP#>/list/<listIndex>/<listCount> args: index, "OSC_UID", "label", bool absolute, bool locked
    #   list after regex: cp#, list, listind, listcount
    # /eos/out/get/cp/2/channels/list/0/7, 1(i), 4992522F-2884-4DF1-BFF2-C72FC3CDDD16(s), 31-47(s), 151-166(s), 201-204(s), 211-212(s), 401-423(s)
    #   /<CP#>/channels/list/<listIndex>/<listCount>, index, "OSC_UID", OSC Number Range: Channel list as commas separated strings
    #   list after regex: cp#, channels, list, listind, listcount
    # /eos/out/get/cp/2/byType/list/0/7, 1(i), 4992522F-2884-4DF1-BFF2-C72FC3CDDD16(s), 31(i), 151(i), 201(i), 211(i), 401(i)
    #   /<CP#>/byType/list/<listIndex>/<listCount>, index, "OSC_UID", OSC Number Range: by type channel list as comma separated strings
    #   list after regex: cp#, byType, list, listind, listcount
    # After receiver is set up we can start iterating through CP count to get the info
    # regex to pull just values after /eos/out/get/cp/
    # that would leave
    address_pattern = r"\/eos\/out\/get\/cp\/(.*)"

    cp_regex = re.search(address_pattern, address)
    cp_address = cp_regex.group(1)
    cp_address = cp_address.split("/")
    print(cp_address)
    global color_palette_output
    global current_color_palette
    cp = cp_address[0]
    response_type = cp_address[1]
    cp_uid = args[1]
    cp_index = args[0]
    eos_out = f"{address}: {args}"
    if response_type == "list":
        # 2/list/0/6, 1(i), UID(s), Blue(s), False(F), False(F), 0(i)
        print("list found")
        current_color_palette.update({
            "eos_out": eos_out,
            "palette_num": cp,
            "cp_label": args[2],
            "cp_index": cp_index,
            "cp_list_listIndex": cp_address[2],
            "cp_list_num_args": cp_address[3],
            "cp_type_absolute": args[3],
            "cp_locked": args[4],
            "cp_undefined_int": args[5]
        })
    elif response_type == "channels":
        # Number of list count minus the cp number and uid is how many chan ranges
        # there are
        list_range = (int(cp_address[4]))
        raw_chan_ranges = args[2:list_range]
        # We have to make sure they are all strings, EOS sends the item as an integer
        # instead of string if it is only one channel instead of a range
        chan_ranges = [str(item) for item in raw_chan_ranges]
        # 2/channels/list/0/7, 1(i), UID(s), 31-47(s), 151-166(s), 201-204(s), 211-212(s), 401-423(s)
        current_color_palette.update({
            "eos_out": eos_out,
            "palette_num": cp,
            "cp_index": cp_index,
            "cp_channels_listIndex": cp_address[3],
            "cp_chan_num_args": cp_address[4],
            "chan_ranges": chan_ranges
        })
    elif response_type == "byType":
        list_range = (int(cp_address[4]))
        raw_byType_channels = args[2:list_range]
        byType_channels = [str(item) for item in raw_byType_channels]
        # 2/byType/list/0/7, 1(i), UID(s), 31(i), 151(i), 201(i), 211(i), 401(i)
        current_color_palette.update({
            "eos_out": eos_out,
            "palette_num": cp,
            "cp_index": cp_index,
            "cp_byType_listIndex": cp_address[3],
            "cp_byType_num_args": cp_address[4],
            "byType_channels": byType_channels
        })
    
    logger.log(helper_logger(), f"current: {current_color_palette}")
    if all(k in current_color_palette for k in ("cp_list_num_args",
                                                "cp_chan_num_args",
                                                "cp_byType_num_args")):
        color_palette_output.update({
            cp_uid: current_color_palette
        })
        _write_json_details()
        _get_details_by_count()
        logger.log(helper_logger(), f"Full: {color_palette_output}")
        current_color_palette = {}

def _write_json_details():
    """
    Record the values to the json file after all collected
    """
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(color_palette_output, f, indent=2)

current_cp_params = {}
def get_cp_params():
    """
    Get all the channel and specific color detail for palette
    """
    global current_cp_params
    current_chan = 0
    cp_num = 0
    user_number = 3
    start_string = f"/eos/user/{user_number}"
    # Define address commands here for easier management
    address_clear_line = f"{start_string}/newcmd"
    address_blind = f"{start_string}/cmd/blind"
    address_open_cp = f"{start_string}/cmd/color_palette/{cp_num}/#"
    address_edit = f"{start_string}/cmd/edit"
    address_select_active = f"{start_string}/cmd/select_active/#"
    address_select_chan = f"{start_string}/cmd/chan/{current_chan}/#"
    # These are the receiving addresses we need to catch:
    out_start_string = "/eos/out"
    out_active_chan = f"{out_start_string}/active/chan"
    out_active_wheel = f"{out_start_string}/active/wheel"
    out_hue_sat = f"{out_start_string}/color/hs"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            logger.info(f"CP File {json_path} Successfully opened, extracting data")
            data = json.load(f)
            # Set console to blind and edit color palette, then softkey edit
            osc_manager.osc_send_raw(address_clear_line)
            osc_manager.osc_send_raw(address_blind)
            # Loop through all the color palettes
            for cp_uid, cp_obj in data.items():
                cp_num = cp_obj["palette_num"]
                logger.info(f"Processing CP {cp_num}: {cp_obj['cp_label']}")
                print(cp_obj['chan_ranges'])
                channel_list = []
                by_type = cp_obj["byType_channels"]
                # Iterate through the channel ranges in the palette
                for range_str in cp_obj['chan_ranges']:
                    # we need to separate the starting and ending numbers
                    range_split = range_str.split("-")
                    start_chan = int(range_split[0])
                    if len(range_split) == 2:
                        end_chan = int(range_split[1])
                        for chan in range(start_chan, end_chan + 1):
                            channel_list.append(chan)
                    elif len(range_split) == 1:
                        channel_list.append(start_chan)
                # Create state object that gets passed to handler
                current_request_state = {
                    "request_info": {'request_type': 'select_active',
                                     'cp_num': cp_num,
                                     'channel': None},
                    'responses': [],
                    'timer': None,
                    'completion_event': threading.Event()
                }
                # Create the handler including the state data
                handler_with_state = partial(_param_collector_handler,
                                            current_request_state)
                # Register all the osc addresses we expect for the query
                osc_manager.osc_receiver_raw(out_active_chan, handler_with_state)
                osc_manager.osc_receiver_raw(out_active_wheel,
                                             handler_with_state,
                                             partial_string=True)
                osc_manager.osc_receiver_raw(out_hue_sat, handler_with_state)
                # send OSC message select active
                # Now that we have a full channel list lets get the palette global info
                osc_manager.osc_send_raw(address_clear_line)
                osc_manager.osc_send_raw(address_open_cp)
                osc_manager.osc_send_raw(address_edit)
                # Select active will return a string with overall palette info
                osc_manager.osc_send_raw(address_select_active)
                # log sent and wait
                logger.info(f"Sent select_active to CP {cp_num}, waiting for response:")
                current_request_state["completion_event"].wait(timeout=2.0)
                # After getting response to select active we will query each channel
                ##############################################################################################################################
    except FileNotFoundError:
        logger.error("Color Palette JSON File not found")
    except json.JSONDecodeError:
        logger.error("Color Palette JSON file cannot be decoded")


def _param_collector_handler(state, address, *args):
    """
    The main handler for collecting parameter data.
    It resets the timeout on each message and checks for early completion.
    """
    # 1. Cancel any existing timer. This is the "reset" action.
    if state["timer"]:
        state["timer"].cancel()

    # 2. Append the new data to the collection for this request.
    state["responses"].append({"address": address, "args": args})

    # 3. Your idea: Check for the "last message" for early completion.
    if "color/hs" in address:
        logger.info("'/color/hs' received, triggering early completion.")
        _process_collected_params(state)
        return # Stop here, no need to set a new timer.

    # 4. Your other idea: Set a dynamic timeout based on latency.
    # We'll use a minimum of 50ms as a safety net for very fast connections.
    latency = osc_manager.get_latency()
    timeout_duration = max(0.05, latency * 10)

    # 5. Start a new timer as a fallback.
    new_timer = threading.Timer(timeout_duration, partial(_process_collected_params,
                                                          state))
    state["timer"] = new_timer
    new_timer.start()

def _process_collected_params(state):
    """
    Final processing step called by the timer or early completion.
    This function is now responsible for signaling the main loop to continue.
    """
# LOGIC CHECKS WITH DATA:
# If a channel is in the by_type list, check that all channels of same
#   manufacturer and model are the same values, if so don't record their
#   values into the json file. Definitely record if different
# Check all channels of same manufacturer and model, if they all have
#   the same values add lowest channel number to by type list in file,
#   and only record the by type channel's data
# Add a top level key to each color palette for by_type_palette that is
#   set to True if all of the recorded channels are by type

# Response to Select Active:
# /eos/out/active/chan, 31-47,151-166,201-204,213-214,
#                       401-423  [100] ETC_Fixtures Vivid_R_11 @ 1067
# Regex IDs version of args:
# 31-47,151-166,201-204,213-214,401-423 = <ranges>
# (double_space) = <unknown_field>
# [100] = <intensity> (of first channel in ranges)
# (not in this file) = <label> (meaning channel label)
# ETC_Fixtures = <manufacturer> (white spaces replaced with underscores)
# Vivid_R_11 = <model> (white spaces replaced with underscores)
# @ indicates the next number is first patch address of first channel
# 1067 <dmx> first channel starting dmx address
    # First, make sure the timer is cancelled to prevent it from firing again.
    if state["timer"]:
        state["timer"].cancel()
        state["timer"] = None

    logger.info(f"Data collection complete for Chan "
                f"{state['request_info']['channel']}. "
                f"Received {len(state['responses'])} messages.")

    # Here you would add the logic to parse the collected state['responses']
    # and add them to your final results dictionary.
    # For now, we'll just log it.
    logger.log(helper_logger(), f"Collected for {state['request_info']['channel']}: "
               f"{state['responses']}")

    # This is the crucial step: signal the main loop that it can proceed.
    state["completion_event"].set()






# Run script Here:
get_cp_params()
# get_all_cp()
# while True:
#     time.sleep(0.5)




# gemini suggested methods

# def _process_collected_params(state):
#     """
#     Final processing step called by the timer or early completion.
#     This function is now responsible for signaling the main loop to continue.
#     """
#     # First, make sure the timer is cancelled to prevent it from firing again.
#     if state["timer"]:
#         state["timer"].cancel()
#         state["timer"] = None

#     logger.info(f"Data collection complete for Chan {state['request_info']['channel']}. "
#                 f"Received {len(state['responses'])} messages.")

#     # Here you would add the logic to parse the collected state['responses']
#     # and add them to your final results dictionary.
#     # For now, we'll just log it.
#     logger.log(helper_logger(), f"Collected for {state['request_info']['channel']}: {state['responses']}")

#     # This is the crucial step: signal the main loop that it can proceed.
#     state["completion_event"].set()


# def _param_collector_handler(state, address, *args):
#     """
#     The main handler for collecting parameter data.
#     It resets the timeout on each message and checks for early completion.
#     """
#     # 1. Cancel any existing timer. This is the "reset" action.
#     if state["timer"]:
#         state["timer"].cancel()

#     # 2. Append the new data to the collection for this request.
#     state["responses"].append({"address": address, "args": args})

#     # 3. Your idea: Check for the "last message" for early completion.
#     if "color/hs" in address:
#         logger.info("'/color/hs' received, triggering early completion.")
#         _process_collected_params(state)
#         return # Stop here, no need to set a new timer.

#     # 4. Your other idea: Set a dynamic timeout based on latency.
#     # We'll use a minimum of 50ms as a safety net for very fast connections.
#     latency = osc_manager.get_latency()
#     timeout_duration = max(0.05, latency * 10)

#     # 5. Start a new timer as a fallback.
#     new_timer = threading.Timer(timeout_duration, partial(_process_collected_params, state))
#     state["timer"] = new_timer
#     new_timer.start()


# def get_cp_params():
#     """
#     Get all the channel and specific color detail for palette
#     """
#     try:
#         with open(json_path, 'r', encoding='utf-8') as f:
#             logger.info(f"CP File {json_path} Successfully opened, extracting data")
#             data = json.load(f)

#             # Loop through each Color Palette from the first part of the script
#             for cp_uid, cp_obj in data.items():
#                 cp_num = cp_obj["palette_num"]
#                 logger.info(f"--- Processing CP {cp_num}: {cp_obj['cp_label']} ---")

#                 # For now, we'll just query the first channel found in 'byType'
#                 # A full implementation would parse the ranges and loop all channels.
#                 if not cp_obj.get("byType_channels"):
#                     logger.warning(f"No 'byType' channels found for CP {cp_num}, skipping.")
#                     continue

#                 # Let's just take the first channel for this example
#                 channel_to_query = cp_obj["byType_channels"][0]

#                 # 1. Create the state object for this specific request.
#                 current_request_state = {
#                     "request_info": {"cp_num": cp_num, "channel": channel_to_query},
#                     "responses": [],
#                     "timer": None,
#                     "completion_event": threading.Event()
#                 }

#                 # 2. Create the handler with the state "frozen" into it.
#                 handler_with_state = partial(_param_collector_handler, current_request_state)

#                 # 3. Register the handler for all the messages we expect.
#                 osc_manager.osc_receiver_raw("/eos/out/active/chan", handler_with_state)
#                 osc_manager.osc_receiver_raw("/eos/out/active/wheel/*", handler_with_state, partial_string=True)
#                 osc_manager.osc_receiver_raw("/eos/out/color/hs", handler_with_state)

#                 # 4. Send the command to Eos to select the channel.
#                 osc_manager.osc_send_raw(f"/eos/newcmd/chan/{channel_to_query}/enter")

#                 # 5. Wait here until the completion_event is set by the handler logic.
#                 logger.info(f"Sent request for Chan {channel_to_query}, waiting for responses...")
#                 current_request_state["completion_event"].wait(timeout=2.0) # 2-second safety timeout
#     except FileNotFoundError:
#         logger.error("Color Palette JSON File not found")
#     except json.JSONDecodeError:
