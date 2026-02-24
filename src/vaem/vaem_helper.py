"""
Helper functions for VAEM driver.

For further reference, see the VAEM documentation found at the Product Page or Operation Instructions.
"""

from enum import IntEnum

vaemValveIndex = {
    1: 0x01,
    2: 0x02,
    3: 0x04,
    4: 0x08,
    5: 0x10,
    6: 0x20,
    7: 0x40,
    8: 0x80,
    "AllValves": 255,
}


class VaemAccess(IntEnum):
    """
    Enum class for the access type to the VAEM.

    Attributes:
        READ (0): Read access
        WRITE (1): Write access
    """

    READ = 0
    WRITE = 1


class VaemDataType(IntEnum):
    """
    Enum class for the data type being passed to and from the VAEM.

    Attributes:
        UINT8 (1): Unsigned 8-bit integer
        UINT16 (2): Unsigned 16-bit integer
        UINT32 (3): Unsigned 32-bit integer
        UINT64 (4): Unsigned 64-bit integer
    """

    UINT8 = 1
    UINT16 = 2
    UINT32 = 3
    UINT64 = 4


class VaemIndex(IntEnum):
    """
    Mapping of indices for the VAEM parameters.

    Attributes:
        CONTROLWORD (0x01): Control Word
        STATUSWORD (0x02): Status Word
        NOMINALVOLTAGE (0x04): Nominal Voltage
        INRUSHCURRENT (0x05): Inrush Current
        HOLDINGCURRENT (0x06): Holding Current
        SWITCHINGTIME (0x07): Switching Time
        PICKUPTIME (0x08): Pick Up Time
        OPERATINGMODE (0x09): Operating Mode
        SAVEPARAMETERS (0x11): Save Parameters
        SELECTVALVE (0x13): Select Valve
        TIMEDELAY (0x16): Time Delay
        ERRORHANDLING (0x2D): Activate or Deactivate Error Handling
        CURRENTREDUCTIONTIME (0x2E): Current Reduction Time
    """

    CONTROLWORD = 0x01
    STATUSWORD = 0x02
    NOMINALVOLTAGE = 0x04
    INRUSHCURRENT = 0x05
    HOLDINGCURRENT = 0x06
    SWITCHINGTIME = 0x07
    PICKUPTIME = 0x08
    OPERATINGMODE = 0x09
    SAVEPARAMETERS = 0x11
    SELECTVALVE = 0x13
    TIMEDELAY = 0x16
    ERRORHANDLING = 0x2D
    CURRENTREDUCTIONTIME = 0x2E


class VaemControlWords(IntEnum):
    """
    Enum class for the VAEM control words.

    Attributes:
        STARTVALVES (0x01): Start Valves
        STOPVALVES (0x04): Stop Valves
        RESETERRORS (0x08): Reset Errors
        STARTVALVESRESETERROR (0x09): Start valves and reset error bit after completion
    """

    STARTVALVES = 0x01
    STOPVALVES = 0x04
    RESETERRORS = 0x08
    STARTVALVESRESETERROR = STARTVALVES + RESETERRORS


class VaemOperatingMode(IntEnum):
    """
    Enum class for the VAEM operating modes.

    Attributes:
        OPMODE1 (0x00): Operating Mode 1 -- Internal via control word via communication interface
        OPMODE2 (0x01): Operating Mode 2 -- External by 24 V trigger input, set switching time of the individual valves
        OPMODE3 (0x02): Operating Mode 3 -- External by 24 V trigger input, duration of the trigger input
    """

    OPMODE1 = 0x00
    OPMODE2 = 0x01
    OPMODE3 = 0x02
