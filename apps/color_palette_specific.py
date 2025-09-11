"""
This script was created with the help of AI.
Specific project for recording all color palette details
"""

import json
import logging
import os
import re
import time
from platformdirs import user_documents_dir
from osc.logging_config import setup_logging, helper_logger
from osc.etcosc import etcosc


# TODO: Output to JSON



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

# Global vars

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
        chan_ranges = [""]
        list_range = (int(cp_address[4]))
        chan_ranges = args[2:list_range]
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
        byType_channels = [""]
        list_range = (int(cp_address[4]))
        byType_channels = args[2:list_range]
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
    global cp_data_file
    try:
        with open(json_path, 'r') as f:
            logger.info(f"CP File {json_path} Successfully opened, extracting data")
            data = json.load(f)
            for cp, obj in data.items():
                cp_num = obj["palette_num"]




    except FileNotFoundError:
        logger.error("Color Palette JSON File not found")
    except json.JSONDecodeError:
        logger.error("Color Palette JSON file cannot be decoded")



# Run script Here:
get_cp_params()
# get_all_cp()
# while True:
    # time.sleep(0.5)