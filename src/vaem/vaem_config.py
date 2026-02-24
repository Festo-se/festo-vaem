"""
Holds all the different VAEM configurations for the different backends.

These are the supported client interface configurations for the VAEM valve control module

Typical usage examples:
    vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)

    vaem = VAEM(config=vaem_config)
"""

from dataclasses import dataclass


@dataclass(kw_only=True)
class VAEMConfig:
    """
    Generic VAEM config dataclass for initialization.

    Attributes:
        interface (str): Interface to connect to VAEM. Ex: 'tcp/ip', 'serial'
        unit_id (int): Modbus Unit ID of the VAEM (default: 1)
    """

    interface: str
    unit_id: int = 1


@dataclass(kw_only=True)
class VAEMTCPConfig(VAEMConfig):
    """
    Datclass for VAEM TCP/IP connection.

    Attributes:
        ip (str): IP address of the VAEM
        port (int): Port number of the VAEM (default: 502)

    Typical usage example:
        vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)

        vaem = VAEM(config=vaem_config)
    """

    ip: str
    port: int = 502


@dataclass(kw_only=True)
class VAEMSerialConfig(VAEMConfig):
    """
    Dataclass for VAEM Serial connection.

    Attributes:
        com_port (str): COM port to connect to VAEM
        baudrate (int): Baudrate for the serial connection (default: 9600). Ex: 9600, 19200, 38400, 57600, 115200

    Typical usage example:
        vaem_serial_config = VAEMSerialConfig(interface = "serial", com_port = "COM3", baudrate = 9600)

        vaem = VAEM(vaem_serial_config)
    """

    com_port: str
    baudrate: int
