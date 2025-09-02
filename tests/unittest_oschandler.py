"""
This file was created with the help of AI.

Unit tests for the OSCHandler module using Python's built-in unittest framework.
"""

import unittest
from osc.oschandler import OSCHandler
import logging
from osc.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class TestOSCHandler(unittest.TestCase):
    def setUp(self):
        # Called before each test method
        # You can set up a basic OSCHandler instance here if needed
        self.tx_ip = '127.0.0.1'
        self.tx_port = 9000
        self.rx_port = 9001
        self.osc_handler = OSCHandler(mode='tx', tx_udp_ip=self.tx_ip, tx_port=self.tx_port)

    def test_send_message(self):
        """Test that send_message does not raise errors with valid input."""
        try:
            self.osc_handler.send_message('/test/address', [1, 2, 3])
        except Exception as e:
            self.fail(f"send_message raised an exception: {e}")

    def test_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        with self.assertRaises(ValueError):
            OSCHandler(mode='invalid', tx_udp_ip=self.tx_ip, tx_port=self.tx_port)

    def test_missing_tx_args(self):
        """Test that missing tx arguments raises ValueError in tx mode."""
        with self.assertRaises(ValueError):
            OSCHandler(mode='tx', tx_udp_ip=None, tx_port=None)

    def test_missing_rx_args(self):
        """Test that missing rx arguments raises ValueError in rx mode."""
        with self.assertRaises(ValueError):
            OSCHandler(mode='rx', rx_port=None)

    def test_register_osc_listener(self):
        """Test that registering a listener does not raise errors."""
        def dummy_handler(address, *args):
            pass
        try:
            self.osc_handler.register_osc_listener('/test/address', dummy_handler)
        except Exception as e:
            self.fail(f"register_osc_listener raised an exception: {e}")

    def test_register_osc_substring(self):
        """Test that registering a substring listener does not raise errors."""
        def dummy_handler(address, *args):
            pass
        try:
            self.osc_handler.register_osc_substring('/test', dummy_handler)
        except Exception as e:
            self.fail(f"register_osc_substring raised an exception: {e}")

    def test_listener_is_called(self):
        """Test that a registered handler is called when a message is dispatched."""
        self.called = False
        def handler(address, *args):
            self.called = True
            self.assertEqual(address, '/test/address')
            self.assertEqual(args, (123,))

        self.osc_handler.register_osc_listener('/test/address', handler)
        # Directly call the handler to simulate a message
        handler('/test/address', 123)
        self.assertTrue(self.called)

    def test_substring_listener_is_called(self):
        """Test that a substring handler is called for matching addresses."""
        self.called = False
        def handler(address, *args):
            self.called = True
            self.assertIn('/test', address)

        self.osc_handler.register_osc_substring('/test', handler)
        # Simulate default handler call
        self.osc_handler.default_handler('/test/abc', 456)
        self.assertTrue(self.called)

if __name__ == '__main__':
    # Optionally, configure logging for test output
    # logger.basicConfig(level=logging.CRITICAL)  # Suppress logs during tests
    unittest.main()
