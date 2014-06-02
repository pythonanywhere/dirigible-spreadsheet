# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
import sys
import time

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.utils.interruptable_thread import InterruptableThread

class TestInterruptableThread(unittest.TestCase):

    def test_interruptable_thread_is(self):
        def sleep_lots():
            # Setting stderr to None keeps test output from
            # having random stack traces inserted
            sys.stderr = None
            start = time.clock()
            while time.clock() - start < 10:
                pass
            self.fail('thread not interrupted')

        it = InterruptableThread(target=sleep_lots)
        it.start()
        it.join(5)
        self.assertTrue(it.isAlive())
        it.interrupt()
        time.sleep(1)
        self.assertFalse(it.isAlive())
