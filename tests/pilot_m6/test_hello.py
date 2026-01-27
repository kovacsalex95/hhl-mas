#!/usr/bin/env python3
"""
M6 Pilot Test - Hello World
Phase 2: Unit tests
"""

import unittest
from hello import hello


class TestHello(unittest.TestCase):
    """Tests for hello.py"""

    def test_hello_returns_greeting(self):
        """Test that hello() returns the expected greeting."""
        result = hello()
        self.assertEqual(result, "Hello, world!")

    def test_hello_returns_string(self):
        """Test that hello() returns a string type."""
        result = hello()
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
