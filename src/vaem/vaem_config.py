"""
Holds all the different VAEM configurations for the different backends.

These are the supported client interface configurations for the VAEM valve control module

Typical usage examples:
    # Factory usage — dispatches to the correct subclass automatically
    vaem_config = VAEMConfig(interface="tcp/ip", ip=ip, port=502)

    # Explicit subclass usage — equivalent to the factory call above
    vaem_config = VAEMTCPConfig(ip=ip, port=502)

    vaem = VAEM(config=vaem_config)
"""

from dataclasses import dataclass


@dataclass(kw_only=True)
class VAEMConfig:
    """
    Generic VAEM config dataclass and factory for initialization.

    When called directly, acts as a factory and returns the appropriate
    subclass instance based on the ``interface`` argument.

    Attributes:
        interface (str): Interface to connect to VAEM. Ex: ``'tcp/ip'``, ``'serial'``
        unit_id (int): Modbus Unit ID of the VAEM (default: 1)

    Example:
        Factory usage returns a VAEMTCPConfig instance::

            config = VAEMConfig(interface="tcp/ip", ip="192.168.0.1")

        Factory usage returns a VAEMSerialConfig instance::

            config = VAEMConfig(interface="serial", com_port="COM3", baudrate=9600)

    Raises:
        ValueError: If ``interface`` is not a recognised value.
    """

    interface: str
    unit_id: int = 1
    # TODO: connected_valve_terminals: set, to be used in guards to throw errors/warnings if a user tries to access a terminal that is not physically connected, per the config

    def __new__(cls, *, interface: str | None = None, **kwargs) -> "VAEMConfig":
        """Create and return the appropriate config subclass instance.

        When called on ``VAEMConfig`` directly, dispatches to the correct
        subclass based on ``interface``. When called on a subclass,
        delegates to ``object.__new__``.

        Args:
            interface: The communication interface. Supported values are
                ``'tcp/ip'`` and ``'serial'``.
            **kwargs: Additional keyword arguments forwarded to the
                subclass ``__init__``.

        Returns:
            A VAEMTCPConfig instance for ``interface='tcp/ip'``, or a
            VAEMSerialConfig instance for ``interface='serial'``.

        Raises:
            ValueError: If ``interface`` is not a recognised value.
        """
        if cls is VAEMConfig:
            if interface == "tcp/ip":
                return object.__new__(VAEMTCPConfig)
            if interface == "serial":
                return object.__new__(VAEMSerialConfig)
            raise ValueError(f"Unknown interface: {interface!r}")
        return object.__new__(cls)


@dataclass(kw_only=True)
class VAEMTCPConfig(VAEMConfig):
    """
    Datclass for VAEM TCP/IP connection.

    Attributes:
        ip (str): IP address of the VAEM # TODO: Make ipaddress.ip_address(...)
        port (int): Port number of the VAEM (default: 502)

    Typical usage example:
        vaem_config = VAEMTCPConfig(ip=, port=502)

        vaem = VAEM(config=vaem_config)
    """

    interface: str = "tcp/ip"
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
        vaem_serial_config = VAEMSerialConfig(com_port = "COM3", baudrate = 9600)

        vaem = VAEM(vaem_serial_config)
    """

    interface: str = "serial"
    com_port: str
    baudrate: int
