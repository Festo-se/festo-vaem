"""
Front end VAEM interface for the Python driver.

This interface is the exposed layer of the device driver to the user.

Typical usage example:
    vaem_tcp_config = VAEMTCPConfig(interface="tcp/ip", ip=ip, port=502)

    vaem = VAEM(config=vaem_tcp_config)

    valve_opening_times = {1: 100,
                            2: 100,
                            3: 100,
                            4: 100,
                            5: 100,
                            6: 100,
                            7: 100,
                            8: 100,
                            }

    vaem.open_valves(timings = valve_opening_times)
"""

import logging
from vaem.vaem_communication import VAEMModbusSerial, VAEMModbusTCP
from vaem.vaem_config import VAEMConfig, VAEMSerialConfig, VAEMTCPConfig

logger = logging.getLogger(__name__)


class VAEM:
    """
    VAEM driver class.

    This is the main class that the user will interact with to control the VAEM valve control module.
    """

    def __init__(self, config: VAEMConfig):
        """
        Constructor.

        Args:
            config (VAEMConfig): A ModbusTCP, or ModbusSerial
                    type to allow the driver to connect to
                    the correct communication interface.

        Returns:
            None

        Raises:
            TypeError: Error occured with config
        """
        if isinstance(config, VAEMConfig):
            self._config = config
            match self._config:
                case VAEMTCPConfig():
                    self._backend = VAEMModbusTCP(config=self._config)
                    logger.debug("VAEM TCP/IP backend initialized with config: %s", self._config)
                case VAEMSerialConfig():
                    logger.error("VAEM Serial backend is currently not implemented.")
                    self._backend = VAEMModbusSerial(config=self._config)
        else:
            logger.error("Error, configuration passed in is not supported by the driver")
            raise TypeError("Error, configuration passed in is not supported by the driver")

    def select_valve(self, valve_id: int) -> None:
        """
        Selects one valve in the VAEM.

        According to VAEM Logic all selected valves can be opened,
        others cannot with open command

        Typical usage example:
            valve_id = 1

            vaem.select_valve(valve_id = valve_id)

        Args:
            valve_id (int): The id of the valve to select

        Returns:
            None
        """
        self._backend.select_valve(valve_id)

    def deselect_valve(self, valve_id: int) -> None:
        """
        Deselects one valve in the VAEM.

        According to VAEM Logic all selected valves can be opened,
        others cannot with open command

        Typical usage example:
            valve_id = 1

            vaem.deselect_valve(valve_id)

        Args:
            valve_id (int): The ID of the valve to select. Valid numbers are from 1 to 8

        Returns:
            None
        """
        self._backend.deselect_valve(valve_id)

    def set_valve_switching_time(self, valve_id: int, opening_time: int) -> None:
        """
        Sets the switching time for the specified valve.

        Typical usage example:
            valve_id = 1

            opening_time = 100

            vaem.set_valve_switching_time(valve_id = valve_id, opening_time = opening_time)

        Args:
            valve_id (int): ID number of the valve for configuration
            opening_time (int): Time in milliseconds of which the Valve with the ID will be opened

        Returns:
            None
        """
        self._backend.set_valve_switching_time(valve_id, opening_time)

    def open_selected_valves(self) -> None:
        """
        Opens all valves that are selected.

        Typical usage example:
            vaem.open_selected_valves()

        Args:
            None

        Returns:
            None
        """
        self._backend.open_selected_valves()

    def open_valves(self, timings: dict[int, int]) -> None:
        """
        Selects and opens valves with specified actuation times.

        Typical usage example:
            valve_opening_times = {1: 100,
                                2: 100,
                                3: 100,
                                4: 100,
                                5: 100,
                                6: 100,
                                7: 100,
                                8: 100,
                                }

            vaem.open_valves(timings = valve_opening_times)

        Args:
            timings (dict): Dictionary of valve indices and actuation times

        Returns:
            None
        """
        self._backend.open_valves(timings)

    def close_valves(self) -> None:
        """
        Closes valves that were previously selected.

        Typical usage example:
            vaem.close_valves()

        Args:
            None

        Returns:
            None
        """
        self._backend.close_valves()

    def get_status(self) -> dict:
        """
        Read the status of the VAEM.

        The status is return as a dictionary with the following keys:

        -> status: 1 if more than 1 valve is active

        -> error: 1 if error in valves is present

        Typical usage example:
            status = vaem.get_status()

            print(status)

        Args:
            None

        Returns:
            Dictionary of the status for the device. For more information, please refer to the VAEM Operation Instruction manual.
        """
        return self._backend.get_status()

    def clear_error(self) -> None:
        """
        If any error occurs in valve opening, must be cleared with this opperation.

        Typical usage example:
            vaem.clear_error()

        Args:
            None

        Returns:
            None
        """
        self._backend.clear_error()

    def set_inrush_current(self, valve_id: int, inrush_current: int) -> None:
        """
        Changes the inrush current for the valves based on valve ID.

        Typical usage example:
            valve_id = 1

            inrush_current_ma = 100

            vaem.set_inrush_current(valve_id = valve_id, inrush_current = inrush_current_ma)

        Args:
            valve_id (int): Target valve for selection
            inrush_current (int): In mA the new inrush current for the valve

        Returns:
            None
        """
        self._backend.set_inrush_current(valve_id, inrush_current)

    def get_inrush_current(self, valve_id: int) -> int | None:
        """
        Gets the Inrush Current for the selected Valve ID.

        Typical usage example:
            valve_id = 1

            inrush_current_ma = get_inrush_current(valve_id = valve_id)

            print(inrush_current_ma)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Inrush current for valve ID in mA
        """
        return self._backend.get_inrush_current(valve_id)

    def set_nominal_voltage(self, valve_id: int, voltage: int) -> None:
        """
        Sets the nominal voltage on the valve ID specified.

        Typical usage example:
            valve_id = 1

            voltage_mv = 10000

            vaem.set_nominal_voltage(valve_id = valve_id, voltage = voltage_mv)

        Args:
            valve_id (int): ID number of valve for setting (1-8)
            voltage (int): Voltage to be set in mV (8000-24000)

        Returns:
            None
        """
        self._backend.set_nominal_voltage(valve_id, voltage)

    def get_nominal_voltage(self, valve_id: int) -> int | None:
        """
        Gets the nominal voltage for the specified valve ID.

        Typical usage example:
            valve_id = 1

            voltage_mv = get_nominal_voltage(valve_id = valve_id)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Nominal voltage in mV
        """
        return self._backend.get_nominal_voltage(valve_id)

    def get_valve_switching_time(self, valve_id: int) -> int | None:
        """
        Gets the switching time in ms for the specific valve ID.

        Typical usage example:
            valve_id = 1

            switching_time_ms = vaem.get_valve_switching_time(valve_id = valve_id)

            print(switching_time_ms)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Switching time in ms
        """
        return self._backend.get_valve_switching_time(valve_id)

    def get_delay_time(self, valve_id: int) -> int | None:
        """
        Gets the current delay time for the valve ID.

        Typical usage example:
            valve_id = 1

            delay_time_ms = vaem.get_delay_time(valve_id = valve_id)

            print(delay_time_ms)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Delay time for the valve ID in ms
        """
        return self._backend.get_delay_time(valve_id)

    def set_delay_time(self, valve_id: int, delay_time: int) -> None:
        """
        Sets the delay time for a specific valve ID.

        Typical usage example:
            valve_id = 1

            delay_time = 100

            vaem.set_delay_time(valve_id = valve_id, delay_time = delay_time)

        Args:
            valve_id (int): Valve ID (1-8)
            delay_time (int): Delay time to be set for the valve ID

        Returns:
            None
        """
        self._backend.set_delay_time(valve_id, delay_time)

    def get_pickup_time(self, valve_id: int) -> int | None:
        """
        Gets the pickup time for the selected valve ID (1-8).

        Typical usage example:
            valve_id = 1

            pickup_time = vaem.get_pickup_time(valve_id = valve_id)

            print(pickup_time)

        Args:
            valve_id (int): Valve ID 1-8

        Returns:
            Pickup time in ms
        """
        return self._backend.get_pickup_time(valve_id)

    def set_pickup_time(self, valve_id: int, pickup_time: int) -> None:
        """
        Sets the pickup time for the specified valve ID 1-8.

        Typical usage example:
            valve_id = 1

            pickup_time = 100

            vaem.set_pickup_time(valve_id = valve_id, pickup_time = pickup_time)

        Args:
            valve_id (int): ID number for valve (1-8)
            pickup_time (int): Pickup time in ms

        Returns:
            None
        """
        self._backend.set_pickup_time(valve_id, pickup_time)

    def get_holding_current(self, valve_id: int) -> int | None:
        """
        Gets the current holding current for the valve selected 1-8.

        Typical usage example:
            valve_id = 1

            holding_current = vaem.get_holding_current(valve_id = valve_id)

            print(holding_current)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Holding current of valve in mA
        """
        return self._backend.get_holding_current(valve_id)

    def set_holding_current(self, valve_id: int, holding_current: int) -> None:
        """
        Sets the holding current for the valve selected 1-8.

        Typical usage example:
            valve_id = 1

            holding_current = 100

            vaem.set_holding_current(valve_id = valve_id, holding_current = holding_current)

        Args:
            valve_id (int): Valve ID (1-8)
            holding_current (int): Holding current in mA (20-400)

        Returns:
            None
        """
        self._backend.set_holding_current(valve_id, holding_current)

    def save_settings(self) -> None:
        """
        Saves all parameters to non-volatile memory.

        Typical usage example:
            vaem.save_settings()

        Args:
            None

        Returns:
            None
        """
        self._backend.save_settings()

    def get_current_reduction_time(self, valve_id: int) -> int | None:
        """
        Gets the time that the current is reduced to the holding current value for the valve selected 1-8.

        Typical usage example:
            valve_id = 1

            reduction_time = vaem.get_current_reduction_time(valve_id = valve_id)

            print(reduction_time)

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            Current reduction time in ms
        """
        return self._backend.get_current_reduction_time(valve_id)

    def set_current_reduction_time(self, valve_id: int, reduction_time: int) -> None:
        """
        Sets the time that the current is reduced to the holding current value for the valve selected 1-8.

        Typical usage example:
            valve_id = 1

            current_reduction_time = 100

            vaem.set_current_reduction_time(valve_id = valve_id, reduction_time = current_reduction_time)

        Args:
            valve_id (int): Valve ID (1-8)
            reduction_time (int): Desired length of time to go from inrush current to holding current in ms

        Returns:
            None
        """
        self._backend.set_current_reduction_time(valve_id, reduction_time)

    def get_error_handling_status(self) -> int | None:
        """
        Gets the current state of the internal error handling of the VAEM device.

        Typical usage example:
            error_handling_status = vaem.get_error_handling_status()

            print(error_handling_status)

        Args:
            None

        Returns:
            State of internal error handling. 1 for enabled, 0 for disabled
        """
        return self._backend.get_error_handling_status()

    def set_error_handling(self, activate: int) -> None:
        """
        Sets the internal error handling of the vaem. Disabling this will cause the VAEM to omit certain errors.

        Typical usage example:
            turn_off_handling = 0

            vaem.set_error_handling(activate = turn_off_handling)

        Args:
            activate (int): 1 or 0. 1 activates the error handling and 0 disables error handling

        Returns:
            None
        """
        self._backend.set_error_handling(activate)
