import socket
import time
from pkg_resources import require
require('cothread==2.13')
require('epicsdbbuilder==1.0')
import cothread

from softioc import softioc, builder

class PIController():
    def __init__(self, host, port=50000, debug=False):
        self.debug = debug

        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1.0) # seconds
        self.connect()

        self.records = {}
        self.create_records()

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
        # exposure time / ms
        self.records["EXPOSURE"] = builder.aOut("EXPOSURE",
                                            initial_value=100,
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


    def start_scan(self, value):

        # Scan parameters
        NX = self.records["NX"].get()
        DX = self.records["DX"].get()
        NY = self.records["NY"].get()
        DY = self.records["DY"].get()
        EXPOSURE = self.records["EXPOSURE"].get()
        MOVETIME = 40 # Magic number
        TABLEX = 1
        TABLEY = 2
        TABLEZ = 3
        AXISX = 1
        AXISY = 2
        AXISZ = 3
        common_dict = {"tableX": TABLEX,
                       "tableY": TABLEY,
                       "tableZ": TABLEZ,
                       "axisX": AXISX,
                       "axisY": AXISY,
                       "axisZ": AXISZ,
                       "exposure": EXPOSURE,
                       "moveTime": MOVETIME,
                       "rows": int(NY/2)}

        # Turn on servos
        setup_commands_step_scan = """SVO 1 1
        SVO 2 1
        SVO 3 1
"""
        # One X step
        setup_commands_x_step = """WAV {tableX:d} {first:s} LIN {moveTime:d} 0 {xDemand:f} {moveTime:d} 0 0
        WAV {tableX:d} & LIN {exposure:d} 0 {xDemand:f} {exposure:d} 0 0
"""

        # One Y step
        setup_commands_y_step = """WAV {tableY:d} {first:s} LIN {yWaitTime:d} 0 {y0:f} {yWaitTime:d} 0 0
        WAV {tableX:d} & LIN {yMoveTime:d} 0 {xDemand:f} {yMoveTime:d} 0 0
        WAV {tableY:d} & LIN {yMoveTime:d} 0 {y1:f} {yMoveTime:d} 0 0
"""

        # Start creating a row...
        # Add x steps forwards
        for i in xrange(NX):
            if i == 0:
                first = "X"
            else:
                first = "&"
            setup_commands_step_scan += setup_commands_x_step.format(xDemand=DX*i, first=first, **common_dict)

        # Add y step
        y_wait_time = NX * (MOVETIME + EXPOSURE)
        y_move_time = MOVETIME
        y0 = 0
        y1 = y0 + DY
        setup_commands_step_scan += setup_commands_y_step.format(y0=y0, y1=y1, first="X",
                                                                 yWaitTime=y_wait_time,
                                                                 yMoveTime=y_move_time,
                                                                 xDemand=(NX-1) * DX,
                                                                 **common_dict)

        # Add x steps backwards
        for i in xrange(NX):
            first = "&"
            setup_commands_step_scan += setup_commands_x_step.format(xDemand=DX*(NX - 1 - i), first=first, **common_dict)

        # Add y step
        y_wait_time = NX * (MOVETIME + EXPOSURE)
        y_move_time = MOVETIME
        y0 = DY
        y1 = y0 + DY
        setup_commands_step_scan += setup_commands_y_step.format(y0=y0, y1=y1, first="&",
                                                                 yWaitTime=y_wait_time,
                                                                 yMoveTime=y_move_time,
                                                                 xDemand = 0 * DX,
                                                                 **common_dict)




        # Set up data recording,
        # Move to start poisition
        setup_commands_rest = """WTR 0 20 1
        RTR 40
        WSL 1 1
        WSL 2 2
        WGC 1 {rows:d}
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

        # Format everything
        setup_commands_step_scan += setup_commands_rest
        setup_commands_step_scan = setup_commands_step_scan.format(**common_dict)

        start_commands = """WGO 1 257 2 257"""

        self.records["scan_talking"].set(1)
        print "Sending setup commands"
        start = time.time()
        status = self.send_multiline(setup_commands_step_scan)
        end = time.time()
        print "elapsed time: %f s" % (end - start)

        if (status == False):
            # Bail
            return

        cothread.Sleep(1)

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