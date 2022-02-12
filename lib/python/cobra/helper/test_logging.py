import unittest
from . import logging

class TestLogger(unittest.TestCase):

    def test_class(self):

        logger = logging.Logger(self)
        self.assertEqual(type(logger).__name__, 'Logger')

    def test_info(self):

        logger = logging.Logger(self)
        logger.info('InfoTest')
        self.assertTrue(logger.in_recent_logs('TestLogger', 'InfoTest'))

    def test_error(self):

        logger = logging.Logger(self)
        logger.error('InfoError')
        self.assertTrue(logger.in_recent_logs('TestLogger', 'InfoError'))

    def test_debug(self):

        logger = logging.Logger(self)
        logger.debug('InfoDebug')
        self.assertTrue(logger.in_recent_logs('TestLogger', 'InfoDebug'))