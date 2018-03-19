#!/usr/bin/env python
import unittest

class TestParser(unittest.TestCase):
    def test_ab(self):
        a = 1
        b = 1
        self.assertEqual(a, b, "a should equal b")
        
if __name__ == "__main__":
    unittest.main()