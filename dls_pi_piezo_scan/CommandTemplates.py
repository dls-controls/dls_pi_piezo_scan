def get_command_templates():
    """Give us the command templates - separated from the main class for clairity"""

    templates = {}

    # Turn on servos
    templates["servos"] = """SVO 1 1
            SVO 2 1
            SVO 3 1
    """
    # One X step
    templates["x_step"] = """WAV {TABLEX:d} {first:s} LIN {MOVETIME:d} 0 {xDemand:f} {MOVETIME:d} 0 0
            WAV {TABLEX:d} & LIN {EXPOSURE:d} 0 {xDemand:f} {EXPOSURE:d} 0 0
    """

    # One Y step
    templates["y_step"] = """WAV {TABLEY:d} {first:s} LIN {yWaitTime:d} 0 {y0:f} {yWaitTime:d} 0 0
            WAV {TABLEX:d} & LIN {yMOVETIME:d} 0 {xDemand:f} {yMOVETIME:d} 0 0
            WAV {TABLEY:d} & LIN {yMOVETIME:d} 0 {y1:f} {yMOVETIME:d} 0 0
    """

    # Set up data recording,
    # Move to start poisition
    templates["rest"] = """WTR 0 20 1
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

    templates["stop_commands"] = """WGO 1 0 2 0
        STP"""

    return templates
