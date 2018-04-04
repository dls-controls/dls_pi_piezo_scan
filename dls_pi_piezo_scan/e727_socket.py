import socket
import time

class PIController():
    def __init__(self, host, port=50000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1.0) # seconds
        self.connect()

    def connect(self):
        """Connect socket to controller"""
        self.socket.connect((self.host, self.port))

    def send(self, command):
        """Send a string to the controller"""
        self.socket.send(command)

    def send_multiline(self, multiline_input):
        for line in multiline_input.split("\n"):
            print "Send " + line
            self.send(line + "\n")
            self.send("ERR?\n")
            if int(self.print_response()) != 0:
                print "Stopping on controller error"
                break

    def print_response(self):
        """Receive a line and print it"""
        data = ""
        while "\n" not in data:
            data = data + self.socket.recv(1024)
        print data
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Make sure we close the socket on destruction"""
        self.socket.close()

# Terminal server
#pi_controller = PIController("172.23.82.5", 4011)
# Ethernet
pi_controller = PIController("172.23.82.249", 50000)

setup_commands = """SVO 1 1
SVO 2 1
SVO 3 1
WAV 1 X LIN 2000 99.000000 0.500000 2000 0 0
WAV 1 & LIN 200 -99.000000 99.500000 180 0 0
WAV 2 X LIN 2000 0 0 2000 0 0
WAV 2 & LIN 200 1.000000 0 180 0 0
WTR 0 99 1
RTR 99
WSL 1 1
WSL 2 2
WGC 1 2
TWC
CTO 1 3 4
TWS 1    1 1 1   21 1 1   41 1 1   61 1 1   81 1 1  102 1 1  122 1 1  142 1 1  162 1 1  182 1
TWS 1  203 1 1  223 1 1  243 1 1  263 1 1  283 1 1  304 1 1  324 1 1  344 1 1  364 1 1  384 1
TWS 1  405 1 1  425 1 1  445 1 1  465 1 1  485 1 1  506 1 1  526 1 1  546 1 1  566 1 1  586 1
TWS 1  607 1 1  627 1 1  647 1 1  667 1 1  687 1 1  708 1 1  728 1 1  748 1 1  768 1 1  788 1
TWS 1  809 1 1  829 1 1  849 1 1  869 1 1  889 1 1  910 1 1  930 1 1  950 1 1  970 1 1  990 1
TWS 1 1011 1 1 1031 1 1 1051 1 1 1071 1 1 1091 1 1 1112 1 1 1132 1 1 1152 1 1 1172 1 1 1192 1
TWS 1 1213 1 1 1233 1 1 1253 1 1 1273 1 1 1293 1 1 1314 1 1 1334 1 1 1354 1 1 1374 1 1 1394 1
TWS 1 1415 1 1 1435 1 1 1455 1 1 1475 1 1 1495 1 1 1516 1 1 1536 1 1 1556 1 1 1576 1 1 1596 1
TWS 1 1617 1 1 1637 1 1 1657 1 1 1677 1 1 1697 1 1 1718 1 1 1738 1 1 1758 1 1 1778 1 1 1798 1
TWS 1 1819 1 1 1839 1 1 1859 1 1 1879 1 1 1899 1 1 1920 1 1 1940 1 1 1960 1 1 1980 1
DRC 1 1 2
DRC 2 2 2
DRC 3 3 2
DRC 4 1 1
DRC 5 2 1
DRC 6 3 1"""

start_commands = """WOS 2 0
MOV 1 0
MOV 2 0
MOV 3 0
WGO 1 1 2 257"""

stop_commands = """WGO 1 0 2 0
STP"""

print "Sending setup commands"
start = time.time()
pi_controller.send_multiline(setup_commands)
end = time.time()
print "elapsed time: %f s" % (end - start)
raw_input("Press return to start scan")

print "Sending start commands"
start = time.time()
pi_controller.send_multiline(start_commands)
end = time.time()
print "elapsed time: %f s" % (end - start)
raw_input("Press return to abort scan")

print "Sending stop commands"
start = time.time()
pi_controller.send_multiline(stop_commands)
end = time.time()
print "elapsed time: %f s" % (end - start)



