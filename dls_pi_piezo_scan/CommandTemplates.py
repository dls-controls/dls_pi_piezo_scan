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
    # etc.

    set_wave_table_rate = """WTR 0 20 1
"""
    set_record_table_rate = """RTR 40
"""
    connect_wave_table_to_generator = """WSL 1 1
WSL 2 2
WSL 3 3
"""
    set_wave_generator_cycles = """WGC 1 {Y_CYCLES:d}
"""
    clear_triggers = """TWC
"""
    configure_data_recorder = """DRC 1 1 2
DRC 2 2 2
DRC 3 3 2
DRC 4 1 1
DRC 5 2 1
DRC 6 3 1
"""
    set_wave_generator_offset = """WOS 1 {X0:f}
WOS 2 {Y0:f}
"""
    move_to_start_position = """MOV 1 {X0:f}
MOV 2 {Y0:f}
MOV 3 {Z0:f}"""

    templates["rest"] = set_wave_table_rate \
            + set_record_table_rate \
            + connect_wave_table_to_generator \
            + set_wave_generator_cycles \
            + clear_triggers \
            + configure_data_recorder \
            + set_wave_generator_offset \
            + move_to_start_position

    templates["stop_commands"] = """WGO 1 0 2 0
STP"""

    return templates
