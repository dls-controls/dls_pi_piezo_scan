# Standard dependencies
import socket
import logging

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
            logging.info(
                "Connect to real controller at host = %s:%d" % (
                self.host, self.port))
        else:
            logging.info("Controller created in debug mode, pretent to CONNECT host = %s:%d" %(self.host, self.port))

    def send(self, command):
        """Send a string to the controller"""
        if not self.debug:
            self.socket.send(command)
            logging.debug("SEND %s" % command)
        else:
            logging.info("SEND %s" % command)

    def send_multiline(self, multiline_input):
        """Send a multiline string of commands line by line"""
        for line in multiline_input.split("\n"):
            line_stripped = line.strip()
            if len(line_stripped) > 0:
                logging.debug("Send " + line_stripped)
                self.send(line_stripped + "\n")
            else:
                logging.warning("Skipped sending empty command line")

        # Check if any previous lines caused errors
        self.send("ERR?\n")
        if int(self.get_response()) != 0:
            logging.error("send_multiline: Stopping on controller error")
            return False

        return True

    def get_response(self):
        """Receive a line from controller"""
        if not self.debug:
            data = ""
            while "\n" not in data:
                try:
                    data = data + self.socket.recv(1024)
                except:
                    logging.warning("Timeout on receive from socket")
            logging.info("RECEIVE: " + data)
        else:
            logging.info("Receive in debug mode")
            # The zero makes ERR? command happy
            data = "0"

        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Make sure we close the socket on destruction"""
        self.socket.close()
