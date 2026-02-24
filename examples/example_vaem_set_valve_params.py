"""Example script of how to set valve parameters on the VAEM device."""

from os import getenv

from vaem import VAEM, VAEMTCPConfig

ip = getenv("VAEM_IP", "192.168.0.1")

"""Create a VAEM instance with TCP/IP configuration"""
vaem_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)
"""Initialize the VAEM device"""
vaem = VAEM(config=vaem_config)

"""Setting all parameters for valve with ID 1"""
valve_id = 1

nominal_voltage_mv = 10000
vaem.set_nominal_voltage(valve_id, nominal_voltage_mv)

swithing_time_ms = 100
vaem.set_valve_switching_time(valve_id, swithing_time_ms)

delay_time_ms = 100
vaem.set_delay_time(valve_id, delay_time_ms)

pickup_time_ms = 100
vaem.set_pickup_time(valve_id, pickup_time_ms)

inrush_current_ma = 100
vaem.set_inrush_current(valve_id, inrush_current_ma)

holding_current_ma = 100
vaem.set_holding_current(valve_id, holding_current_ma)

current_reduction_time = 100
vaem.set_current_reduction_time(valve_id, current_reduction_time)

"""Save all settings to the VAEM device's eeprom"""
vaem.save_settings()
