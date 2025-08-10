# Created with help from AI

"""
A simple Python OSC server to capture and inspect incoming messages.

This script listens on a specified IP address and port for OSC messages
and prints their address and arguments to the console. This is useful for
debugging and understanding the structure of OSC data sent from applications
like the ETC Eos lighting console.

Usage:
1. Make sure you have the `python-osc` library installed:
   pip install python-osc
2. Run the script from your terminal:
   python your_script_name.py
3. By default, it listens on 127.0.0.1 (localhost) at port 8001. You can
   specify a different IP or port using command-line arguments:
   python your_script_name.py --ip "0.0.0.0" --port 9001
"""

import argparse
import asyncio

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

import re

# It's more efficient to compile the regular expression once.
# This pattern uses named groups `(?P<name>...)` for clarity and robustness.
EOS_CHAN_PATTERN = re.compile(
    r"^(?P<ranges>[\d,-]+)\s+"          # Capture channel ranges
    r"(?P<unknown_field>\S*)\s*"        # Capture the optional status field
    r"\[(?P<intensity>[^\]]+)\]\s+"     # Capture intensity
    r"(?P<label>.*?)\s*"                # Capture optional label
    r"(?P<manufacturer>\S+)\s+"         # Capture manufacturer
    r"(?P<model>\S+)\s+@\s+"            # Capture model
    r"(?P<dmx>\d+)$"                     # Capture DMX address
)


def message_handler(address: str, *args):
    """
    Handles incoming OSC messages by printing their details.

    This function is a "catch-all" handler. It will be triggered for any
    OSC message received by the server.

    Args:
        address: The OSC address pattern of the received message (e.g., "/eos/out/active/cue").
        args: A list of the arguments included in the message.
    """
    print("----------------------------------------------------")  # printing starting dashes
    print(f"OSC Address: {address}")  # printing osc address

    # Check if there are no args
    if not args:  # checking if args is empty
        print("Arguments: [No arguments in message]")  # printing if args is empty
    else:  # execute if args is not empty
        print("Arguments:")  # printing 'Arguments:'
        # Loop through each argument to inspect its type and value
        for i, arg in enumerate(args):  # loop and enumerate through each arg
            # repr() is used to get a developer-friendly representation
            # of the object, which makes whitespace and other special
            # characters visible (e.g., ' ' vs. '').
            print(f"  [{i}]: {repr(arg)} (Type: {type(arg).__name__})")  # printing arg

            # Specific parsing for the channel string
            if address == "/eos/out/active/chan" and i == 0 and isinstance(arg, str):
                match = EOS_CHAN_PATTERN.match(arg)

                if match:
                    # groupdict() returns a dictionary of all the named subgroups
                    data = match.groupdict()
                    channel_ranges = data['ranges'].split(',')

                    print("\n    --- Parsed Channel Data ---")
                    print("    Channel Ranges:")
                    for channel_range in channel_ranges:
                        print(f"      - {channel_range.strip()}")

                    unknown = data['unknown_field'].strip()
                    label = data['label'].strip()
                    print(f"    Intensity:       {data['intensity']}")
                    print(f"    Unknown Field:   {unknown if unknown else '[None]'}")
                    print(f"    Fixture Label:   {label if label else '[None]'}")
                    print(f"    Manufacturer:    {data['manufacturer']}")
                    print(f"    Fixture Model:   {data['model']}")
                    print(f"    DMX Address:     {data['dmx']}")
                    print("    ---------------------------\n")
                else:
                    # This message will appear if the string format changes unexpectedly.
                    print("\n    [Parser] Could not match the Eos channel string format.")

    print(
        "----------------------------------------------------\n"
    )  # printing ending dashes, and newline


async def main(ip: str, port: int):
    """
    The main function to set up and run the OSC server.
    """
    # The dispatcher maps OSC addresses to handler functions.
    # We will use a "catch-all" approach to see every message.
    dispatcher = Dispatcher()

    # The "*" pattern matches any OSC address. All messages will be sent
    # to our message_handler function.
    dispatcher.map("*", message_handler)

    print(f"👂 Listening for OSC messages on {ip}:{port}")
    print("Press Ctrl+C to stop the server.")

    # Create and run the server. It will listen indefinitely.
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()

    try:
        # Keep the server running until it's manually interrupted.
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
    finally:
        transport.close()



if __name__ == "__main__":
    # Set up command-line argument parsing.
    # This allows you to easily change the IP and port without editing the code.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="The IP address to listen on (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="The port to listen on (default: 8001)"
    )
    args = parser.parse_args()

    # Run the main asynchronous event loop.
    try:
        asyncio.run(main(args.ip, args.port))
    except Exception as e:  # catching exceptions
        print(f"An error occurred: {e}")  # printing exception
