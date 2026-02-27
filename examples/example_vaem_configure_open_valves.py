"""Example script to configure and open all valves on the VAEM device."""

from os import getenv

from vaem import VAEM, VAEMTCPConfig
from festo_python_logging import configure_logging

configure_logging(verbose=True, silence=["pymodbus.logging"])

ip = getenv("VAEM_IP", "192.168.0.1")

"""Create a VAEM instance with TCP/IP configuration"""
vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)

"""Configure and open all valves on the VAEM device"""
opening_time_ms = 100
for _ in range(1, 9):
    vaem.select_valve(_)
    vaem.set_valve_switching_time(valve_id=_, opening_time=opening_time_ms)

"""Open all selected valves"""
vaem.open_selected_valves()

"""Deselect all valves after operation"""
for _ in range(1, 9):
    vaem.deselect_valve(_)
