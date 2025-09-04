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
from platformdirs import user_log_dir

APP_NAME = "OSCModules"
APP_AUTHOR = "DavidOSmith"

# Setup logging if not already started
def setup_logging():
    log_dir = user_log_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "oscmodules.log")

    # Check if a logging instance has already been created
    if not logging.getLogger().handlers:
        timed_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        logging.basicConfig(
            level=logging.INFO,
            format="{%(asctime)s %(levelname)s %(name)s: %(message)s}",
            handlers=[
                timed_handler,
                logging.StreamHandler()
            ]
        )
        # logging.info(f"Logging to: {log_file}")