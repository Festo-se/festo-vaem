"""Example script to start up the VAEM device."""

from os import getenv

from vaem import VAEM, VAEMTCPConfig

ip = getenv("VAEM_IP", "192.168.0.1")

"""Create a VAEM instance with TCP/IP configuration"""
vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)
