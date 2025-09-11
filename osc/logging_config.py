### Created with the assistance of AI ###
r"""
Logging configuration setup.
Writes logs to system user logs directory
Needs to be imported into each apps level file
Windows: C:\Users\<user>\appdata\local\DavidOSmith
macOS: ~/Library/Logs/DavidOSmith
Linux: ~/.local/share/DavidOsmith
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler
from platformdirs import user_log_dir
from platformdirs import user_cache_dir

APP_NAME = "OSCModules"
APP_AUTHOR = "DavidOSmith"

# Create a custom logger for having output events separate from log
MAIN_LOGGER_DIR = user_log_dir(APP_NAME, APP_AUTHOR)
ALT_LOGGER_DIR = user_cache_dir(APP_NAME, APP_AUTHOR)
# Output RAW data from pygame controller
RAW_LOGGER_NAME = "raw_output"
RAW_LOGGER_LEVEL = 25
RAW_LOGGER_DIR = ALT_LOGGER_DIR
RAW_LOGGER_MAXBYTES = 1000000
# Output OSC Messages to check for issues
OSC_LOGGER_NAME = "osc_output"
OSC_LOGGER_LEVEL = 26
OSC_LOGGER_DIR = ALT_LOGGER_DIR
OSC_LOGGER_MAXBYTES = 1000000
# Helper logger, for logging ay other info to user_cache_dir
HELPER_LOGGER_NAME = "helper_output"
HELPER_LOGGER_LEVEL = 27
HELPER_LOGGER_DIR = ALT_LOGGER_DIR
HELPER_LOGGER_MAXBYTES = 1000000

def raw_logger():
    """
    from osc.logging_config import raw_logger will make this logging
    method available for use
    """
    return RAW_LOGGER_LEVEL

def osc_logger():
    """
    from osc.logging_config import osc_logger will make this logging
    method available for use
    """
    return OSC_LOGGER_LEVEL

def helper_logger():
    """
    from osc.logging_config import helper_logger.
    Use this logger to record any other data for testing or other purposes
    """
    return HELPER_LOGGER_LEVEL

# Setup logging if not already started
def setup_logging():
    """
    Get the loggers set up for the project outputs.
    Outputs standard logs to user log folder.
    Additionally outputs certain raw data to user cache dir
    for analyzing output data
    """
    # Check if a logging instance has already been created
    if not logging.getLogger().handlers:
        default_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        console_formatter = logging.Formatter(
            '%(name)-12s: %(levelname)-8s %(message)s')

        # Configure main logger info:
        log_dir = MAIN_LOGGER_DIR
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "oscmodules.log")
        # Use a date based handler with file cleanup
        main_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        main_handler.setFormatter(default_formatter)
        # Filter out any of the non-default logger types
        main_handler.addFilter(lambda record: (record.levelno % 10) == 0)

        # Configure raw logger
        logging.addLevelName(RAW_LOGGER_LEVEL, RAW_LOGGER_NAME)
        raw_dir = RAW_LOGGER_DIR
        os.makedirs(raw_dir, exist_ok=True)
        raw_file = os.path.join(raw_dir, "joystick_raw.log")
        # Use a RotatingFileHandler to limit space used. The stream could be fast
        raw_handler = RotatingFileHandler(
            filename=raw_file,
            maxBytes=RAW_LOGGER_MAXBYTES,
            backupCount=1,
            encoding='utf-8'
        )
        raw_handler.setFormatter(default_formatter)
        raw_handler.addFilter(lambda record: record.levelno == RAW_LOGGER_LEVEL)

        # Configure OSC output logger
        logging.addLevelName(OSC_LOGGER_LEVEL, OSC_LOGGER_NAME)
        osc_dir = OSC_LOGGER_DIR
        os.makedirs(osc_dir,exist_ok=True)
        osc_file = os.path.join(osc_dir, "osc_output.log")
        osc_handler = RotatingFileHandler(
            filename=osc_file,
            maxBytes=OSC_LOGGER_MAXBYTES,
            backupCount=1,
            encoding='utf-8'
        )
        osc_handler.setFormatter(default_formatter)
        osc_handler.addFilter(lambda record: record.levelno == OSC_LOGGER_LEVEL)

        # Configure Helper output logger
        logging.addLevelName(HELPER_LOGGER_LEVEL, HELPER_LOGGER_NAME)
        helper_dir = HELPER_LOGGER_DIR
        os.makedirs(helper_dir, exist_ok=True)
        helper_file = os.path.join(helper_dir, "helper_output.log")
        helper_handler = RotatingFileHandler(
            filename=helper_file,
            maxBytes=HELPER_LOGGER_MAXBYTES,
            backupCount=1,
            encoding='utf-8'
        )
        helper_handler.setFormatter(default_formatter)
        helper_handler.addFilter(lambda record: record.levelno == HELPER_LOGGER_LEVEL)

        # Configure the handler that outputs the log messages to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(lambda record: (record.levelno % 10) == 0)

        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(main_handler)
        root_logger.addHandler(raw_handler)
        root_logger.addHandler(osc_handler)
        root_logger.addHandler(helper_handler)
        root_logger.addHandler(console_handler)
