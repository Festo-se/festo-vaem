"""
Unit tests for VAEM communication module (vaem_communication.py).

This module contains tests for the low-level Modbus communication layer
including frame construction/deconstruction and device operations.
"""

import pytest
from vaem.vaem_communication import VAEMModbusTCP
from vaem.vaem_helper import VaemIndex, VaemDataType, VaemAccess


class TestVAEMModbusClientFrameConstruction:
    """Test frame construction for Modbus communication."""

    def test_construct_frame_basic(self, vaem_tcp_backend):
        """Test basic frame construction."""
        backend = vaem_tcp_backend
        data = {
            "access": 0,
            "dataType": 2,
            "paramIndex": 0x01,
            "paramSubIndex": 0,
            "errorRet": 0,
            "transferValue": 0,
        }
        frame = backend._construct_frame(data)
        assert isinstance(frame, list)
        assert len(frame) > 0

    def test_construct_frame_with_transfer_value(self, vaem_tcp_backend):
        """Test frame construction with transfer value."""
        backend = vaem_tcp_backend
        data = {
            "access": 1,
            "dataType": 2,
            "paramIndex": 0x05,
            "paramSubIndex": 0,
            "errorRet": 0,
            "transferValue": 150,
        }
        frame = backend._construct_frame(data)
        assert isinstance(frame, list)
        assert len(frame) > 0

    def test_construct_frame_multiple_calls(self, vaem_tcp_backend):
        """Test multiple frame constructions."""
        backend = vaem_tcp_backend
        for i in range(5):
            data = {
                "access": i % 2,
                "dataType": 2,
                "paramIndex": 0x01 + i,
                "paramSubIndex": 0,
                "errorRet": 0,
                "transferValue": 100 + i,
            }
            frame = backend._construct_frame(data)
            assert isinstance(frame, list)


class TestVAEMModbusClientFrameDeconstruction:
    """Test frame deconstruction from Modbus communication."""

    def test_deconstruct_frame_basic(self, vaem_tcp_backend):
        """Test basic frame deconstruction."""
        backend = vaem_tcp_backend
        # Create a mock frame response
        frame = [0x0002, 0x0001, 0x0000, 0x0000, 0x0096]  # Example frame
        data = backend._deconstruct_frame(frame)
        assert isinstance(data, dict)
        assert "access" in data
        assert "dataType" in data
        assert "paramIndex" in data
        assert "paramSubIndex" in data
        assert "errorRet" in data
        assert "transferValue" in data

    def test_deconstruct_frame_with_transfer_value(self, vaem_tcp_mock):
        """Test frame deconstruction with transfer value extraction."""
        backend = vaem_tcp_mock._backend
        frame = [0x0201, 0x0005, 0x0000, 0x0000, 0x0096]
        data = backend._deconstruct_frame(frame)
        assert data["transferValue"] is not None

    def test_deconstruct_frame_none_input(self, vaem_tcp_backend):
        """Test frame deconstruction with None input."""
        backend = vaem_tcp_backend
        data = backend._deconstruct_frame(None)
        assert isinstance(data, dict)
        assert data == {}


class TestVAEMModbusClientGetTransferValue:
    """Test transfer value generation for VAEM operations."""

    def test_get_transfer_value_read_operation(self, vaem_tcp_backend):
        """Test generating transfer value for read operation."""
        backend = vaem_tcp_backend
        result = backend._get_transfer_value(
            VaemAccess.READ.value,
            VaemIndex.STATUSWORD,
            0,
            0
        )
        assert result["access"] == VaemAccess.READ.value
        assert result["paramIndex"] == VaemIndex.STATUSWORD.value
        assert result["transferValue"] == 0

    def test_get_transfer_value_write_operation(self, vaem_tcp_backend):
        """Test generating transfer value for write operation."""
        backend = vaem_tcp_backend
        result = backend._get_transfer_value(
            VaemAccess.WRITE.value,
            VaemIndex.INRUSHCURRENT,
            0,
            150
        )
        assert result["access"] == VaemAccess.WRITE.value
        assert result["paramIndex"] == VaemIndex.INRUSHCURRENT.value
        assert result["transferValue"] == 150

    def test_get_transfer_value_uint32_datatype(self, vaem_tcp_backend):
        """Test transfer value with UINT32 data type."""
        backend = vaem_tcp_backend
        result = backend._get_transfer_value(
            VaemAccess.READ.value,
            VaemIndex.SWITCHINGTIME,
            0,
            0
        )
        assert result["dataType"] == VaemDataType.UINT32.value

    def test_get_transfer_value_uint8_datatype(self, vaem_tcp_backend):
        """Test transfer value with UINT8 data type."""
        backend = vaem_tcp_backend
        result = backend._get_transfer_value(
            VaemAccess.WRITE.value,
            VaemIndex.OPERATINGMODE,
            0,
            1
        )
        assert result["dataType"] == VaemDataType.UINT8.value

    def test_get_transfer_value_select_valve(self, vaem_tcp_backend):
        """Test transfer value for select valve operation."""
        backend = vaem_tcp_backend
        result = backend._get_transfer_value(
            VaemAccess.WRITE.value,
            VaemIndex.SELECTVALVE,
            1,  # valve index
            0
        )
        assert result["paramIndex"] == VaemIndex.SELECTVALVE.value
        assert result["transferValue"] == 1


class TestVAEMModbusClientStatusParsing:
    """Test status word parsing."""

    def test_get_status_basic(self, vaem_tcp_backend):
        """Test basic status word parsing."""
        backend = vaem_tcp_backend
        status_word = 0x01  # Status bit set
        status = backend._get_status(status_word)
        assert isinstance(status, dict)
        assert status["Status"] == 1

    def test_get_status_error_bit(self, vaem_tcp_backend):
        """Test error bit extraction from status word."""
        backend = vaem_tcp_backend
        status_word = 0x08  # Error bit set
        status = backend._get_status(status_word)
        assert status["Error"] == 1

    def test_get_status_readiness_bit(self, vaem_tcp_backend):
        """Test readiness bit extraction from status word."""
        backend = vaem_tcp_backend
        status_word = 0x10  # Readiness bit set
        status = backend._get_status(status_word)
        assert status["Readiness"] == 1

    def test_get_status_operating_mode(self, vaem_tcp_backend):
        """Test operating mode bits extraction."""
        backend = vaem_tcp_backend
        status_word = 0xC0  # Operating mode bits set
        status = backend._get_status(status_word)
        assert status["OperatingMode"] == 3

    def test_get_status_all_valves(self, vaem_tcp_backend):
        """Test extraction of all valve status bits."""
        backend = vaem_tcp_backend
        status_word = 0xFF00  # All valve bits set
        status = backend._get_status(status_word)
        for i in range(1, 9):
            assert status[f"Valve{i}"] == 1

    def test_get_status_all_bits_set(self, vaem_tcp_backend):
        """Test status parsing with all bits set."""
        backend = vaem_tcp_backend
        status_word = 0xFFFF  # All bits set
        status = backend._get_status(status_word)
        assert status["Status"] == 1
        assert status["Error"] == 1
        assert status["Readiness"] == 1
        assert all(status[f"Valve{i}"] == 1 for i in range(1, 9))


class TestVAEMModbusTCPInitialization:
    """Test TCP client initialization."""

    def test_tcp_client_valid_config(self, vaem_tcp_backend):
        """Test TCP client initializes with valid config."""
        assert isinstance(vaem_tcp_backend, VAEMModbusTCP)
        assert vaem_tcp_backend._config.ip == "192.168.0.1"
        assert vaem_tcp_backend._config.port == 502

    def test_tcp_client_invalid_config_type_error(self, mocker):
        """Test TCP client raises TypeError with invalid config."""
        invalid_config = "not_a_config"
        with pytest.raises(TypeError):
            VAEMModbusTCP(config=invalid_config)

    def test_tcp_client_attributes_initialized(self, vaem_tcp_mock):
        """Test TCP client attributes are properly initialized."""
        backend = vaem_tcp_mock._backend
        assert backend.client is not None
        assert backend._read_param is not None
        assert backend._write_param is not None
        assert backend.error_handling_enabled is not None
        assert backend.active_valves is not None


class TestVAEMModbusClientValveSelection:
    """Test valve selection operations."""

    def test_select_valve_valid_id(self, vaem_tcp_backend):
        """Test selecting a valid valve."""
        backend = vaem_tcp_backend
        backend.select_valve(valve_id=1)
        # Verify active valves list is updated
        assert backend.active_valves[0] == 1

    def test_select_valve_all_ids(self, vaem_tcp_mock):
        """Test selecting all valve IDs."""
        backend = vaem_tcp_mock._backend
        for valve_id in range(1, 9):
            backend.select_valve(valve_id=valve_id)
        # Verify all valves are marked as active
        assert all(valve == 1 for valve in backend.active_valves)

    def test_deselect_valve_valid_id(self, vaem_tcp_mock):
        """Test deselecting a valid valve."""
        backend = vaem_tcp_mock._backend
        backend.deselect_valve(valve_id=1)

    def test_deselect_all_valves(self, vaem_tcp_mock):
        """Test deselecting all valves."""
        backend = vaem_tcp_mock._backend
        for valve_id in range(1, 9):
            backend.deselect_valve(valve_id=valve_id)


class TestVAEMModbusClientValveParameters:
    """Test valve parameter get/set operations."""

    def test_set_inrush_current(self, vaem_tcp_mock):
        """Test setting inrush current."""
        backend = vaem_tcp_mock._backend
        backend.set_inrush_current(valve_id=1, inrush_current=150)

    def test_get_inrush_current(self, vaem_tcp_mock):
        """Test getting inrush current."""
        backend = vaem_tcp_mock._backend
        result = backend.get_inrush_current(valve_id=1)
        assert result == 150

    def test_set_nominal_voltage(self, vaem_tcp_mock):
        """Test setting nominal voltage."""
        backend = vaem_tcp_mock._backend
        backend.set_nominal_voltage(valve_id=1, voltage=12000)

    def test_get_nominal_voltage(self, vaem_tcp_mock):
        """Test getting nominal voltage."""
        backend = vaem_tcp_mock._backend
        result = backend.get_nominal_voltage(valve_id=1)
        assert result == 12000

    def test_set_valve_switching_time(self, vaem_tcp_mock):
        """Test setting valve switching time."""
        backend = vaem_tcp_mock._backend
        backend.set_valve_switching_time(valve_id=1, opening_time=100)

    def test_get_valve_switching_time(self, vaem_tcp_mock):
        """Test getting valve switching time."""
        backend = vaem_tcp_mock._backend
        result = backend.get_valve_switching_time(valve_id=1)
        assert result == 135

    def test_set_delay_time(self, vaem_tcp_mock):
        """Test setting delay time."""
        backend = vaem_tcp_mock._backend
        backend.set_delay_time(valve_id=1, delay_time=50)

    def test_get_delay_time(self, vaem_tcp_mock):
        """Test getting delay time."""
        backend = vaem_tcp_mock._backend
        result = backend.get_delay_time(valve_id=1)
        assert result == 20

    def test_set_pickup_time(self, vaem_tcp_mock):
        """Test setting pickup time."""
        backend = vaem_tcp_mock._backend
        backend.set_pickup_time(valve_id=1, pickup_time=100)

    def test_get_pickup_time(self, vaem_tcp_mock):
        """Test getting pickup time."""
        backend = vaem_tcp_mock._backend
        result = backend.get_pickup_time(valve_id=1)
        assert result == 50

    def test_set_holding_current(self, vaem_tcp_mock):
        """Test setting holding current."""
        backend = vaem_tcp_mock._backend
        backend.set_holding_current(valve_id=1, holding_current=100)

    def test_get_holding_current(self, vaem_tcp_mock):
        """Test getting holding current."""
        backend = vaem_tcp_mock._backend
        result = backend.get_holding_current(valve_id=1)
        assert result == 100

    def test_get_current_reduction_time(self, vaem_tcp_mock):
        """Test getting current reduction time."""
        backend = vaem_tcp_mock._backend
        backend.get_current_reduction_time(valve_id=1)


class TestVAEMModbusClientValveOperations:
    """Test valve operation methods."""

    def test_open_selected_valves(self, vaem_tcp_mock):
        """Test opening selected valves."""
        backend = vaem_tcp_mock._backend
        backend.open_selected_valves()

    def test_close_valves(self, vaem_tcp_mock):
        """Test closing valves."""
        backend = vaem_tcp_mock._backend
        backend.close_valves()

    def test_open_valves_with_timings(self, vaem_tcp_mock):
        """Test opening valves with timings."""
        backend = vaem_tcp_mock._backend
        timings = {1: 100, 2: 100, 3: 100}
        backend.open_valves(timings=timings)

    def test_save_settings(self, vaem_tcp_mock):
        """Test saving settings to non-volatile memory."""
        backend = vaem_tcp_mock._backend
        backend.save_settings()

    def test_clear_error(self, vaem_tcp_mock):
        """Test clearing errors."""
        backend = vaem_tcp_mock._backend
        backend.clear_error()


class TestVAEMModbusClientErrorHandling:
    """Test error handling functionality."""

    def test_set_error_handling_enabled(self, vaem_tcp_mock):
        """Test enabling error handling."""
        backend = vaem_tcp_mock._backend
        backend.set_error_handling(activate=1)

    def test_set_error_handling_disabled(self, vaem_tcp_mock):
        """Test disabling error handling."""
        backend = vaem_tcp_mock._backend
        backend.set_error_handling(activate=0)

    def test_get_error_handling_status(self, vaem_tcp_mock):
        """Test getting error handling status."""
        backend = vaem_tcp_mock._backend
        result = backend.get_error_handling_status()
        assert result == 1


class TestVAEMModbusClientStatusRetrieval:
    """Test status retrieval operations."""

    def test_get_status(self, vaem_tcp_mock):
        """Test getting device status."""
        backend = vaem_tcp_mock._backend
        status = backend.get_status()
        assert isinstance(status, dict)
        assert "Status" in status
        assert "Error" in status


class TestVAEMModbusClientInitialization:
    """Test VAEM initialization process."""

    def test_vaem_init(self, vaem_tcp_mock):
        """Test VAEM device initialization."""
        backend = vaem_tcp_mock._backend
        backend._vaem_init()


class TestVAEMModbusClientComplexOperations:
    """Test complex operations and sequences."""

    def test_configure_single_valve_sequence(self, vaem_tcp_mock):
        """Test configuring a single valve with multiple parameters."""
        backend = vaem_tcp_mock._backend
        
        valve_id = 1
        backend.set_nominal_voltage(valve_id=valve_id, voltage=12000)
        backend.set_inrush_current(valve_id=valve_id, inrush_current=150)
        backend.set_holding_current(valve_id=valve_id, holding_current=100)
        backend.set_valve_switching_time(valve_id=valve_id, opening_time=100)
        
        # Verify we can read back the values
        voltage = backend.get_nominal_voltage(valve_id=valve_id)
        current = backend.get_inrush_current(valve_id=valve_id)
        holding = backend.get_holding_current(valve_id=valve_id)
        switching = backend.get_valve_switching_time(valve_id=valve_id)
        
        assert voltage is not None
        assert current is not None
        assert holding is not None
        assert switching is not None

    def test_full_valve_operation_sequence(self, vaem_tcp_mock):
        """Test a complete sequence of valve operations."""
        backend = vaem_tcp_mock._backend
        
        # Get initial status
        status = backend.get_status()
        assert status is not None
        
        # Configure valve
        backend.set_nominal_voltage(valve_id=1, voltage=12000)
        backend.select_valve(valve_id=1)
        
        # Open valve
        backend.open_selected_valves()
        
        # Close valve
        backend.close_valves()
        
        # Deselect valve
        backend.deselect_valve(valve_id=1)
        
        # Get final status
        final_status = backend.get_status()
        assert final_status is not None

    def test_multiple_valves_configuration(self, vaem_tcp_mock):
        """Test configuring multiple valves."""
        backend = vaem_tcp_mock._backend
        
        for valve_id in range(1, 9):
            backend.set_nominal_voltage(valve_id=valve_id, voltage=12000)
            backend.set_inrush_current(valve_id=valve_id, inrush_current=150)
            backend.set_holding_current(valve_id=valve_id, holding_current=100)

    def test_error_handling_workflow(self, vaem_tcp_mock):
        """Test error handling workflow."""
        backend = vaem_tcp_mock._backend
        
        # Get initial error status
        status = backend.get_error_handling_status()
        assert status == 1
        
        # Disable error handling
        backend.set_error_handling(activate=0)
        
        # Clear any errors
        backend.clear_error()
        
        # Re-enable error handling
        backend.set_error_handling(activate=1)

    def test_save_and_retrieve_settings(self, vaem_tcp_mock):
        """Test saving settings and retrieving them."""
        backend = vaem_tcp_mock._backend
        
        # Set parameters
        backend.set_nominal_voltage(valve_id=1, voltage=12000)
        backend.set_inrush_current(valve_id=1, inrush_current=150)
        
        # Save settings
        backend.save_settings()
        
        # Retrieve settings
        voltage = backend.get_nominal_voltage(valve_id=1)
        current = backend.get_inrush_current(valve_id=1)
        
        assert voltage == 12000
        assert current == 150
