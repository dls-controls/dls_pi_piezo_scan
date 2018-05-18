#!/bin/env dls-python
import PIController
import PIStepScan

from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')

from softioc import softioc, builder

import unittest
import random





class PIControllerTest(unittest.TestCase):
    """A"""

    def setUp(self):
        print self.__doc__
        builder.SetDeviceName(self.__doc__.split(" ")[0])
        self.controller = PIController.PIController(host="127.0.0.1", port=50000, debug=True)
        self.scan = PIStepScan.PIStepScan(self.controller)

        random.seed()

    def tearDown(self):
        self.controller = None
        self.scan = None

class TestRecords(PIControllerTest):
    """TestRecords - test setting scan parameters via records"""

    def test_records(self):
        """Set some scan parameters via records\
        and check that we see the right values"""
        # Set up some random parameters
        data = {   "NX": random.randint(0,100),
                   "NY": random.randint(0,100),
                   "DX": float(random.randint(0,100) / 10),
                   "DY": float(random.randint(0,100) / 10),
                   "X0": float(random.randint(0,3000) / 100),
                   "Y0": float(random.randint(0,3000) / 100),
                   "Z0": float(random.randint(0,3000) / 100)}

        # Set these values in the records
        for key, value in data.iteritems():
            self.scan.records[key].set(value)

        # Get the parameters from the records
        self.scan.get_scan_parameters()

        # Check the values were set
        for key, value in data.iteritems():
            self.assertEqual(self.scan.params[key], value)

class TestTemplate(PIControllerTest):
    """TestTemplate - check we can call the load_command_template smethod"""

    def test_template(self):
        self.scan.load_command_templates()

class TestStopCommands(PIControllerTest):
    """TestStopCommands - make sure stop commands are made by constructor"""

    def test_stop_commands(self):
        # Stop commands > 0 length
        self.assertGreater(len(self.scan.stop_commands.get()), 0)

class TestAdd(PIControllerTest):
    """TestAdd - add commands to the internal store"""

    def test_add(self):
        self.assertEqual(self.scan.setup_commands.get(), "")
        self.scan.setup_commands.add("some command")
        self.assertEqual(self.scan.setup_commands.get(), "some command")
        self.scan.setup_commands.add("\nanother command")
        self.assertEqual(self.scan.setup_commands.get(), "some command\nanother command")
        self.scan.setup_commands.clear()
        self.assertEqual(self.scan.setup_commands.get(), "")

        self.assertEqual(self.scan.start_commands.get(), "")
        self.scan.start_commands.add("start command")
        self.assertEqual(self.scan.start_commands.get(), "start command")
        self.scan.start_commands.clear()
        self.assertEqual(self.scan.start_commands.get(), "")

class TestStartCommands(PIControllerTest):
    """TestStartCommands"""

    def test_start_commands(self):
        self.scan.prepare_start_commands()
        print self.scan.start_commands.get()

class TestSetupCommands(PIControllerTest):
    """TestSetupCommands"""

    def test_start_commands(self):
        self.scan.prepare_setup_commands()
        print self.scan.setup_commands.get()

if __name__ == "__main__":

    unittest.main()