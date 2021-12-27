import unittest
from . import logging

class TestLogger(unittest.TestCase):

    def test_class(self):

        logger = logging.Logger(self)
        self.assertEqual(type(logger).__name__, 'Logger')