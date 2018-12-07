# Standard dependencies
import time
import logging

# Extra dependencies
from pkg_resources import require

# Other files in this module
import CommandTemplates
import RecordInterface
import CommandStore
import PIController
import CoordinateTransform

from PIConstants import *

# Common bits
min_x = 0.0
min_y = 0.0
min_z = 0.0

max_x = 300.0
max_y = 300.0
max_z = 300.0

class PIStepScan():
    def __init__(self, controller):
        """:param controller PIController object"""

        self.controller = controller #type: PIController.PIController

        # Prepare command templates
        self.setup_commands = CommandStore.CommandStore()
        self.start_commands = CommandStore.CommandStore()
        self.stop_commands = CommandStore.CommandStore()
        self.load_command_templates()

        # Prepare stop commands so they are always ready to go, since they never change
        self.prepare_stop_commands()

        # Create coordinate transformation object
        self.transform = CoordinateTransform.CoordinateTransform()

    def create_records(self):
        """Create records for EPICS interface"""

        self.records = RecordInterface.create_records(configure_scan_function=self.configure_scan,
                                                        start_scan_function=self.start_scan,
                                                      min_x=min_x, min_y=min_y, min_z=min_z,
                                                      max_x=max_x, max_y=max_y, max_z=max_z)

    def load_command_templates(self):
        """Makes the command templates accessible"""

        self.templates = CommandTemplates.get_command_templates()

    def get_scan_parameters(self):
        """Gather the parameters for the scan and populate a dict for use in
        building commands"""

        # Scan parameters
        # Number of cycles of the Y wave generator is
        # half of the number of Y rows in the scan
        Y_CYCLES = int(self.records["NY"].get() / 2)

        # Create a dictionary of the scan parameters
        # which we will use for string substitution in commands
        self.params = {"TABLEX": TABLEX,
                                "TABLEY": TABLEY,
                                "TABLEZ": TABLEZ,
                                "AXISX": AXISX,
                                "AXISY": AXISY,
                                "AXISZ": AXISZ,
                                "rows": Y_CYCLES}

        # Get all the values from our records
        for key, record in self.records.iteritems():
            self.params[key] = record.get()

    def verify_parameters(self):
        """Check validity of scan parameters"""
        x_range = self.params["DX"] * self.params["NX"]
        y_range = self.params["DY"] * self.params["NY"]
        z_range = self.params["DZ"] * self.params["NZ"]

        failure = []

        # Won't hit x limit
        if self.params["X0"] - (x_range / 2) <= min_x:
            failure.append("Will hit x negative limit")
        if self.params["X0"] + (x_range / 2) >= max_x:
            failure.append("Will hit x positive limit")

        # Won't hit y limit
        if self.params["Y0"] - (y_range / 2) <= min_y:
            failure.append("Will hit y negative limit")
        if self.params["Y0"] + (y_range / 2) >= max_y:
            failure.append("Will hit y positive limit")

        # Won't hit z limit
        if self.params["Z0"] - (z_range / 2) <= min_z:
            failure.append("Will hit z negative limit")
        if self.params["Z0"] + (z_range / 2) >= max_z:
            failure.append("Will hit z positive limit")

        # Number of wave points can fit in available memory
        total_points = self.calculate_required_data_points()
        points_percentage = float(total_points) / float(E727_AVAILALBE_DATAPOINTS) * 100.0

        if total_points > E727_AVAILALBE_DATAPOINTS:
            failure.append("Too many points in scan. "
                           "Requested %d but only %d availale on controller." % (
                total_points, E727_AVAILALBE_DATAPOINTS))
        else:
            logging.info("We will use %d of %d data points for wavetable (%.1f%%)" % (
            total_points, E727_AVAILALBE_DATAPOINTS, points_percentage))

        # Determine result
        if len(failure) > 0:
            logging.error("Parameter checks failed. Reasons: " + ";".join(failure))
            return False
        else:
            logging.info("Parameter checks passed")
            return True

    def calculate_required_data_points(self):
        # TODO: Not sure this is a perfect calculation yet
        # TODO: Only valid with 1ms per point (WTR = 20) as currently
        # TODO actually its definitely not because Y takes less than the others
        points_per_x_step = self.params["MOVETIME"] + self.params["EXPOSURE"]
        points_per_y_step = self.params["MOVETIME"] + self.params["EXPOSURE"]
        points_per_z_step = self.params["MOVETIME"] + self.params["EXPOSURE"]
        total_points = points_per_x_step * self.params["NX"] + \
                       points_per_y_step * self.params["NY"] + \
                       points_per_z_step * self.params["NZ"]
        return total_points

    def configure_scan(self, value = None):
        """Sets up a scan"""

        self.records["STATE"].set(STATE_PREPARING)
        self.get_scan_parameters()

        # Check parameters are valid
        if self.verify_parameters() == False:
            # Parameter checks failed
            self.records["STATE"].set(STATE_ERROR)
            return False

        if self.prepare_setup_commands() == False:
            self.records["STATE"].set(STATE_ERROR)
            return False

        if self.prepare_start_commands() == False:
            self.records["STATE"].set(STATE_ERROR)
            return False

        if self.send_setup_commands() == False:
            self.records["STATE"].set(STATE_ERROR)
            return False

        if True:
            # If we got to this point then configured scan OK.
            self.records["STATE"].set(STATE_READY)

    def start_scan(self, value = None):
        """starts a scan which has already been configured"""

        # Check scan has been configured
        if self.records["STATE"].get() != STATE_READY:
            # Parameter checks failed
            self.records["STATE"].set(STATE_ERROR)
            logging.error("Can't start scan - needs to be configured first")
            return False
        else:

            if self.send_start_commands() == False:
                self.records["STATE"].set(STATE_ERROR)
                logging.error("Error sending start commands.")
                return False

            # Started scan OK.
            self.records["STATE"].set(STATE_READY)


    def create_odd_rows(self):
        """Create an odd row: x steps forwards then y makes one step forwards"""

        # Add the x steps forwards
        for step in xrange(self.params["NX"]):
            if step == 0:
                # First step replaces wavetable contents
                action = ACTION_REPLACE
            else:
                # Subsequent steps are appended
                action = ACTION_APPEND

            self.setup_commands.add(self.templates["x_step"].format(
                xDemand=self.params["DX"] * step, first=action, **self.params))

        # Add the y step
        # Y waits while X is going forward
        # then moves one step of its own

        # How long y waits while x is moving
        y_wait_time = self.params["NX"] * (
                self.params["MOVETIME"] + self.params["EXPOSURE"])
        # Time for y to move one step
        y_move_time = self.params["MOVETIME"]
        # y position before step
        # is zero because we set generator to start where it left off
        y0 = 0
        # y postiion after step
        y1 = y0 + self.params["DY"]
        # X waits at the last position in the row
        x_demand = (self.params["NX"] - 1) * self.params["DX"]

        # Add the commands
        self.setup_commands.add(
            self.templates["y_step"].format(y0=y0, y1=y1, first=ACTION_REPLACE,
                                            yWaitTime=y_wait_time,
                                            yMOVETIME=y_move_time,
                                            xDemand=x_demand,
                                            **self.params))

    def create_even_rows(self):
        """Create an even-numbered row: x steps backwards then y makes one step forwards"""

        # Add the x steps backwards
        for step in xrange(self.params["NX"]):
            # Always append since even row is added after odd
            action = ACTION_APPEND
            x_demand = self.params["DX"] * (self.params["NX"] - 1 - step)
            self.setup_commands.add(
                self.templates["x_step"].format(xDemand=x_demand, first=action,
                                                **self.params))

        # Add the y step
        # Y waits while X is going forward
        # then moves one step of its own

        # How long Y waits for while X is moving
        y_wait_time = self.params["NX"] * (
        self.params["MOVETIME"] + self.params["EXPOSURE"])
        # Time for Y to complete 1 step
        y_move_time = self.params["MOVETIME"]
        # Y start position for step: from endpoint of previous step
        y0 = self.params["DY"]
        # Y end position for step
        y1 = y0 + self.params["DY"]
        # X waits at last position of row
        x_demand = 0 * self.params["DX"]

        # Add the commands
        self.setup_commands.add(
            self.templates["y_step"].format(y0=y0, y1=y1, first=ACTION_APPEND,
                                            yWaitTime=y_wait_time,
                                            yMOVETIME=y_move_time,
                                            xDemand=x_demand,
                                            **self.params))

    def prepare_setup_commands(self):
        """Prepares the setup commands with the current scan parameters"""

        # NOTE must have already got and checked parameters

        self.setup_commands.clear()

        # Create the odd and even rows
        self.create_odd_rows()
        self.create_even_rows()

        # Add remaining commands
        Y_CYCLES = self.params["NY"]/2
        self.setup_commands.add(self.templates["rest"].format(Y_CYCLES=Y_CYCLES, **self.params))
        return True

    def prepare_start_commands(self):
        """Prepare the commands that will start the scan"""

        self.start_commands.clear()
        self.start_commands.add("""WGO 1 257 2 257""")

    def prepare_stop_commands(self):
        """Prepare the commands that will stop the scan"""

        self.stop_commands.add(self.templates["stop_commands"])

    def send_setup_commands(self):
        """Send down the setup commands"""

        logging.info("Sending setup commands")

        start = time.time()
        status = self.controller.send_multiline(self.setup_commands.get())
        end = time.time()

        logging.info("Finished setup commands, took %f s" % (end - start))

        return status

    def send_start_commands(self):
        """Send down the start commands
        This will actually triggers the start of the scan"""

        logging.info("Sending start commands")

        start = time.time()
        self.controller.send_multiline(self.start_commands.get())
        end = time.time()

        logging.info("Finished start commands, took %f s" % (end - start))


    def abort_scan(self, value=None):
        """Wrapper to be used as callback for abort record"""
        self.controller.send_stop_commands()

    def send_stop_commands(self):
        """Send the stop commands to the controller"""

        logging.info("Sending stop commands")
        start = time.time()
        self.controller.send_multiline(self.stop_commands.get())
        end = time.time()
        logging.info("elapsed time: %f s" % (end - start))
