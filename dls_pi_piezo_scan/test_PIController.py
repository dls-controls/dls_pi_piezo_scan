#!/bin/env dls-python
import PIController

from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')

from softioc import softioc, builder

import unittest
import random

class PIControllerTests(unittest.TestCase):
    def setUp(self):
        builder.SetDeviceName("BL13J-MO-PI-01:SCAN")
        self.controller = PIController.PIController(host="127.0.0.1", port=50000, debug=True)

        random.seed()

    def test_params(self):
        """Set some scan parameters via records\
        and check that we see the right values"""
        # Set up the parameters
        data = {   "NX": random.randint(0,100),
                   "NY": random.randint(0,100),
                   "DX": float(random.randint(0,100) / 10),
                   "DY": float(random.randint(0,100) / 10),
                   "X0": float(random.randint(0,3000) / 100),
                   "Y0": float(random.randint(0,3000) / 100),
                   "Z0": float(random.randint(0,3000) / 100)}

        for key, value in data.iteritems():
            self.controller.records[key].set(value)

        # Get the parameters from the records
        self.controller.get_scan_parameters()

        # Check them
        for key, value in data.iteritems():
            self.assertEqual(self.controller.scan_parameters[key], value)


    def tearDown(self):
        self.controller = None

if __name__ == "__main__":
    unittest.main()