import os
import sys
import logging

from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')
require("numpy")

from softioc import softioc, builder

import PIController
import PIStepScan

if __name__ == '__main__':
    # Prepare params for IOC
    builder.SetDeviceName("BL13J-MO-PI-01:SCAN")
    builder.stringIn('WHOAMI', VAL='PI scan controller')
    builder.stringIn('HOSTNAME', VAL=os.uname()[1])

    logging.basicConfig(level=logging.DEBUG)

    # Connect to PI controller
    # Terminal server
    # pi_controller = PIController("172.23.82.5", 4011)
    # Ethernet
    #pi_controller = PIController.PIController("172.23.82.249", 50000, debug=False)
    pi_controller = PIController.PIController("Fake address 01", 50000,
                                              debug=True)

    # Step scan logic and records
    pi_step_scan = PIStepScan.PIStepScan(pi_controller)
    # Create our records
    pi_step_scan.create_records()

    # Start IOC
    builder.LoadDatabase()
    softioc.iocInit()

    softioc.interactive_ioc(globals())
    sys.exit()
