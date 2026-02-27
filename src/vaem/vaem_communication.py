"""
Festo VAEM backend communication module.

This module handles all communication underneath the hood
 and abstracting it all from the user.
"""

import logging
import struct
from abc import ABC, abstractmethod

from pymodbus.client import ModbusBaseClient, ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException, ModbusIOException

from .vaem_config import VAEMConfig, VAEMSerialConfig, VAEMTCPConfig
from .vaem_helper import (
    VaemAccess,
    VaemControlWords,
    VaemDataType,
    VaemIndex,
    VaemOperatingMode,
    vaemValveIndex,
)

logger = logging.getLogger(__name__)


class VAEMModbusClient(ABC):
    """Modbus Client Class."""

    @abstractmethod
    def __init__(self, config: VAEMConfig):
        """
        VAEMModbusClient constructor.

        Abstract base class to build out VAEM clients.

        Args:
            config (VAEMConfig): A ModbusTCP or ModbusSerial
                    type to allow the driver to connect to the
                    correct communication interface.

        Returns:
            None
        """
        self._config = config
        self.client = ModbusBaseClient
        self.version = None
        self._read_param = {
            "address": 0,
            "length": 0x07,
        }
        self._write_param = {
            "address": 0,
            "length": 0x07,
        }
        self._init_done = True
        self.error_handling_enabled = 1
        self.active_valves = [0, 0, 0, 0, 0, 0, 0, 0]

    def _get_transfer_value(self, operation, index, sub_index=0, transfer_value=None) -> dict:
        """
        Gets the transfer value for the VAEM operation.

        Args:
            operation: access
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
            case 0x01 | 0x02 | 0x04 | 0x05 | 0x06 | 0x11:
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

    def _deconstruct_frame(self, frame) -> dict:
        """
        Deconstructs incoming data frame from VAEM device.

        Args:
            frame: dict coming in from the device
        Returns:
            data: dictionary that contains the information from the dataframe.
        """
        data = {}
        if frame is not None:
            data["access"] = (frame[0] & 0xFF00) >> 8
            data["dataType"] = frame[0] & 0x00FF
            data["paramIndex"] = frame[1]
            data["paramSubIndex"] = (frame[2] & 0xFF00) >> 8
            data["errorRet"] = frame[2] & 0x00FF
            data["transferValue"] = 0
            for i in range(4):
                data["transferValue"] += frame[len(frame) - 1 - i] << (i * 16)

        return data

    def _transfer(self, write_data: list):
        """
        Method of transferring information from Python driver to device.

        Args:
            write_data: List of data that will be transferred to VAEM device
        Returns:
            Response from VAEM device.
        """
        data = 0
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
            return data.registers
        except ModbusException as modbus_error:
            logger.error("Something went wrong with read opperation VAEM : %s", str(modbus_error))
        return None

    def _vaem_init(self):
        """
        Runs an additional vaem initialization process to configure.

        the correct read and write for the driver.
        """
        data = {}
        frame = []

        if self._init_done:
            try:
                # set operating mode
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.OPERATINGMODE,
                    0,
                    VaemOperatingMode.OPMODE1.value,
                )
                frame = self._construct_frame(data)
                self._transfer(frame)
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
        frame = []
        if self._init_done:
            # save settings
            data["access"] = VaemAccess.WRITE.value
            data["dataType"] = VaemDataType.UINT32.value
            data["paramIndex"] = VaemIndex.SAVEPARAMETERS.value
            data["paramSubIndex"] = 0
            data["errorRet"] = 0
            data["transferValue"] = 99999
            frame = self._construct_frame(data)
            self._transfer(frame)
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
        data = {}
        if self._init_done:
            if valve_id in range(1, 9):
                # get currently selected valves
                data = self._get_transfer_value(
                    VaemAccess.READ.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id],
                )
                frame = self._construct_frame(data)
                resp = self._transfer(frame)
                # select new valve
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id] | self._deconstruct_frame(resp)["transferValue"],
                )
                frame = self._construct_frame(data)
                self._transfer(frame)
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
        data = {}
        if self._init_done:
            if valve_id in range(1, 9):
                # get currently selected valves
                data = self._get_transfer_value(
                    VaemAccess.READ.value,
                    VaemIndex.SELECTVALVE,
                    vaemValveIndex[valve_id],
                )
                frame = self._construct_frame(data)
                resp = self._transfer(frame)
                # deselect new valve
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SELECTVALVE,
                    self._deconstruct_frame(resp)["transferValue"] & (~(vaemValveIndex[valve_id])),
                )
                frame = self._construct_frame(data)
                self._transfer(frame)
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
        data = {}
        if self._init_done:
            opening_time = int(opening_time / 0.2)
            if (opening_time in range(0, 9999999999999)) and (valve_id in range(1, 9)):
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.SWITCHINGTIME,
                    (valve_id - 1),
                    int(opening_time),
                )
                frame = self._construct_frame(data)
                self._transfer(frame)
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
        data = {}
        if self._init_done:
            # save settings
            if self.error_handling_enabled:
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.CONTROLWORD,
                    0,
                    VaemControlWords.STARTVALVES.value,
                )
            else:
                data = self._get_transfer_value(
                    VaemAccess.WRITE.value,
                    VaemIndex.CONTROLWORD,
                    0,
                    VaemControlWords.STARTVALVESRESETERROR.value,
                )
            frame = self._construct_frame(data)
            self._transfer(frame)

            # reset the control word
            data = self._get_transfer_value(
                VaemAccess.WRITE.value, VaemIndex.CONTROLWORD, 0, VaemControlWords.RESETERRORS.value
            )
            frame = self._construct_frame(data)
            self._transfer(frame)
            self.clear_error()
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
        data = {}
        if self._init_done:
            # save settings
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.STOPVALVES.value,
            )
            frame = self._construct_frame(data)
            self._transfer(frame)
            self.clear_error()
        else:
            logger.warning("No VAEM Connected!!")

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
        data = {}
        if self._init_done:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.STATUSWORD,
                0,
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            logger.info(self._get_status(self._deconstruct_frame(resp)["transferValue"]))
            return self._get_status(self._deconstruct_frame(resp)["transferValue"])
        logger.warning("No VAEM Connected!!")
        return {}

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
        data = {}
        if self._init_done:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.RESETERRORS.value,
            )
            frame = self._construct_frame(data)
            self._transfer(frame)
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            if inrush_current not in range(20, 1001):
                raise ValueError(
                    f"Error, input for inrush current was: {inrush_current}, inrush current ranges from 20, 1000 mA"
                )
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.INRUSHCURRENT,
                (valve_id - 1),
                int(inrush_current),
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.INRUSHCURRENT,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return self._deconstruct_frame(resp)["transferValue"]
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            if voltage not in range(8000, 24001):
                raise ValueError(f"Error, input voltage was: {voltage}, input voltage ranges from 8000-24000 mV")
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.NOMINALVOLTAGE,
                (valve_id - 1),
                voltage,
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.NOMINALVOLTAGE,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return self._deconstruct_frame(resp)["transferValue"]
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was: {valve_id}, IDs range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.SWITCHINGTIME,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return int(self._deconstruct_frame(resp)["transferValue"] * 0.2)
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.TIMEDELAY,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return int(self._deconstruct_frame(resp)["transferValue"] * 0.2)
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            delay_time = int(delay_time / 0.2)
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.TIMEDELAY,
                (valve_id - 1),
                delay_time,
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.PICKUPTIME,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return int(self._deconstruct_frame(resp)["transferValue"] * 0.2)
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            if pickup_time not in range(1, 501):
                raise ValueError(f"Error, input pickup time was {pickup_time} ms, This is out of the range of 1-500 ms")
            pickup_time = int(pickup_time / 0.2)
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.PICKUPTIME,
                (valve_id - 1),
                pickup_time,
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.HOLDINGCURRENT,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return self._deconstruct_frame(resp)["transferValue"]
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            if holding_current not in range(20, 401):
                raise ValueError(f"Error, input holding current out of range: {holding_current}")
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.HOLDINGCURRENT,
                (valve_id - 1),
                int(holding_current),
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                (valve_id - 1),
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return int(self._deconstruct_frame(resp)["transferValue"] * 0.2)
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
        data = {}
        if self._init_done:
            if valve_id not in range(1, 9):
                raise ValueError(f"Error, input valve ID was {valve_id}, ID's range from 1-8")
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                (valve_id - 1),
                int(reduction_time),
            )
            frame = self._construct_frame(data)
            self._transfer(frame)

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
        data = {}
        if self._init_done:
            if activate not in (0, 1):
                raise ValueError(f"Error, value inputted was {activate}, Either a 1 or 0 is accepted")
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.ERRORHANDLING,
                0,
                int(not activate),
            )
            frame = self._construct_frame(data)
            self._transfer(frame)
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
        data = {}
        if self._init_done:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.ERRORHANDLING,
                0,
                0,
            )
            frame = self._construct_frame(data)
            resp = self._transfer(frame)
            return int(not self._deconstruct_frame(resp)["transferValue"])
        return None


class VAEMModbusTCP(VAEMModbusClient):
    """VAEM Modbus TCP client class."""

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
            self._vaem_init()
            self.version = None
            self._read_param = {
                "address": 0,
                "length": 0x07,
            }
            self._write_param = {
                "address": 0,
                "length": 0x07,
            }
            self.active_valves = [0, 0, 0, 0, 0, 0, 0, 0]
        except ConnectionError as e:
            logger.error("Connection error: %s. ", str(e))
        except ModbusIOException as io_error:
            logger.error("Modbus IO error: %s. ", str(io_error))
            logger.info(self._config)


class VAEMModbusSerial(VAEMModbusClient):
    """Class used as the interface backend for using Serial communication."""

    def __init__(self, config: VAEMSerialConfig):
        """
        VAEMModbusSerial Constructor.

        Args:
            config (VAEMSerialConfig): A configuration class designated for ModbusSerial

        Returns:
            None

        Raises:
            NotImplementedError: Interface currently in development.
            TypeError: Config does not match serial interface specs.
            RuntimeError: A runtime error with the serial interface has occurred.
        """
        super().__init__(config)
        logger.error(
            """Modbus Serial backend is currently an experimental feature. \
            Attempting operation with this feature may result in unexpected or incorrect behavior. \
            This will be available as a fully supported feature in future releases."""
        )
        raise NotImplementedError(
            "Modbus Serial backend is not yet implemented. This will be available in future releases."
        )
        if not isinstance(config, VAEMSerialConfig):
            config_type = type(config)
            raise TypeError(
                f"""Error: Config does not match the ModbusSerial backend.
                            The type passed in was: {config_type}"""
            )
        try:
            self._config = config
            self.client = ModbusSerialClient(port=self._config.com_port, baudrate=self._config.baudrate)
        except RuntimeError as run_err:
            logger.error("Runtime error: %s. ", str(run_err))
