"""
VAEM Serial Communication Module.

This module provides a dedicated serial communication implementation
for the VAEM valve control module using PySerial over RS-232/RS-485.

Typical usage example:
    vaem_serial_config = VAEMSerialConfig(
        interface="serial",
        com_port="COM3",
        baudrate=9600,
        unit_id=1
    )

    serial_comm = VAEMSerialCommunication(config=vaem_serial_config)
"""

import logging
import struct
import time
from typing import Optional

import serial

from .vaem_config import VAEMSerialConfig
from .vaem_helper import (
    VaemAccess,
    VaemControlWords,
    VaemDataType,
    VaemIndex,
    VaemOperatingMode,
    vaemValveIndex,
)

logger = logging.getLogger(__name__)


class VAEMSerialCommunication:
    """
    VAEM Serial Communication Handler.

    This class manages serial communication with VAEM devices
    over serial interfaces (RS-232, RS-485) using PySerial.

    Attributes:
        serial_port (serial.Serial): PySerial port instance
        _config (VAEMSerialConfig): Configuration for serial communication
        _init_done (bool): Flag indicating successful initialization
        error_handling_enabled (int): Error handling state (1=enabled, 0=disabled)
        active_valves (list): Tracking array for valve selection states
    """

    def __init__(self, config: VAEMSerialConfig, timeout: float = 1.0, retry_count: int = 3):
        """
        Initialize VAEM Serial Communication handler.

        Args:
            config (VAEMSerialConfig): Serial configuration with port and baudrate settings
            timeout (float): Communication timeout in seconds (default: 1.0)
            retry_count (int): Number of retries for failed operations (default: 3)

        Raises:
            TypeError: Config is not VAEMSerialConfig instance
            RuntimeError: Failed to initialize serial connection
            ValueError: Invalid configuration parameters
        """
        if not isinstance(config, VAEMSerialConfig):
            config_type = type(config)
            raise TypeError(f"Error: Config does not match the Serial backend. The type passed in was: {config_type}")

        self._config = config
        self.timeout = timeout
        self.retry_count = retry_count
        self._init_done = False
        self.error_handling_enabled = 1
        self.active_valves = [0, 0, 0, 0, 0, 0, 0, 0]
        self.serial_port = None

        self._initialize_serial_connection()

    def _initialize_serial_connection(self) -> None:
        """
        Initialize serial connection to VAEM device.

        Sets up PySerial port with configured parameters and establishes connection.

        Raises:
            RuntimeError: Unable to create or connect to serial port
        """
        try:
            logger.info(
                "Initializing VAEM Serial Connection on %s at %d baud",
                self._config.com_port,
                self._config.baudrate,
            )

            # Create and open serial port
            self.serial_port = serial.Serial(
                port=self._config.com_port,
                baudrate=self._config.baudrate,
                timeout=self.timeout,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
            )

            if not self.serial_port.is_open:
                raise RuntimeError(f"Failed to open serial port {self._config.com_port}")

            logger.info("Serial connection established successfully")

            # Small delay to allow device to initialize
            time.sleep(0.1)

            # Run VAEM initialization procedure
            self._vaem_init()
            self._init_done = True

        except (RuntimeError, serial.SerialException) as e:
            logger.error("Serial connection initialization failed: %s", str(e))
            self._init_done = False
            raise RuntimeError(f"Failed to initialize serial connection: {e}") from e

    def _vaem_init(self) -> None:
        """
        Perform VAEM device initialization.

        Sets operating mode to OPMODE1 and clears any existing errors.

        Raises:
            RuntimeError: Communication error during initialization
        """
        try:
            logger.debug("Running VAEM initialization sequence")

            # Set operating mode to OPMODE1
            data = {
                "access": VaemAccess.WRITE.value,
                "dataType": VaemDataType.UINT8.value,
                "paramIndex": VaemIndex.OPERATINGMODE.value,
                "paramSubIndex": 0,
                "errorRet": 0,
                "transferValue": VaemOperatingMode.OPMODE1.value,
            }

            self._transfer_data(data)
            time.sleep(0.05)

            # Clear any existing errors
            self.clear_error()
            logger.debug("VAEM initialization sequence completed")

        except RuntimeError as e:
            logger.error("VAEM initialization failed: %s", str(e))
            raise

    def _construct_frame(self, data: dict) -> bytes:
        """
        Construct serial frame for transmission to VAEM device.

        Converts data dictionary into binary frame with proper formatting.

        Args:
            data (dict): Data dictionary containing:
                - access: Read/Write operation type
                - dataType: Data type specification
                - paramIndex: Parameter index
                - paramSubIndex: Parameter sub-index
                - errorRet: Error return code
                - transferValue: Data value to transfer

        Returns:
            bytes: Binary frame ready for transmission

        Raises:
            ValueError: Invalid data format or values
        """
        try:
            # Pack data into binary format
            frame = struct.pack(
                ">BBHBBQ",
                data["access"],
                data["dataType"],
                data["paramIndex"],
                data["paramSubIndex"],
                data["errorRet"],
                data["transferValue"],
            )

            logger.debug("Frame constructed: %s", frame.hex())
            return frame

        except (ValueError, struct.error) as e:
            logger.error("Frame construction failed: %s", str(e))
            raise ValueError(f"Unable to construct frame: {e}") from e

    def _deconstruct_frame(self, frame: bytes) -> dict:
        """
        Deconstruct incoming serial frame from VAEM device.

        Converts binary frame back into data dictionary.

        Args:
            frame (bytes): Binary frame received from device

        Returns:
            dict: Deconstructed data containing:
                - access: Operation type
                - dataType: Data type
                - paramIndex: Parameter index
                - paramSubIndex: Parameter sub-index
                - errorRet: Error return code
                - transferValue: Received data value

        Raises:
            ValueError: Invalid frame format
        """
        if frame is None or len(frame) < 12:
            logger.error("Invalid frame received: %s", frame.hex() if frame else "None")
            raise ValueError("Invalid frame format")

        try:
            # Unpack binary data
            access, datatype, param_index, param_sub_index, error_ret, transfer_value = struct.unpack(
                ">BBHBBQ",
                frame,
            )

            data = {
                "access": access,
                "dataType": datatype,
                "paramIndex": param_index,
                "paramSubIndex": param_sub_index,
                "errorRet": error_ret,
                "transferValue": transfer_value,
            }

            logger.debug("Frame deconstructed: %s", data)
            return data

        except (struct.error, ValueError) as e:
            logger.error("Frame deconstruction failed: %s", str(e))
            raise ValueError(f"Unable to deconstruct frame: {e}") from e

    def _transfer_data(self, data: dict, retry: bool = True) -> Optional[dict]:
        """
        Transfer data to VAEM device via serial connection.

        Implements retry logic for improved reliability over serial connections.

        Args:
            data (dict): Data to be transferred to VAEM
            retry (bool): Whether to retry on failure (default: True)

        Returns:
            dict: Deconstructed response frame, or None if transfer failed

        Raises:
            RuntimeError: Device not initialized or communication error
        """
        if not self._init_done:
            logger.warning("VAEM device not initialized - cannot perform transfer")
            raise RuntimeError("VAEM device not initialized")

        if self.serial_port is None or not self.serial_port.is_open:
            logger.error("Serial port not open")
            raise RuntimeError("Serial port is not open")

        frame = self._construct_frame(data)
        attempt = 0

        while attempt < self.retry_count:
            try:
                # Clear any pending data in buffer
                self.serial_port.reset_input_buffer()

                # Send frame
                logger.debug("Sending frame: %s", frame.hex())
                self.serial_port.write(frame)
                self.serial_port.flush()

                # Read response
                response_frame = self.serial_port.read(12)

                if len(response_frame) < 12:
                    raise RuntimeError("Incomplete response from device")

                logger.debug("Received frame: %s", response_frame.hex())
                response_data = self._deconstruct_frame(response_frame)

                logger.debug("Data transferred successfully on attempt %d", attempt + 1)
                return response_data

            except (RuntimeError, ValueError) as e:
                attempt += 1
                logger.warning(
                    "Transfer attempt %d/%d failed: %s",
                    attempt,
                    self.retry_count,
                    str(e),
                )

                if attempt >= self.retry_count:
                    logger.error("Failed to transfer data after %d attempts", self.retry_count)
                    raise RuntimeError(f"Communication failed after {self.retry_count} attempts: {e}") from e

                # Brief delay before retry
                time.sleep(0.1)

        return None

    def _get_transfer_value(
        self,
        operation: int,
        index: VaemIndex,
        sub_index: int = 0,
        transfer_value: Optional[int] = None,
    ) -> dict:
        """
        Generate transfer value dictionary for VAEM operation.

        Constructs a properly formatted data dictionary based on operation type,
        index, and other parameters.

        Args:
            operation (int): Access type (READ or WRITE)
            index (VaemIndex): VAEM index enumeration
            sub_index (int): Sub-index value (default: 0)
            transfer_value (int): Value to transfer (default: None)

        Returns:
            dict: Formatted transfer value dictionary

        Raises:
            ValueError: Invalid index or operation type
        """
        out = {
            "access": operation,
            "paramIndex": index.value,
            "paramSubIndex": sub_index,
            "errorRet": 0,
            "dataType": VaemDataType.UINT16.value,
            "transferValue": transfer_value or 0,
        }

        # Adjust data type and sub-index based on parameter index
        match index.value:
            case 0x07 | 0x08 | 0x16 | 0x2E:
                # Response time parameters (32-bit)
                out["dataType"] = VaemDataType.UINT32.value
            case 0x09 | 0x2D:
                # Operating mode (8-bit)
                out["dataType"] = VaemDataType.UINT8.value
            case 0x13:
                # Valve selection (8-bit, special handling)
                out["dataType"] = VaemDataType.UINT8.value
                out["paramSubIndex"] = 0
                out["transferValue"] = sub_index
            case 0x01 | 0x02 | 0x04 | 0x05 | 0x06 | 0x11:
                # Standard 16-bit parameters
                pass
            case _:
                logger.warning("Potentially unsupported index: 0x%02X", index.value)

        return out

    def _get_status(self, status_word: int) -> dict:
        """
        Parse VAEM status word into individual status flags.

        Extracts individual status bits from the 16-bit status word.

        Args:
            status_word (int): 16-bit status word from VAEM

        Returns:
            dict: Dictionary of parsed status flags:
                - Status: Overall device status
                - Error: Error flag
                - Readiness: Device readiness
                - OperatingMode: Current operating mode
                - Valve1-8: Individual valve states
        """
        status = {
            "Status": status_word & 0x01,
            "Error": (status_word & 0x08) >> 3,
            "Readiness": (status_word & 0x10) >> 4,
            "OperatingMode": (status_word & 0xC0) >> 6,
            "Valve1": (status_word & 0x100) >> 8,
            "Valve2": (status_word & 0x200) >> 9,
            "Valve3": (status_word & 0x400) >> 10,
            "Valve4": (status_word & 0x800) >> 11,
            "Valve5": (status_word & 0x1000) >> 12,
            "Valve6": (status_word & 0x2000) >> 13,
            "Valve7": (status_word & 0x4000) >> 14,
            "Valve8": (status_word & 0x8000) >> 15,
        }
        return status

    def select_valve(self, valve_id: int) -> None:
        """
        Select a valve for subsequent operations.

        Args:
            valve_id (int): Valve ID to select (1-8)

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            logger.error("Invalid valve ID: %d (valid range: 1-8)", valve_id)
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            # Read current selection state
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.SELECTVALVE,
                vaemValveIndex[valve_id],
            )
            response = self._transfer_data(data)

            # Add new valve to selection
            current_selection = response["transferValue"]
            new_selection = vaemValveIndex[valve_id] | current_selection

            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.SELECTVALVE,
                new_selection,
            )
            self._transfer_data(data)
            self.active_valves[valve_id - 1] = 1
            logger.info("Valve %d selected", valve_id)

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to select valve %d: %s", valve_id, str(e))
            raise

    def deselect_valve(self, valve_id: int) -> None:
        """
        Deselect a valve.

        Args:
            valve_id (int): Valve ID to deselect (1-8)

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            logger.error("Invalid valve ID: %d (valid range: 1-8)", valve_id)
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            # Read current selection state
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.SELECTVALVE,
                vaemValveIndex[valve_id],
            )
            response = self._transfer_data(data)

            # Remove valve from selection
            current_selection = response["transferValue"]
            new_selection = current_selection & (~vaemValveIndex[valve_id])

            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.SELECTVALVE,
                new_selection,
            )
            self._transfer_data(data)
            self.active_valves[valve_id - 1] = 0
            logger.info("Valve %d deselected", valve_id)

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to deselect valve %d: %s", valve_id, str(e))
            raise

    def open_selected_valves(self) -> None:
        """
        Open all selected valves.

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        try:
            # Determine control word based on error handling setting
            control_value = (
                VaemControlWords.STARTVALVES.value
                if self.error_handling_enabled
                else VaemControlWords.STARTVALVESRESETERROR.value
            )

            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                control_value,
            )
            self._transfer_data(data)

            # Reset control word
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.RESETERRORS.value,
            )
            self._transfer_data(data)
            self.clear_error()
            logger.info("Selected valves opened")

        except RuntimeError as e:
            logger.error("Failed to open selected valves: %s", str(e))
            raise

    def close_valves(self) -> None:
        """
        Close previously opened valves.

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.STOPVALVES.value,
            )
            self._transfer_data(data)
            self.clear_error()
            logger.info("Valves closed")

        except RuntimeError as e:
            logger.error("Failed to close valves: %s", str(e))
            raise

    def get_status(self) -> dict:
        """
        Read device status.

        Returns:
            dict: Status dictionary with individual status flags

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.STATUSWORD,
                0,
                0,
            )
            response = self._transfer_data(data)
            status = self._get_status(response["transferValue"])
            logger.debug("Device status: %s", status)
            return status

        except RuntimeError as e:
            logger.error("Failed to get device status: %s", str(e))
            raise

    def clear_error(self) -> None:
        """
        Clear device error flags.

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CONTROLWORD,
                0,
                VaemControlWords.RESETERRORS.value,
            )
            self._transfer_data(data)
            logger.debug("Device errors cleared")

        except RuntimeError as e:
            logger.error("Failed to clear errors: %s", str(e))
            raise

    def set_valve_switching_time(self, valve_id: int, opening_time: int) -> None:
        """
        Set valve switching time.

        Args:
            valve_id (int): Valve ID (1-8)
            opening_time (int): Opening time in milliseconds

        Raises:
            ValueError: Invalid valve ID or opening time
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            logger.error("Invalid valve ID: %d", valve_id)
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            # Convert milliseconds to device units (0.2ms per unit)
            switching_time_units = int(opening_time / 0.2)

            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.SWITCHINGTIME,
                valve_id - 1,
                switching_time_units,
            )
            self._transfer_data(data)
            logger.info("Valve %d switching time set to %d ms", valve_id, opening_time)

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to set switching time for valve %d: %s", valve_id, str(e))
            raise

    def get_valve_switching_time(self, valve_id: int) -> Optional[int]:
        """
        Get valve switching time.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Switching time in milliseconds, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            logger.error("Invalid valve ID: %d", valve_id)
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.SWITCHINGTIME,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            # Convert back to milliseconds (multiply by 0.2)
            switching_time_ms = int(response["transferValue"] * 0.2)
            logger.debug("Valve %d switching time: %d ms", valve_id, switching_time_ms)
            return switching_time_ms

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get switching time for valve %d: %s", valve_id, str(e))
            raise

    def set_inrush_current(self, valve_id: int, inrush_current: int) -> None:
        """
        Set valve inrush current.

        Args:
            valve_id (int): Valve ID (1-8)
            inrush_current (int): Inrush current in mA (20-1000)

        Raises:
            ValueError: Invalid valve ID or current value
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        if inrush_current not in range(20, 1001):
            raise ValueError(f"Inrush current {inrush_current} out of range (20-1000 mA)")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.INRUSHCURRENT,
                valve_id - 1,
                inrush_current,
            )
            self._transfer_data(data)
            logger.info("Valve %d inrush current set to %d mA", valve_id, inrush_current)

        except RuntimeError as e:
            logger.error("Failed to set inrush current for valve %d: %s", valve_id, str(e))
            raise

    def get_inrush_current(self, valve_id: int) -> Optional[int]:
        """
        Get valve inrush current.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Inrush current in mA, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            logger.warning("Device not initialized")
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.INRUSHCURRENT,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            inrush_current = response["transferValue"]
            logger.debug("Valve %d inrush current: %d mA", valve_id, inrush_current)
            return inrush_current

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get inrush current for valve %d: %s", valve_id, str(e))
            raise

    def set_holding_current(self, valve_id: int, holding_current: int) -> None:
        """
        Set valve holding current.

        Args:
            valve_id (int): Valve ID (1-8)
            holding_current (int): Holding current in mA (20-400)

        Raises:
            ValueError: Invalid valve ID or current value
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        if holding_current not in range(20, 401):
            raise ValueError(f"Holding current {holding_current} out of range (20-400 mA)")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.HOLDINGCURRENT,
                valve_id - 1,
                holding_current,
            )
            self._transfer_data(data)
            logger.info("Valve %d holding current set to %d mA", valve_id, holding_current)

        except RuntimeError as e:
            logger.error("Failed to set holding current for valve %d: %s", valve_id, str(e))
            raise

    def get_holding_current(self, valve_id: int) -> Optional[int]:
        """
        Get valve holding current.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Holding current in mA, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.HOLDINGCURRENT,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            holding_current = response["transferValue"]
            logger.debug("Valve %d holding current: %d mA", valve_id, holding_current)
            return holding_current

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get holding current for valve %d: %s", valve_id, str(e))
            raise

    def set_nominal_voltage(self, valve_id: int, voltage: int) -> None:
        """
        Set valve nominal voltage.

        Args:
            valve_id (int): Valve ID (1-8)
            voltage (int): Nominal voltage in mV (8000-24000)

        Raises:
            ValueError: Invalid valve ID or voltage value
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        if voltage not in range(8000, 24001):
            raise ValueError(f"Voltage {voltage} out of range (8000-24000 mV)")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.NOMINALVOLTAGE,
                valve_id - 1,
                voltage,
            )
            self._transfer_data(data)
            logger.info("Valve %d nominal voltage set to %d mV", valve_id, voltage)

        except RuntimeError as e:
            logger.error("Failed to set nominal voltage for valve %d: %s", valve_id, str(e))
            raise

    def get_nominal_voltage(self, valve_id: int) -> Optional[int]:
        """
        Get valve nominal voltage.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Nominal voltage in mV, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.NOMINALVOLTAGE,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            voltage = response["transferValue"]
            logger.debug("Valve %d nominal voltage: %d mV", valve_id, voltage)
            return voltage

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get nominal voltage for valve %d: %s", valve_id, str(e))
            raise

    def set_delay_time(self, valve_id: int, delay_time: int) -> None:
        """
        Set valve delay time.

        Args:
            valve_id (int): Valve ID (1-8)
            delay_time (int): Delay time in milliseconds

        Raises:
            ValueError: Invalid valve ID or delay time
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.TIMEDELAY,
                valve_id - 1,
                delay_time,
            )
            self._transfer_data(data)
            logger.info("Valve %d delay time set to %d ms", valve_id, delay_time)

        except RuntimeError as e:
            logger.error("Failed to set delay time for valve %d: %s", valve_id, str(e))
            raise

    def get_delay_time(self, valve_id: int) -> Optional[int]:
        """
        Get valve delay time.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Delay time in milliseconds, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.TIMEDELAY,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            delay_time = response["transferValue"]
            logger.debug("Valve %d delay time: %d ms", valve_id, delay_time)
            return delay_time

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get delay time for valve %d: %s", valve_id, str(e))
            raise

    def set_pickup_time(self, valve_id: int, pickup_time: int) -> None:
        """
        Set valve pickup time.

        Args:
            valve_id (int): Valve ID (1-8)
            pickup_time (int): Pickup time in milliseconds

        Raises:
            ValueError: Invalid valve ID or pickup time
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.PICKUPTIME,
                valve_id - 1,
                pickup_time,
            )
            self._transfer_data(data)
            logger.info("Valve %d pickup time set to %d ms", valve_id, pickup_time)

        except RuntimeError as e:
            logger.error("Failed to set pickup time for valve %d: %s", valve_id, str(e))
            raise

    def get_pickup_time(self, valve_id: int) -> Optional[int]:
        """
        Get valve pickup time.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Pickup time in milliseconds, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.PICKUPTIME,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            pickup_time = response["transferValue"]
            logger.debug("Valve %d pickup time: %d ms", valve_id, pickup_time)
            return pickup_time

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get pickup time for valve %d: %s", valve_id, str(e))
            raise

    def set_current_reduction_time(self, valve_id: int, reduction_time: int) -> None:
        """
        Set valve current reduction time.

        Args:
            valve_id (int): Valve ID (1-8)
            reduction_time (int): Reduction time in milliseconds

        Raises:
            ValueError: Invalid valve ID or reduction time
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                valve_id - 1,
                reduction_time,
            )
            self._transfer_data(data)
            logger.info("Valve %d current reduction time set to %d ms", valve_id, reduction_time)

        except RuntimeError as e:
            logger.error("Failed to set current reduction time for valve %d: %s", valve_id, str(e))
            raise

    def get_current_reduction_time(self, valve_id: int) -> Optional[int]:
        """
        Get valve current reduction time.

        Args:
            valve_id (int): Valve ID (1-8)

        Returns:
            int: Current reduction time in milliseconds, or None if read failed

        Raises:
            ValueError: Invalid valve ID
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if valve_id not in range(1, 9):
            raise ValueError(f"Valve index out of bounds: {valve_id}")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.CURRENTREDUCTIONTIME,
                valve_id - 1,
                0,
            )
            response = self._transfer_data(data)
            reduction_time = response["transferValue"]
            logger.debug("Valve %d current reduction time: %d ms", valve_id, reduction_time)
            return reduction_time

        except (ValueError, RuntimeError) as e:
            logger.error("Failed to get current reduction time for valve %d: %s", valve_id, str(e))
            raise

    def set_error_handling(self, activate: int) -> None:
        """
        Enable or disable error handling.

        Args:
            activate (int): 1 to enable, 0 to disable

        Raises:
            ValueError: Invalid activate value
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        if activate not in (0, 1):
            raise ValueError(f"Activate value must be 0 or 1, got {activate}")

        try:
            data = self._get_transfer_value(
                VaemAccess.WRITE.value,
                VaemIndex.ERRORHANDLING,
                0,
                activate,
            )
            self._transfer_data(data)
            self.error_handling_enabled = activate
            logger.info("Error handling %s", "enabled" if activate else "disabled")

        except RuntimeError as e:
            logger.error("Failed to set error handling: %s", str(e))
            raise

    def get_error_handling_status(self) -> Optional[int]:
        """
        Get error handling status.

        Returns:
            int: 1 if enabled, 0 if disabled, or None if read failed

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        try:
            data = self._get_transfer_value(
                VaemAccess.READ.value,
                VaemIndex.ERRORHANDLING,
                0,
                0,
            )
            response = self._transfer_data(data)
            status = response["transferValue"]
            logger.debug("Error handling status: %s", "enabled" if status else "disabled")
            return status

        except RuntimeError as e:
            logger.error("Failed to get error handling status: %s", str(e))
            raise

    def save_settings(self) -> None:
        """
        Save all parameters to non-volatile memory.

        Raises:
            RuntimeError: Device not initialized
        """
        if not self._init_done:
            raise RuntimeError("VAEM device not initialized")

        try:
            data = {
                "access": VaemAccess.WRITE.value,
                "dataType": VaemDataType.UINT32.value,
                "paramIndex": VaemIndex.SAVEPARAMETERS.value,
                "paramSubIndex": 0,
                "errorRet": 0,
                "transferValue": 99999,
            }
            self._transfer_data(data)
            logger.info("Settings saved to non-volatile memory")

        except RuntimeError as e:
            logger.error("Failed to save settings: %s", str(e))
            raise

    def disconnect(self) -> None:
        """
        Close serial connection to VAEM device.

        Safely disconnects from the device and cleans up resources.
        """
        try:
            if self.serial_port is not None and self.serial_port.is_open:
                self.serial_port.close()
                self._init_done = False
                logger.info("Serial connection closed")
        except Exception as e:
            logger.error("Error closing connection: %s", str(e))

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.disconnect()
