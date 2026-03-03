"""Example script to get valve parameters from the VAEM device."""

from os import getenv

from vaem import VAEM, VAEMTCPConfig
from festo_python_logging import configure_logging

configure_logging(verbose=True, silence=["pymodbus.logging"])

ip = getenv("VAEM_IP", "192.168.0.1")

"""Create a VAEM instance with TCP/IP configuration"""
vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)

"""Get and print valve parameters for specified valve ID"""
valve_id = 1

nominal_voltage_mv = vaem.get_nominal_voltage(valve_id)
print(f"Nominal Voltage (mV) for Valve {valve_id}: {nominal_voltage_mv}")

switching_time_ms = vaem.get_valve_switching_time(valve_id)
print(f"Switching Time (ms) for Valve {valve_id}: {switching_time_ms}")

delay_time_ms = vaem.get_delay_time(valve_id)
print(f"Delay Time (ms) for Valve {valve_id}: {delay_time_ms}")

pickup_time_ms = vaem.get_pickup_time(valve_id)
print(f"Pickup Time (ms) for Valve {valve_id}: {pickup_time_ms}")

inrush_current_ma = vaem.get_inrush_current(valve_id)
print(f"Inrush Current (mA) for Valve {valve_id}: {inrush_current_ma}")

holding_current_ma = vaem.get_holding_current(valve_id)
print(f"Holding Current (mA) for Valve {valve_id}: {holding_current_ma}")

current_reduction_time_ms = vaem.get_current_reduction_time(valve_id)
print(
    f"Time it takes in ms to go from inrush current in mA to holding current in mA for Valve {valve_id}: {current_reduction_time_ms}"
)
