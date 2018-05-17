# Standard dependencies
import socket
import time

# Extra dependencies
from pkg_resources import require
require('cothread==2.13')
import cothread

# Other files in this module
import CommandTemplates, RecordInterface

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
        self.setup_commands = ""
        self.start_commands = ""
        self.stop_commands = ""
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

    def add(self, command, command_type="setup"):
        """Append a line to store of commands"""
        if command_type == "setup":
            self.setup_commands += command
        elif command_type == "start":
            self.start_commands += command
        elif command_type == "stop":
            self.stop_commands += command

    def start_scan(self, value):
        """Sets up and starts a scan"""
        self.records["scan_talking"].set(1)
        self.prepare_setup_commands()
        self.prepare_start_commands()

        self.send_setup_commands()
        cothread.Sleep(1)
        self.send_start_commands()
        self.records["scan_talking"].set(0)


    def prepare_setup_commands(self):
        """Prepares the setup commands with the current scan parameters"""

        # Start creating a row...
        # Add x steps forwards
        for i in xrange(self.params["NX"]):
            if i == 0:
                first = "X"
            else:
                first = "&"
            self.add(self.templates["x_step"].x_step.format(xDemand=self.params["DX"] * i, first=first, **self.params))

        # Add y step
        y_wait_time = self.params["NX"] * (self.params["MOVETIME"] + self.params["EXPOSURE"])
        y_move_time = self.params["MOVETIME"]
        y0 = 0
        y1 = y0 + self.params["DY"]
        x_demand = (self.params["NX"] - 1) * self.params["DX"]
        self.add(self.templates["y_step"].format(y0=y0, y1=y1, first="X",
                                                 yWaitTime=y_wait_time,
                                                 yMOVETIME=y_move_time,
                                                 xDemand=x_demand,
                                                 **self.params))

        # Add x steps backwards
        for i in xrange(self.params["NX"]):
            first = "&"
            x_demand = self.params["DX"]*(self.params["NX"] - 1 - i)
            self.add(self.templates["x_step"].format(xDemand=x_demand, first=first, **self.params))

        # Add y step
        y_wait_time = self.params["NX"] * (self.params["MOVETIME"] + self.params["EXPOSURE"])
        y_move_time = self.params["MOVETIME"]
        y0 = self.params["DY"]
        y1 = y0 + self.params["DY"]
        x_demand = 0 * self.params["DX"]
        self.add(self.templates["y_step"].format(y0=y0, y1=y1, first="&",
                                                                 yWaitTime=y_wait_time,
                                                                 yMOVETIME=y_move_time,
                                                                 xDemand = x_demand,
                                                                 **self.params))

        # Format everything
        self.add(self.templates["rest"].format(**self.params))

    def prepare_start_commands(self):
        """Prepare the commands that will start the scan"""

        self.add("""WGO 1 257 2 257""", command_type="start")

    def prepare_stop_commands(self):
        """Prepare the commands that will stop the scan"""

        self.add(self.templates["stop_commands"], command_type="stop")

    def send_setup_commands(self):
        """Send down the setup commands"""

        print "Sending setup commands"
        start = time.time()
        status = self.send_multiline(setup_commands_step_scan)
        end = time.time()
        print "elapsed time: %f s" % (end - start)

        return status

    def send_start_commands(self):
        """Send down the start commands
        This will actually triggers the start of the scan"""

        print "Sending start commands"
        start = time.time()
        self.send_multiline(start_commands)
        end = time.time()
        print "elapsed time: %f s" % (end - start)
        self.records["scan_talking"].set(0)

    def abort_scan(self, value=None):
        """Wrapper to be used as callback for abort record"""
        self.send_stop_commands()

    def send_stop_commands(self):

        print "Sending stop commands"
        start = time.time()
        self.send_multiline(self.stop_commands)
        end = time.time()
        print "elapsed time: %f s" % (end - start)
