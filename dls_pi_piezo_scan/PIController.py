# Standard dependencies
import socket
import time

# Extra dependencies
from pkg_resources import require
require('cothread==2.13')
import cothread

# Other files in this module
import CommandTemplates, RecordInterface
import CommandStore

REPLACE = "X"
APPEND = "&"

class PIController():
    def __init__(self, host, port=50000, debug=False):
        # Debug flag causes us to not actually connect
        # and print out commands instead
        self.debug = debug

        # Set up connection to controller
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1.0) # seconds
        self.connect()

        # Create our records
        self.create_records()

        # Prepare command templates
        self.setup_commands = CommandStore.CommandStore()
        self.start_commands = CommandStore.CommandStore()
        self.stop_commands = CommandStore.CommandStore()
        self.load_command_templates()

        # Prepare stop commands so they are always ready to go, since they never change
        self.prepare_stop_commands()

    def create_records(self):

        # Common bits
        min_x = 0.0
        min_y = 0.0
        min_z = 0.0

        max_x = 300.0
        max_y = 300.0
        max_z = 300.0

        self.records = RecordInterface.create_records(self.start_scan,
                                                      min_x, min_y, min_z,
                                                      max_x, max_y, max_z)



    def connect(self):
        """Connect socket to controller"""
        if not self.debug:
            self.socket.connect((self.host, self.port))
        else:
            print "DEBUG CONNECT host = %s:%d" %(self.host, self.port)

    def send(self, command):
        """Send a string to the controller"""
        if not self.debug:
            self.socket.send(command)
        else:
            print "DEBUG SEND %s" % command

    def send_multiline(self, multiline_input):
        """Send a multiline string of commands line by line"""
        for line in multiline_input.split("\n"):
            print "Send " + line.strip()
            self.send(line.strip() + "\n")

        # Check if any previous lines caused errors
        self.send("ERR?\n")
        if int(self.print_response()) != 0:
            print "Stopping on controller error"
            return False

        return True

    def print_response(self):
        """Receive a line and print it"""
        if not self.debug:
            data = ""
            while "\n" not in data:
                data = data + self.socket.recv(1024)
            print data
        data = "0"
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Make sure we close the socket on destruction"""
        self.socket.close()

    def load_command_templates(self):
        """Makes the command templates accessible"""

        self.templates = CommandTemplates.get_command_templates()

    def get_scan_parameters(self):
        """Gather the parameters for the scan and populate a dict for use in
        building commands"""

        # Scan parameters

        # Which wave table for which axis
        TABLEX = 1
        TABLEY = 2
        TABLEZ = 3

        # Axis number assignments
        AXISX = 1
        AXISY = 2
        AXISZ = 3

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

        for key, record in self.records.iteritems():
            self.params[key] = record.get()

    def start_scan(self, value):
        """Sets up and starts a scan"""
        self.records["scan_talking"].set(1)
        self.prepare_setup_commands()
        self.prepare_start_commands()

        self.send_setup_commands()
        cothread.Sleep(1)
        self.send_start_commands()
        self.records["scan_talking"].set(0)


    def create_odd_rows(self):
        """Create an odd row: x steps forwards then y makes one step forwards"""

        # Add the x steps forwards
        for step in xrange(self.params["NX"]):
            if step == 0:
                # First step replaces wavetable contents
                action = REPLACE
            else:
                # Subsequent steps are appended
                action = APPEND

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
            self.templates["y_step"].format(y0=y0, y1=y1, first=REPLACE,
                                            yWaitTime=y_wait_time,
                                            yMOVETIME=y_move_time,
                                            xDemand=x_demand,
                                            **self.params))

    def create_even_rows(self):
        """Create an even-numbered row: x steps backwards then y makes one step forwards"""

        # Add the x steps backwards
        for step in xrange(self.params["NX"]):
            # Always append since even row is added after odd
            action = APPEND
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
            self.templates["y_step"].format(y0=y0, y1=y1, first=APPEND,
                                            yWaitTime=y_wait_time,
                                            yMOVETIME=y_move_time,
                                            xDemand=x_demand,
                                            **self.params))

    def prepare_setup_commands(self):
        """Prepares the setup commands with the current scan parameters"""

        self.get_scan_parameters()
        self.setup_commands.clear()

        # Create the odd and even rows
        self.create_odd_rows()
        self.create_even_rows()

        # Add remaining commands
        Y_CYCLES = self.params["NY"]/2
        self.setup_commands.add(self.templates["rest"].format(Y_CYCLES=Y_CYCLES, **self.params))

    def prepare_start_commands(self):
        """Prepare the commands that will start the scan"""

        self.start_commands.clear()
        self.start_commands.add("""WGO 1 257 2 257""")

    def prepare_stop_commands(self):
        """Prepare the commands that will stop the scan"""

        self.stop_commands.add(self.templates["stop_commands"])

    def send_setup_commands(self):
        """Send down the setup commands"""

        print "Sending setup commands"
        start = time.time()
        status = self.send_multiline(self.setup_commands.get())
        end = time.time()
        print "elapsed time: %f s" % (end - start)

        return status

    def send_start_commands(self):
        """Send down the start commands
        This will actually triggers the start of the scan"""

        print "Sending start commands"
        start = time.time()
        self.send_multiline(self.start_commands.get())
        end = time.time()
        print "elapsed time: %f s" % (end - start)
        self.records["scan_talking"].set(0)

    def abort_scan(self, value=None):
        """Wrapper to be used as callback for abort record"""
        self.send_stop_commands()

    def send_stop_commands(self):

        print "Sending stop commands"
        start = time.time()
        self.send_multiline(self.stop_commands.get())
        end = time.time()
        print "elapsed time: %f s" % (end - start)
