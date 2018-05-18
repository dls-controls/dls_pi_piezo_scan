import os
import sys
import logging



import PIController
import PIStepScan

from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')

from softioc import softioc, builder

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
    pi_controller = PIController.PIController("172.23.82.249", 50000, debug=True)

    # Step scan logic and records
    pi_step_scan = PIStepScan.PIStepScan(pi_controller)

    # Start IOC
    builder.LoadDatabase()
    softioc.iocInit()

    softioc.interactive_ioc(globals())
    sys.exit()
