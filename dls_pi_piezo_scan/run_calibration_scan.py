#!//dls_sw/prod/R3.14.12.3/support/pythonSoftIoc/2-11/pythonIoc
from pkg_resources import require
require('cothread==2.13')
#require('epicsdbbuilder==1.0')
require("numpy")

import argparse
import logging

import PIStepScan
import PIController
from PIConstants import *


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run a calibration routine for PI E727 controller analogue output. "
                                     "Will set up a waveform to step one axis over a specified range, "
                                     "issuing triggers at each step that are used to trigger an external "
                                     "measurement device (assume a Zebra) to measure the output signal "
                                     "(at the moment you have to configure your measurement device separately, this script "
                                     "doesn't do that).")

    parser.add_argument("--address", type=str, help="IP address of controller")
    parser.add_argument("--port", type=int, help="IP port number of controller", default=50000)
    parser.add_argument("--axis", type=int, choices=[1, 2, 3], help="Axis number to scan", required=True)
    parser.add_argument("--start", type=float, help="Start position (EGU)", required=True)
    parser.add_argument("--end", type=float, help="End position (EGU)", required=True)
    parser.add_argument("-s", "--number_of_steps", type=int, help="Number of steps to make", required=True)
    parser.add_argument("-m", "--move_time", type=int, help="Time for each move, per step (ms)")
    parser.add_argument("-t", "--time_in_position", type=int, help="Time to wait in position at each step (ms)", required=True)
    parser.add_argument("-n", "--n_repeats", type=int, default=1, help="Repeat the scan n times")
    parser.add_argument("-d", "--dryrun", action="store_true", help="Print commands instead of sending them")


    return parser.parse_args()

def create_params(args):
    # Create parameter objects to push into the PIStepScan class
    param_dict = {"STATE": STATE_NOT_CONFIGRED,
                  "NX": args.number_of_steps,
                  "NY": 1,
                  "NZ": 1,
                  "DX": (args.end - args.start) / float(args.number_of_steps),
                  "DY": 1,
                  "DZ": 1,
                  "X0": args.start,
                  "Y0": 50,
                  "Z0": 50,
                  "MOVETIME": args.move_time,
                  "EXPOSURE": args.time_in_position,
                  "axis_to_scan": args.axis
    }

    return param_dict

def main():
    args = parse_arguments()

    logging.basicConfig(level=logging.DEBUG)

    # Create controller object
    pi_controller = PIController.PIController(args.address, args.port,
                                              debug=args.dryrun)

    step_scan = PIStepScan.PICalibrationScan(pi_controller)
    step_scan.insert_params(create_params(args))
    step_scan.get_scan_parameters()

    step_scan.configure_scan()

    step_scan.start_scan()


if __name__ == "__main__":
    main()