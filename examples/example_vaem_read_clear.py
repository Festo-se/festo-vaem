"""Example script to read and clear errors on the VAEM device."""

from os import getenv

from vaem import VAEM, VAEMTCPConfig
from festo_python_logging import configure_logging

configure_logging(verbose=True, silence=["pymodbus.logging"])

ip = getenv("VAEM_IP", "192.168.0.1")

"""Create a VAEM instance with TCP/IP configuration"""
vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)

"""Read and clear any errors on the VAEM device"""
status = vaem.get_status()
print(f"VAEM Status before clear: {status}")
vaem.clear_error()
status = vaem.get_status()
print(f"VAEM Status after clear: {status}")
