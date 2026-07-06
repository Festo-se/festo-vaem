"""Example script to read and clear errors on the VAEM device over a serial connection."""

from os import getenv

from vaem import VAEM, VAEMSerialConfig
from festo_python_logging import configure_logging

configure_logging(verbose=True, silence=["pymodbus.logging"])

com_port = getenv("VAEM_SERIAL_PORT", "COM3")

"""Create a VAEM instance with serial configuration"""
vaem_config = VAEMSerialConfig(interface="serial", com_port=com_port, baudrate=9600)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)

"""Read and clear any errors on the VAEM device"""
status = vaem.get_status()
print(f"VAEM Status before clear: {status}")
vaem.clear_error()
status = vaem.get_status()
print(f"VAEM Status after clear: {status}")
