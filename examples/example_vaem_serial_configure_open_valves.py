"""Example script to configure and open all valves on the VAEM device over a serial connection."""

from os import getenv

from vaem import VAEM, VAEMSerialConfig
from festo_python_logging import configure_logging

configure_logging(verbose=True, silence=["pymodbus.logging"])

com_port = getenv("VAEM_SERIAL_PORT", "COM3")

"""Create a VAEM instance with serial configuration"""
vaem_config = VAEMSerialConfig(interface="serial", com_port=com_port, baudrate=9600)
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
