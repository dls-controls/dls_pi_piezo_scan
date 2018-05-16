import socket
import time
from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')
import cothread

from softioc import softioc, builder

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
        self.records = {}
        self.create_records()

        # Prepare command templates
        self.setup_commands = ""
        self.start_commands = ""
        self.stop_commands = ""
        self.load_command_templates()

        # Prepare stop commands so they are always ready to go
        self.prepare_stop_commands()



    def create_records(self):
        # Start the scan
        self.records["start_scan"] = builder.mbbOut('START',
                                           initial_value=0,
                                           PINI='NO',
                                           NOBT=2,
                                           ZRVL=0, ZRST='Stop',
                                           ONVL=1, ONST='Go',
                                           on_update=self.start_scan,
                                           always_update=True)

        # Status to say we're sending commands
        self.records["scan_talking"] = builder.mbbIn("TALKING",
                                                initial_value=0,
                                                PINI='YES',
                                                NOBT=2,
                                                ZRVL=0, ZRST='Ready',
                                                ONVL=1, ONST='Talking',
                                                ZRSV="NO_ALARM", ONSV="MINOR"
                                                )
        # Number of steps in x
        self.records["NX"] = builder.longOut("NX",
                                                 initial_value=30,
                                                 PINI='YES',
                                                 LOPR=1, HOPR=1000000)
        # Number of steps in y
        self.records["NY"] = builder.longOut("NY",
                                                 initial_value=30,
                                                 PINI='YES',
                                                 DRVL=1, DRVH=1000000)
        # x step size / um
        self.records["DX"] = builder.aOut("DX",
                                            initial_value=0.1,
                                            PINI='YES',
                                            DRVL=0.001, DRVH=300.0,
                                          EGU="um", PREC=3)
        # y step size / um
        self.records["DY"] = builder.aOut("DY",
                                            initial_value=0.1,
                                            PINI='YES',
                                            DRVL=0.001, DRVH=300.0,
                                          EGU="um", PREC=3)

        # x centre position / um
        self.records["X0"] = builder.aOut("X0",
                                          initial_value=150,
                                          PINI='YES',
                                          DRVL=0.001, DRVH=300.0,
                                          EGU="um", PREC=3)
        # y centre position / um
        self.records["Y0"] = builder.aOut("Y0",
                                          initial_value=150,
                                          PINI='YES',
                                          DRVL=0.001, DRVH=300.0,
                                          EGU="um", PREC=3)

        # z centre position / um
        self.records["Z0"] = builder.aOut("Z0",
                                          initial_value=150,
                                          PINI='YES',
                                          DRVL=0.001, DRVH=300.0,
                                          EGU="um", PREC=3)

        # EXPOSURE time / ms
        self.records["EXPOSURE"] = builder.aOut("EXPOSURE",
                                            initial_value=100,
                                            PINI='YES',
                                            DRVL=0.001, DRVH=300.0,
                                          EGU="ms", PREC=1)

        # Move time / ms
        self.records["MOVETIME"] = builder.aOut("MOVETIME",
                                                initial_value=40,
                                                PINI='YES',
                                                DRVL=0.001, DRVH=300.0,
                                                EGU="ms", PREC=1)



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

        self.templates = {}

        # Turn on servos
        self.templates["servos"] = """SVO 1 1
                SVO 2 1
                SVO 3 1
        """
        # One X step
        self.templates["x_step"] = """WAV {TABLEX:d} {first:s} LIN {MOVETIME:d} 0 {xDemand:f} {MOVETIME:d} 0 0
                WAV {TABLEX:d} & LIN {EXPOSURE:d} 0 {xDemand:f} {EXPOSURE:d} 0 0
        """

        # One Y step
        self.templates["y_step"] = """WAV {TABLEY:d} {first:s} LIN {yWaitTime:d} 0 {y0:f} {yWaitTime:d} 0 0
                WAV {TABLEX:d} & LIN {yMOVETIME:d} 0 {xDemand:f} {yMOVETIME:d} 0 0
                WAV {TABLEY:d} & LIN {yMOVETIME:d} 0 {y1:f} {yMOVETIME:d} 0 0
        """

        # Set up data recording,
        # Move to start poisition
        self.templates["rest"] = """WTR 0 20 1
                RTR 40
                WSL 1 1
                WSL 2 2
                WGC 1 {Y_CYCLES:d}
                TWC
                DRC 1 1 2
                DRC 2 2 2
                DRC 3 3 2
                DRC 4 1 1
                DRC 5 2 1
                DRC 6 3 1
                WOS 1 0
                WOS 2 0
                MOV 1 10
                MOV 2 10
                MOV 3 10
                WOS 1 10
                WOS 2 10"""

        self.templates["stop_commands"] = """WGO 1 0 2 0
            STP"""

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
        self.records["scan_talking"].set(1)
        self.prepare_setup_commands()
        self.prepare_start_commands()

        self.send_setup_commands()
        cothread.Sleep(1)
        self.send_start_commands()
        self.records["scan_talking"].set(0)


    def prepare_setup_commands(self):

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
        # Start commands
        self.add("""WGO 1 257 2 257""", command_type="start")

    def prepare_stop_commands(self):
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
        """Send down the start commands which actually triggers the start of the scan"""

        print "Sending start commands"
        start = time.time()
        self.send_multiline(start_commands)
        end = time.time()
        print "elapsed time: %f s" % (end - start)
        self.records["scan_talking"].set(0)


def abort_scan(self,value):
    stop_commands = """WGO 1 0 2 0
            STP"""
    print "Sending stop commands"
    start = time.time()
    self.send_multiline(stop_commands)
    end = time.time()
    print "elapsed time: %f s" % (end - start)
