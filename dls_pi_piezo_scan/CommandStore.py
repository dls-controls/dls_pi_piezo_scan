class CommandStore:
    """Store a set of commands, add to it and clear it"""

    def __init__(self):
        self.commands = ""

    def add(self, command):
        self.commands += command

    def clear(self):
        self.commands = ""

    def get(self):
        return self.commands
