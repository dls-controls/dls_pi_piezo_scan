#!/usr/bin/env python
import unittest

import dls_pi_piezo_scan

class TestParser(unittest.TestCase):
    def test_true(self):
        cond = dls_pi_piezo_scan.return_true()
        self.assertEqual(cond, True, "should return true")
        
if __name__ == "__main__":
    unittest.main()