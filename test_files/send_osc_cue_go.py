# Created with help from AI

from pythonosc.udp_client import SimpleUDPClient
import time

# OSC target IP and port
ip = "127.0.0.1"
port = 8000

# Create OSC client
client = SimpleUDPClient(ip, port)

time.sleep(3)

# Send the cue go command ("/eos/cue/1/fire")
client.send_message("/eos/cue/5/fire", [])

print(f"Sent OSC message '/eos/cue/1/fire' to {ip}:{port}")
