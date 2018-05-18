# Standard dependencies
import socket

class PIController():
    """Handles connection to the controller and sending/receiving commands"""

    def __init__(self, host, port=50000, debug=False):
        """:param host IP address of controller (or terninal server
        :param port IP port of controller or terminal server
        :param debug If True, doesn't connect but prints commands"""

        # Debug flag causes us to not actually connect
        # and print out commands instead
        self.debug = debug

        # Set up connection to controller
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1.0) # seconds
        self.connect()

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
