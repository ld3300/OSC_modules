
##### Make sure all py modules are very thoroughly documented, including all input/output options ###

##### CURRENT TASKS #####
- figure out button strings to step through gobos, maybe also color wheels
- configure how hat works
- Figure out osc string for color temperature wheel

##### ##### ##### ##### 


test send and receive OSC: COMPLETE
### Milestone 1: Reliable OSC Send/Receive

1. Create a Python module for sending OSC messages.
2. Create a Python module for receiving OSC messages.
3. Document all functions, inputs, and outputs.
4. Write a test script to verify round-trip communication.
5. Log all sent and received messages for debugging.
# ##############################################################################

### Milestone 2 EOS OSC wrapper
Goal:
Develop a reusable Python module (eososc.py) that wraps OSCHandler and provides high-level, ETC EOS-specific OSC functionality for use in all future EOS-related projects.

Tasks:

1. Create eososc.py as a wrapper for OSCHandler
- Import and use OSCHandler internally.
- Document the module, its purpose, and its relationship to OSCHandler.
2. Implement and document core EOS actions
- ping() method: Send the ETC OSC ping command and handle the response.
- fire_cue(cue_number): Fire a cue on the EOS system.
- set_channel(channel, value): Set a channel value.
- send_raw(address, *args): Allow sending any raw OSC command/arguments directly to OSCHandler.
3. Response and connection handling
- Implement a method to verify ping responses and measure latency.
- Add callback registration for EOS responses (e.g., on_ping_response, on_cue_fired).
- Document how to use these callbacks for connection health and command verification.
4. Prepare for color palette export
- Add stubs/placeholders for color palette export and parsing methods.
- Document the expected OSC addresses and response patterns for palette export.
- Note any ETC EOS quirks or undocumented behaviors discovered.
5. Testing and extensibility
- Write unit tests for all implemented EOS methods.
- Ensure the module is well-documented and easy to extend for future EOS features.
- Add comments and docstrings explaining command construction and future intended features.

-- Notes:
- Reference and update eos_osc_command_ref.md as you discover or formalize new command patterns.
- Use docstrings and comments to clarify how each EOS-specific method works and how it interacts with OSCHandler.
- Plan for future expansion (e.g., color palette import/export, error handling, advanced EOS features).
- This milestone will provide a robust, reusable foundation for all ETC EOS automation and integration tasks, keeping your codebase organized and maintainable.

# ##############################################################################



make a module to extract color palette information using osc returns
store color palette information to probably xml file
find a way to indicate if palette is "by type"
make a module to restore color palettes to a fresh show file with selectable channel range
send command to push color palette information to new show file, including the by type indicator when appropriate
make sure existing color palettes aren't being overwritten first
Package for sharing, running on machine without needing to install python or dependencies

later:
switch from threading to async
add OSC receive method to check that send commands were successful
add ability to send subscribe commands to EOS
add modules for custom buttons, controllers, etc. This may require a webpage type UI
Add colorpicker that could run on any OSC, even a tablet or phone.
Add TCP to OSC py modules

Feature Creep options:
allow regex


Implement module for moving light autofocus process and device, this will be a tough algorithm to figure out.

potential future feature: add way to route received commands to other ports for interaction with multiple other systems.
Make color palettes persistently available on a phone or tablet interface