"""
Festo VAEM backend communication module.

This module handles all communication underneath the hood
and abstracting it all from the user.
"""

import logging

import struct
import time
import serial
import atexit
from abc import ABC, abstractmethod

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException, ModbusIOException
from .vaem_config import VAEMConfig, VAEMSerialConfig, VAEMTCPConfig
from .vaem_helper import (
    VaemAccess,
    VaemControlWords,
    VaemDataType,
    VaemIndex,
    VaemOperatingMode,
    vaemValveIndex,
    VAEM_SERIAL_REGEX,
)

logger = logging.getLogger(__name__)


class VAEMBase(ABC):
    """Base VAEM Client Class."""

    @abstractmethod
    def __init__(self, config: VAEMConfig):
        """
        VAEMBase constructor.

        Abstract base class to build out VAEM clients.

        Args:
            config (VAEMConfig): A ModbusTCP or ModbusSerial
                    type to allow the driver to connect to the
                    correct communication interface.

        Returns:
            None
        """
        self._init_done = False
        self._config = config

        self.error_handling_enabled = 1  # TODO: Make this part of the config
        self.active_valves = [0, 0, 0, 0, 0, 0, 0, 0]
        # self.active_valves = {i:False for i in range(1,9)} TODO: Change name active_valves to selected_valves
        # TODO: Add config item for connected_valve_terminals (instead of active_valves -- undoing confusion)
        atexit.register(self.close_client)  # TODO: Check if this is right

    def get_transfer_value(self, operation, index, sub_index=0, transfer_value=None) -> dict:
        """
        Gets the transfer value for the VAEM operation.

        Typical usage example:
            data = vaem.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.STARTVALVES.value,
            )

        Args:
            operation: Operational access type -- Read or Write specifier
            index: Data object index for accessing VAEM register. Must be of type VaemIndex Enum class
            sub_index: Data object sub_index; often, the valve index for the VAEM
            transfer_value: The actual value to be transfered and saved to the index:sub_index pair location on the VAEM
        Returns:
            dictionary of out parameters to be passed into the VAEM
        """
        out = {}
        out["access"] = operation
        out["paramIndex"] = index.value
        out["paramSubIndex"] = sub_index
        out["errorRet"] = 0
        out["dataType"] = VaemDataType.UINT16.value
        out["transferValue"] = transfer_value

        match index.value:
            case 0x07 | 0x08 | 0x16 | 0x2E:
                # Response time
                out["dataType"] = VaemDataType.UINT32.value
            case 0x09 | 0x2D:
                # Operating mode
                out["dataType"] = VaemDataType.UINT8.value
            case 0x13:
                out["dataType"] = VaemDataType.UINT8.value
                out["paramSubIndex"] = 0
                out["transferValue"] = sub_index
            case 0x01 | 0x02 | 0x04 | 0x05 | 0x06 | 0x0B:
                pass
            case _:
                logger.error("Currently unsupported input param")

        return out

    def _get_status(self, status_word) -> dict:
        """
        Gets the current status of the different parts of the VAEM.

        from the 15 bit status word returned by the VAEM.

        Args:
            status_word (int): 15 bit binary status word from VAEM

        Returns:
            Dictionary of values for each param
        """
        status = {}
        status["Status"] = status_word & 0x01
        status["Error"] = (status_word & 0x08) >> 3
        status["Readiness"] = (status_word & 0x10) >> 4
        status["OperatingMode"] = (status_word & 0xC0) >> 6
        status["Valve1"] = (status_word & 0x100) >> 8
        status["Valve2"] = (status_word & 0x200) >> 9
        status["Valve3"] = (status_word & 0x400) >> 10
        status["Valve4"] = (status_word & 0x800) >> 11
        status["Valve5"] = (status_word & 0x1000) >> 12
        status["Valve6"] = (status_word & 0x2000) >> 13
        status["Valve7"] = (status_word & 0x4000) >> 14
        status["Valve8"] = (status_word & 0x8000) >> 15
        return status

    @abstractmethod
    def _construct_frame(self, data: dict) -> list:
        """
        Constructs data frame for transfer to VAEM device.

        Args:
            data (dict): Data to be sent to VAEM device
        Returns:
            list or string containing values to be passed to the device
        """
        pass

    @abstractmethod
    def _deconstruct_frame(self, frame) -> dict | None:
        """
        Deconstructs incoming data frame from VAEM device.

        Args:
            frame: dict coming in from the device
        Returns:
            data: dictionary that contains the information from the dataframe.
        """
        pass

    @abstractmethod
    def _transfer(self, write_data: list) -> list:
        """
        Method of transferring information from Python driver to device.

        Args:
            write_data: List of data that will be transferred to VAEM device
        Returns:
            Response from VAEM device.
        """
        pass

    @abstractmethod
    def close_client(self):
        """
        Closes the client connection to the VAEM device.

        Returns:
            None
        """
        pass

    def send_command(self, data: dict) -> dict | None:
        """
        Sends commands to vaem device and returns response.

        Typical usage example:
            data = vaem._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.STARTVALVES.value,
            )
            response = vaem.send_command(data)

        Args:
            data: Dictionary of data that will be transferred to VAEM device

        Returns:
            Dictionary of response data from VAEM device.
        """
        frame = self._construct_frame(data)
        resp = self._transfer(frame)
        if resp is not None:
            resp = self._deconstruct_frame(resp)
        return resp

    def _vaem_init(self):
        """
        Runs an additional vaem initialization process to configure.

        the correct read and write for the driver.
        """
        if self._init_done:
            try:
                # set operating mode
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.OPERATINGMODE,
                    0,
                    VaemOperatingMode.OPMODE1.value,
                )
                self.send_command(data)
                self.clear_error()
                self._init_done = True
                self.error_handling_enabled = self.get_error_handling_status()
            except ConnectionError as e:
                logger.error("Connection error: %s. ", str(e))
        else:
            logger.warning("No VAEM Connected!! CANNOT INITIALIZE")

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
        data = {}
        if self._init_done:
            # save settings
            data["access"] = VaemAccess.WRITE.value
            data["dataType"] = VaemDataType.UINT32.value
            data["paramIndex"] = VaemIndex.SAVEPARAMETERS.value
            data["paramSubIndex"] = 0
            data["errorRet"] = 0
            data["transferValue"] = 99999
            self.send_command(data)
        else:
            logger.warning("No VAEM Connected!!")

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id in range(1, 9):
                # get currently selected valves
                # data = [VaemAccess.READ.value, VaemIndex.SELECTVALVE.value, vaemValveIndex[valve_id]]
                data = self.get_transfer_value(
                    VaemAccess.READ.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id],
                )
                resp = self.send_command(data)
                if resp is None:
                    logger.warning("Failed to read select valve status")
                    return
                # select new valve
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id] | resp["transferValue"],
                )
                self.send_command(data)
                self.active_valves[valve_id - 1] = 1
            else:
                logger.error("Valve ID's have a range of 1-8, Inputted : %s", valve_id)
                raise ValueError(f"Valve index out of bounds: {valve_id}")
        else:
            logger.warning("No VAEM Connected!!")

    def deselect_valve(self, valve_id: int) -> None:
        """
        Deselects one valve in the VAEM.

        According to VAEM Logic all selected valves can be opened,
        others cannot with open command

        Typical usage example:
            for _ in range (1, 9):

                vaem.deselect_valve(_)

        Args:
            valve_id (int): The ID of the valve to select. Valid numbers are from 1 to 8

        Returns:
            None

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id in range(1, 9):
                # get currently selected valves
                data = self.get_transfer_value(
                    VaemAccess.READ.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id],
                )
                resp = self.send_command(data)
                if resp is None:
                    logger.warning("Failed to read select valve status")
                    return
                # deselect new valve
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SELECTVALVE,
                    resp["transferValue"] & (~(vaemValveIndex[valve_id])),
                )
                self.send_command(data)
                self.active_valves[valve_id - 1] = 0
            else:
                logger.error("Valve ID's have a range of 1-8, Inputted : %s", valve_id)
                raise ValueError(f"Valve index out of bounds: {valve_id}")
        else:
            logger.warning("No VAEM Connected!!")

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            opening_time = int(opening_time / 0.2)
            if (opening_time in range(0, 9999999999999)) and (valve_id in range(1, 9)):
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SWITCHINGTIME,
                    (valve_id - 1),
                    int(opening_time),
                )
                self.send_command(data)
            else:
                logger.error("Valve ID's have a range of 1-8, Inputted : %s", valve_id)
                raise ValueError
        else:
            logger.warning("No VAEM Connected!!")

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
        if self._init_done:
            # save settings
            if self.error_handling_enabled:
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.CONTROLWORD,
                    0,
                    VaemControlWords.STARTVALVES.value,
                )
                self.send_command(data)
            else:
                data = self.get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.CONTROLWORD,
                    0,
                    VaemControlWords.STARTVALVESRESETERROR.value,
                )
                self.send_command(data)

            self.clear_control_word()
        else:
            logger.warning("No VAEM Connected!!")

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
        for key, value in timings.items():
            self.select_valve(valve_id=key)
            self.set_valve_switching_time(valve_id=key, opening_time=value)
        self.open_selected_valves()

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
        if self._init_done:
            # save settings
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.STOPVALVES.value,
            )
            self.send_command(data)
            self.clear_error()
        else:
            logger.warning("No VAEM Connected!!")

    def get_control_word(self) -> int | None:
        """
        Gets the current control word of the VAEM.

        Typical usage example:
            control_word = vaem.get_control_word()

            print(control_word)

        Args:
            None

        Returns:
            Control word of the VAEM. For more information, please refer to the VAEM Operation Instruction manual.
        """
        if self._init_done:
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.CONTROLWORD,
                0,
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(resp["transferValue"])
        logger.warning("No VAEM Connected!!")
        return None

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
        if self._init_done:
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.STATUSWORD,
                0,
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                logger.info(self._get_status(resp["transferValue"]))
                return self._get_status(resp["transferValue"])
        logger.warning("No VAEM Connected!!")
        return {}

    def clear_control_word(self) -> None:
        """
        Clears the control word of the VAEM.

        This is used to reset the control word after an open or close command.

        Typical usage example:
            vaem.clear_control_word()
        """
        if self._init_done:
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.RESETSTATE.value,
            )
            resp = self.send_command(data)
            if resp is not None and resp["errorRet"] == 0:
                logger.info("Control word cleared successfully")
        else:
            logger.warning("No VAEM Connected!!")

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
        if self._init_done:
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.RESETERRORS.value,
            )
            resp = self.send_command(data)
            if resp is not None:
                if resp["errorRet"] == 0:
                    logger.info("Error cleared successfully")
                    self.clear_control_word()
                else:
                    logger.error("Error could not be cleared, error code: %s", resp["errorRet"])
        else:
            logger.warning("No VAEM Connected!!")

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

        Raises:
            ValueError: Valve index out of bounds
            ValueError: Input value for current not in range 20 - 1000 mA
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            if inrush_current not in range(20, 1001):
                raise ValueError(
                    f"Error, input for inrush current was: {inrush_current}, inrush current ranges from 20, 1000 mA"
                )
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.INRUSHCURRENT,
                (valve_id - 1),
                int(inrush_current),
            )
            self.send_command(data)

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.INRUSHCURRENT,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return resp["transferValue"]
        return None

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

        Raises:
            ValueError: Valve index out of bounds
            ValueError: Input value for voltage not in range 8000 - 24000 mV
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            if voltage not in range(8000, 24001):
                raise ValueError(f"Error, input voltage was: {voltage}, input voltage ranges from 8000-24000 mV")
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.NOMINALVOLTAGE,
                (valve_id - 1),
                voltage,
            )
            self.send_command(data)

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.NOMINALVOLTAGE,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return resp["transferValue"]
        return None

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.SWITCHINGTIME,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(resp["transferValue"] * 0.2)
        return None

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.TIMEDELAY,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(resp["transferValue"] * 0.2)
        return None

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            delay_time = int(delay_time / 0.2)
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.TIMEDELAY,
                (valve_id - 1),
                delay_time,
            )
            self.send_command(data)

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.PICKUPTIME,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(resp["transferValue"] * 0.2)
        return None

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

        Raises:
            ValueError: Valve index out of bounds
            ValueError: Input value for pickup time not in range 1 - 500 ms
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            if pickup_time not in range(1, 501):
                raise ValueError(f"Error, input pickup time was {pickup_time} ms, This is out of the range of 1-500 ms")
            pickup_time = int(pickup_time / 0.2)
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.PICKUPTIME,
                (valve_id - 1),
                pickup_time,
            )
            self.send_command(data)

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.HOLDINGCURRENT,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return resp["transferValue"]
        return None

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

        Raises:
            ValueError: Valve index out of bounds
            ValueError: Input value for holding current not in range 20 - 400 mA
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            if holding_current not in range(20, 401):
                raise ValueError(f"Error, input holding current out of range: {holding_current}")
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.HOLDINGCURRENT,
                (valve_id - 1),
                int(holding_current),
            )
            self.send_command(data)

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                (valve_id - 1),
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(resp["transferValue"] * 0.2)
        return None

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

        Raises:
            ValueError: Valve index out of bounds
        """
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            reduction_time = int(reduction_time * 5)
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                (valve_id - 1),
                int(reduction_time),
            )
            self.send_command(data)

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

        Raises:
            ValueError: Input value for activation was not a 1 or 0
        """
        if self._init_done:
            if activate not in (0, 1):
                raise ValueError(f"Error, value inputted was {activate}, Either a 1 or 0 is accepted")
            data = self.get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.ERRORHANDLING,
                0,
                int(not activate),
            )
            self.send_command(data)
            self.error_handling_enabled = activate
            match activate:
                case 0:
                    logger.warning("""WARNING: Disabling error handling will cause the device to omit certain errors and
                                           certain functionalitites of the driver will be disabled """)
                case 1:
                    logger.info("""Error handling is enabled""")

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
        if self._init_done:
            data = self.get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.ERRORHANDLING,
                0,
                0,
            )
            resp = self.send_command(data)
            if resp is not None:
                return int(not resp["transferValue"])
        return None


class VAEMModbusTCP(VAEMBase):
    """VAEM Modbus TCP client class."""

    client: ModbusTcpClient

    def __init__(self, config: VAEMTCPConfig):
        """
        Contstructor.

        Args:
            config (VAEMTCPConfig): A configuration class designated for ModbusTCP.

        Returns:
            None

        Raises:
            TypeError: Incorrect ModbusTCP config passed in
            ConnectionError: Connection error with device
            ModbusIOException: Error with Modbus connection
        """
        self._read_param = {
            "address": 0,
            "length": 0x07,
        }
        self._write_param = {
            "address": 0,
            "length": 0x07,
        }
        super().__init__(config)
        if not isinstance(config, VAEMTCPConfig):
            config_type = type(config)
            raise TypeError(
                f"""Error: Config does not match the ModbusTCP backend
                The type passed in was: {config_type}"""
            )
        try:
            self._config = config
            self.client = ModbusTcpClient(host=self._config.ip, port=self._config.port)
            self.client.connect()
            self._init_done = True
            self._vaem_init()
        except ConnectionError as e:
            logger.error("Connection error: %s. ", str(e))
        except ModbusIOException as io_error:
            logger.error("Modbus IO error: %s. ", str(io_error))
            logger.info(self._config)

    def _construct_frame(self, data: dict) -> list:
        """
        Constructs data frame for transfer to VAEM device.

        Args:
            data (dict): Data to be sent to VAEM device
        Returns:
            list of values to be passed as the expected data type of the Modbus data frame
        """
        frame = []
        tmp = struct.pack(
            ">BBHBBQ",
            data["access"],
            data["dataType"],
            data["paramIndex"],
            data["paramSubIndex"],
            data["errorRet"],
            data["transferValue"],
        )
        try:
            for i in range(0, len(tmp) - 1, 2):
                frame.append((tmp[i] << 8) + tmp[i + 1])
        except ValueError as e:
            logger.error("Value error: %s. ", str(e))
        return frame

    def _deconstruct_frame(self, frame) -> dict | None:
        """
        Deconstructs incoming data frame from VAEM device.

        Args:
            frame: dict coming in from the device
        Returns:
            data: dictionary that contains the information from the dataframe.
        """
        data = {}
        if frame:
            data["access"] = (frame[0] & 0xFF00) >> 8
            data["dataType"] = frame[0] & 0x00FF
            data["paramIndex"] = frame[1]
            data["paramSubIndex"] = (frame[2] & 0xFF00) >> 8
            data["errorRet"] = frame[2] & 0x00FF
            data["transferValue"] = 0
            for i in range(4):
                data["transferValue"] += frame[len(frame) - 1 - i] << (i * 16)
        else:
            logger.warning("Empty data frame received, potential operation error state detected: %s", frame)
            return None
        return data

    def _transfer(self, write_data: list) -> list:
        """
        Method of transferring information from Python driver to device.

        Args:
            write_data: List of data that will be transferred to VAEM device
        Returns:
            Response from VAEM device.
        """
        data_registers = []
        if not self.client.connected:
            self.client.connect()
        try:
            data = self.client.readwrite_registers(
                read_address=self._read_param["address"],
                read_count=self._read_param["length"],
                write_address=self._write_param["address"],
                values=write_data,
                device_id=self._config.unit_id,
            )
            time.sleep(0.001)
            data_registers = data.registers
        except ModbusException as modbus_error:
            logger.error("Something went wrong with read opperation VAEM : %s", str(modbus_error))

        return data_registers

    def close_client(self) -> None:
        """
        Closes the Modbus TCP client connection.

        Typical usage example:
            vaem.close_client()

        Args:
            None

        Returns:
            None
        """
        try:
            if self.client and self.client.connected:
                self.client.close()
                logger.info("Modbus TCP connection closed successfully.")
        except Exception as error:
            logger.error("Error occurred while closing Modbus TCP connection: %s", str(error))


class VAEMSerial(VAEMBase):
    """Class used as the interface backend for using Serial communication."""

    class EfficientSerial(serial.Serial):
        """Efficient Serial Subclass.

        Pyserial has known issues that make `Serial.readall` and `Serial.readline` very slow. This implementation address that
        by
        cf. https://github.com/pyserial/pyserial/issues/216#issuecomment-369414522
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.buffer = bytearray()

        def readline(self, size: int | None = -1, /, eol: bytes = b"\r") -> bytes:
            i = self.buffer.find(eol)
            if i >= 0:
                r = self.buffer[: i + 1]
                self.buffer = self.buffer[i + 1 :]
                return bytes(r)
            while True:
                i = max(1, min(2048, self.in_waiting))
                data = self.read(i)
                if not data:
                    # Read timed out with no terminator; return whatever is buffered.
                    r = bytes(self.buffer)
                    self.buffer = bytearray()
                    return r
                i = data.find(eol)
                if i >= 0:
                    r = bytes(self.buffer + data[: i + 1])
                    self.buffer = bytearray(data[i + 1 :])
                    return r
                else:
                    self.buffer.extend(data)

    client: EfficientSerial

    def __init__(self, config: VAEMSerialConfig):
        """
        VAEMModbusSerial Constructor.

        Args:
            config (VAEMSerialConfig): A configuration class designated for ModbusSerial

        Returns:
            None

        Raises:
            TypeError: Config does not match serial interface specs.
            RuntimeError: A runtime error with the serial interface has occurred.
        """
        super().__init__(config)
        logger.info("Initializing VAEMSerial client")
        if not isinstance(config, VAEMSerialConfig):
            config_type = type(config)
            raise TypeError(
                f"""Error: Config does not match the Serial backend.
                            The type passed in was: {config_type}"""
            )
        try:
            self._config = config
            logger.debug(
                "Opening serial connection on port=%s baudrate=%s",
                self._config.com_port,
                self._config.baudrate,
            )
            self.client = self.EfficientSerial(
                port=self._config.com_port,
                baudrate=self._config.baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1,  # TODO: comprehensive timeout setting function. Different for modbus and serial backends
            )
            # self.reader = ReadLine(self.client)
            logger.info("Serial connection established on %s", self._config.com_port)
            self._init_done = True
            self._vaem_init()
        except RuntimeError as run_err:
            logger.error("Runtime error: %s. ", str(run_err))

    def _list_to_ascii(self, command_list: list) -> str:
        """
        Convert command list to an ASCII telegram string and validate syntax.

        Args:
            command_list (list): Tokenized serial command frame.

        Returns:
            str: Validated ASCII telegram command.

        Raises:
            ValueError: Command list is empty or does not match expected VAEM syntax.
        """
        logger.debug("VAEMSerial._list_to_ascii called with command_list=%s", command_list)
        if not command_list:
            raise ValueError("Command list cannot be empty")
        encoded = "".join(str(value) for value in command_list)
        tx_valid = VAEM_SERIAL_REGEX["tx_write"].match(encoded) or VAEM_SERIAL_REGEX["tx_read"].match(encoded)
        if not tx_valid:
            raise ValueError(f"Invalid serial command format: {encoded!r}")
        logger.debug("ASCII encoded command: %r", encoded)
        return encoded

    def _ascii_to_list(self, decoded_response_string: str) -> list:
        """
        Normalize and validate a serial ASCII response telegram.

        Args:
            decoded_response_string (str): Decoded response payload from serial interface.

        Returns:
            list: Tokenized response components (e.g., ["R", "U", "32", ":", "I", "7", "S", "1", "E", "0", "V", "1000"]).

        Raises:
            ValueError: Response is empty or does not match expected VAEM syntax.
        """
        logger.debug("VAEMSerial._ascii_to_list called with response=%r", decoded_response_string)
        normalized = decoded_response_string.strip()
        if not normalized:
            raise ValueError("Empty serial response")
        message = normalized.splitlines()[0].strip()

        read_match = VAEM_SERIAL_REGEX["rx_read"].match(message)
        write_match = VAEM_SERIAL_REGEX["rx_write"].match(message)
        m = read_match if read_match is not None else write_match
        if m is None:
            raise ValueError(f"Invalid serial response format: {message!r}")
        g = m.groupdict()
        tokens: list = [
            g["access"],
            "U",
            g["data_type"],
            ":",
        ]
        if g.get("index") is not None and g.get("subindex") is not None:
            tokens += ["I", g["index"], "S", g["subindex"]]
        tokens += ["E", g["error_code"]]
        if g.get("transfer_value") is not None:
            tokens += ["V", g["transfer_value"]]

        logger.debug("Parsed serial response tokens: %s", tokens)
        return tokens

    def _construct_frame(self, data: dict) -> list:
        """
        Constructs data frame for transfer to VAEM device.

        Args:
            data (dict): Data to be sent to VAEM device
        Returns:
            string of values to be passed as the expected data type of the Modbus data frame
        """
        logger.debug(
            "VAEMSerial._construct_frame called with access=%s index=%s sub_index=%s data_type=%s",
            data.get("access"),
            data.get("paramIndex"),
            data.get("paramSubIndex"),
            data.get("dataType"),
        )
        match data["dataType"]:
            case 1:
                data["dataType"] = "08"
            case 2:
                data["dataType"] = "16"
            case 3:
                data["dataType"] = "32"
            case 4:
                data["dataType"] = "64"
            case _:
                raise ValueError(f"Unspecified data type: {data['dataType']}")

        match data["access"]:
            case 0:
                frame = [
                    "R",
                    "U",
                    data["dataType"],
                    ":",
                    "I",
                    data["paramIndex"],
                    "S",
                    data["paramSubIndex"],
                    "\r",
                ]
            # pattern = "{access:l}U{data_type:d}:I{param_index:d}S{param_sub_index:d}V{transfer_value:d}<CR>"
            # data_string = "WU32:I7S1V1000<CR>"
            # parsed = parse(pattern, data_string)
            # "WU32:I7S1V1000<CR>"
            case 1:
                frame = [
                    "W",
                    "U",
                    data["dataType"],
                    ":",
                    "I",
                    data["paramIndex"],
                    "S",
                    data["paramSubIndex"],
                    "V",
                    data["transferValue"],
                    "\r",
                ]
            case _:
                raise ValueError(f"Unknown access type: {data['access']}")

        logger.debug("Constructed serial frame: %s", frame)
        return frame

    def _deconstruct_frame(self, frame) -> dict | None:
        """
        Deconstructs incoming tokenized data frame from VAEM device.

        Args:
            frame (list): Tokenized response components from _ascii_to_list.

        Returns:
            dict: Dictionary containing access, errorRet, and transferValue (if applicable).

        Raises:
            ValueError: Unable to parse frame or invalid token structure.
        """
        logger.debug("VAEMSerial._deconstruct_frame called with frame=%r", frame)
        data = {}

        # Frame layout from _ascii_to_list (index/subindex are optional in device replies):
        #   read:  ["R", "U", dtype, ":", ("I", index, "S", subindex,)? "E", error, "V", value]
        #   write: ["W", "U", dtype, ":", ("I", index, "S", subindex,)? "E", error]
        if not frame:
            logger.warning("Empty data frame received, potential operation error state detected: %s", frame)
            return None

        if not isinstance(frame, list) or "E" not in frame:
            raise ValueError(f"Unable to parse serial frame: {frame!r}")

        access_field = frame[0]  # "R" or "W"
        data["errorRet"] = int(frame[frame.index("E") + 1])

        if access_field == "R":
            data["access"] = VaemAccess.READ.value
            if "V" in frame:
                data["transferValue"] = int(frame[frame.index("V") + 1])
            logger.info("Returned Value: %s", data.get("transferValue"))
            logger.info("Returned error: %s", data["errorRet"])
            return data

        if access_field == "W":
            data["access"] = VaemAccess.WRITE.value
            logger.debug("Parsed write response with errorRet=%s", data["errorRet"])
            logger.info("Returned error: %s", data["errorRet"])
            return data

        raise ValueError(f"Unable to parse serial frame: {frame!r}")

    def _transfer(self, write_data: list) -> list:
        """
        Method of transferring information from Python driver to device.

        Args:
            write_data: List of data that will be transferred to VAEM device
        Returns:
            Response from VAEM device.
        """
        parsed = []
        logger.debug("VAEMSerial._transfer called with write_data=%s", write_data)
        try:
            encoded = self._list_to_ascii(write_data)
            logger.debug("BYTES: %s", list(encoded))

            self.client.reset_input_buffer()
            self.client.buffer = bytearray()
            logger.debug("Serial input buffer cleared")

            bytes_written = self.client.write(encoded.encode("ascii"))
            logger.debug("Serial write returned code: %s", bytes_written)
            self.client.flush()
            logger.debug("Serial bytes written and flushed")

            # Plan B: stream the response line by line within an overall deadline.
            # The device may emit non-telegram lines (a lone CR, prompt char,
            # blanks) before the real reply, so keep reading until the matching
            # telegram is parsed, then stop immediately for minimal latency.
            #
            # The device reply echoes the access type ("R"/"W") and the data type
            # ("08"/"16"/"32"/"64") but NOT the register index/subindex, so we
            # match on access + data type and rely on the synchronous,
            # buffer-flushed exchange for register alignment. Any stale or
            # mismatched frame is ignored; if no match arrives we return [] so the
            # caller sees "no response" rather than a wrong value.
            expected_access = write_data[0] if write_data else None
            expected_dtype = write_data[2] if len(write_data) > 2 else None
            deadline = time.monotonic() + (self.client.timeout or 1.0)
            while time.monotonic() < deadline:
                raw = self.client.readline(eol=b"\r")
                if not raw:
                    break  # read timed out with no more data
                try:
                    decoded = raw.decode("ascii")
                except UnicodeDecodeError:
                    continue
                try:
                    tokens = self._ascii_to_list(decoded)
                except ValueError:
                    # Echo/prompt/blank line - keep streaming.
                    continue
                if tokens[0] == expected_access and tokens[2] == expected_dtype:
                    parsed = tokens
                    break
            logger.debug("Parsed serial response: %s", parsed)
        except Exception as error:
            logger.error("Transfer error: %s", str(error))
        return parsed

    # def _read_lines(self) -> list:
    #     """Blah."""
    #     next_line = "True"
    #     responses = []
    #     while next_line:
    #         responses.append(next_line)
    #         next_line = self.reader.readline()
    #     return responses

    def close_client(self) -> None:
        """
        Closes the serial client connection.

        Typical usage example:
            vaem.close_client()

        Args:
            None

        Returns:
            None
        """
        logger.debug("VAEMSerial.close_client called")
        try:
            if self.client and self.client.is_open:
                self.client.close()
                logger.info("Serial connection closed successfully.")
            else:
                logger.debug("Serial connection already closed or not initialized")
        except Exception as error:
            logger.error("Error occurred while closing serial connection: %s", str(error))
