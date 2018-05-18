from pkg_resources import require
require('epicsdbbuilder==1.0')
from softioc import builder

def create_records(start_scan_function, min_x, min_y, min_z, max_x, max_y, max_z):
    """Create the records for the scan interface"""

    # We'll return them in a dict
    records = {}

    # Start the scan
    records["start_scan"] = builder.mbbOut('START',
                                       initial_value=0,
                                       PINI='NO',
                                       NOBT=2,
                                       ZRVL=0, ZRST='Stop',
                                       ONVL=1, ONST='Go',
                                       on_update=start_scan_function,
                                       always_update=True)

    # Status to say we're sending commands
    records["STATE"] = builder.mbbIn("STATE",
                                            initial_value=0,
                                            PINI='YES',
                                            NOBT=2,
                                            ZRVL=0, ZRST='Not configured', ZRSV="INVALID",
                                            ONVL=1, ONST='Preparing', ONSV="MINOR",
                                            TWVL=2, TWST='Error', TWSV="MAJOR",
                                            THVL=3, THST='Ready', THSV="NO_ALARM",
                                            )
    # Number of steps in x
    records["NX"] = builder.longOut("NX",
                                             initial_value=30,
                                             PINI='YES',
                                             LOPR=1, HOPR=1000000)
    # Number of steps in y
    records["NY"] = builder.longOut("NY",
                                             initial_value=30,
                                             PINI='YES',
                                             DRVL=1, DRVH=1000000)
    # Number of steps in z
    records["NZ"] = builder.longOut("NZ",
                                             initial_value=30,
                                             PINI='YES',
                                             DRVL=1, DRVH=1000000)
    # x step size / um
    records["DX"] = builder.aOut("DX",
                                        initial_value=0.1,
                                        PINI='YES',
                                        DRVL=0.001, DRVH=300.0,
                                      EGU="um", PREC=3)
    # y step size / um
    records["DY"] = builder.aOut("DY",
                                        initial_value=0.1,
                                        PINI='YES',
                                        DRVL=0.001, DRVH=300.0,
                                      EGU="um", PREC=3)

    # z step size / um
    records["DZ"] = builder.aOut("DZ",
                                 initial_value=0.1,
                                 PINI='YES',
                                 DRVL=0.001, DRVH=300.0,
                                 EGU="um", PREC=3)

    # x centre position / um
    records["X0"] = builder.aOut("X0",
                                      initial_value=150,
                                      PINI='YES',
                                      DRVL=min_x, DRVH=max_x,
                                      EGU="um", PREC=3)
    # y centre position / um
    records["Y0"] = builder.aOut("Y0",
                                      initial_value=150,
                                      PINI='YES',
                                      DRVL=min_y, DRVH=max_y,
                                      EGU="um", PREC=3)

    # z centre position / um
    records["Z0"] = builder.aOut("Z0",
                                      initial_value=150,
                                      PINI='YES',
                                      DRVL=min_z, DRVH=max_z,
                                      EGU="um", PREC=3)

    # EXPOSURE time / ms
    records["EXPOSURE"] = builder.aOut("EXPOSURE",
                                        initial_value=100,
                                        PINI='YES',
                                        DRVL=0.001, DRVH=300.0,
                                      EGU="ms", PREC=1)

    # Move time / ms
    records["MOVETIME"] = builder.aOut("MOVETIME",
                                            initial_value=40,
                                            PINI='YES',
                                            DRVL=0.001, DRVH=300.0,
                                            EGU="ms", PREC=1)

    return records