"""
Unit tests for the VAEM main driver interface (vaem.py).

This module contains tests for the VAEM class that provide a high-level
interface to the valve control functionality.
"""

import pytest
from vaem import VAEM


class TestVAEMInitialization:
    """Test VAEM class initialization."""

    def test_vaem_tcp_initialization(self, vaem_tcp_mock):
        """Test that VAEM initializes correctly with TCP config."""
        assert isinstance(vaem_tcp_mock, VAEM)
        assert vaem_tcp_mock._config.ip == "192.168.0.1"
        assert vaem_tcp_mock._config.port == 502
        assert vaem_tcp_mock._config.unit_id == 1

    def test_vaem_invalid_config_raises_type_error(self, mocker):
        """Test that invalid config raises TypeError."""
        with pytest.raises(TypeError):
            VAEM(config="invalid_config")

    def test_vaem_backend_is_set(self, vaem_tcp_mock):
        """Test that backend is properly set during initialization."""
        assert vaem_tcp_mock._backend is not None


class TestVAEMValveSelection:
    """Test valve selection and deselection functionality."""

    def test_select_valve_valid_id(self, vaem_tcp_mock):
        """Test selecting a valid valve ID."""
        vaem_tcp_mock.select_valve(valve_id=1)
        vaem_tcp_mock._mock_backend.select_valve.assert_called_with(1)

    def test_select_multiple_valves(self, vaem_tcp_mock):
        """Test selecting multiple valve IDs sequentially."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.select_valve(valve_id=valve_id)
        assert vaem_tcp_mock._mock_backend.select_valve.call_count == 8

    def test_deselect_valve_valid_id(self, vaem_tcp_mock):
        """Test deselecting a valid valve ID."""
        vaem_tcp_mock.deselect_valve(valve_id=1)
        vaem_tcp_mock._mock_backend.deselect_valve.assert_called_with(1)

    def test_deselect_all_valves(self, vaem_tcp_mock):
        """Test deselecting all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.deselect_valve(valve_id=valve_id)
        assert vaem_tcp_mock._mock_backend.deselect_valve.call_count == 8


class TestVAEMValveSwitchingTime:
    """Test valve switching time configuration."""

    def test_set_valve_switching_time(self, vaem_tcp_mock):
        """Test setting valve switching time."""
        valve_id = 1
        opening_time = 100
        vaem_tcp_mock.set_valve_switching_time(valve_id=valve_id, opening_time=opening_time)
        vaem_tcp_mock._mock_backend.set_valve_switching_time.assert_called_with(valve_id, opening_time)

    def test_get_valve_switching_time(self, vaem_tcp_mock):
        """Test getting valve switching time."""
        valve_id = 1
        result = vaem_tcp_mock.get_valve_switching_time(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_valve_switching_time.assert_called_with(valve_id)
        assert result == 135  # From conftest.py mock return value

    def test_set_switching_time_multiple_valves(self, vaem_tcp_mock):
        """Test setting switching time for multiple valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_valve_switching_time(valve_id=valve_id, opening_time=100 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_valve_switching_time.call_count == 8


class TestVAEMValveOperations:
    """Test valve opening and closing operations."""

    def test_open_selected_valves(self, vaem_tcp_mock):
        """Test opening all selected valves."""
        vaem_tcp_mock.open_selected_valves()
        vaem_tcp_mock._mock_backend.open_selected_valves.assert_called_once()

    def test_close_valves(self, vaem_tcp_mock):
        """Test closing valves."""
        vaem_tcp_mock.close_valves()
        vaem_tcp_mock._mock_backend.close_valves.assert_called_once()

    def test_open_valves_with_timings(self, vaem_tcp_mock):
        """Test opening valves with specified timings."""
        valve_timings = {
            1: 100,
            2: 150,
            3: 200,
            4: 100,
            5: 100,
            6: 100,
            7: 100,
            8: 100,
        }
        vaem_tcp_mock.open_valves(timings=valve_timings)
        vaem_tcp_mock._mock_backend.open_valves.assert_called_with(valve_timings)

    def test_open_valves_all_valves(self, vaem_tcp_mock):
        """Test opening all 8 valves with timing."""
        valve_timings = {i: 100 for i in range(1, 9)}
        vaem_tcp_mock.open_valves(timings=valve_timings)
        vaem_tcp_mock._mock_backend.open_valves.assert_called_once()


class TestVAEMStatus:
    """Test device status functionality."""

    def test_get_status(self, vaem_tcp_mock):
        """Test getting device status."""
        status = vaem_tcp_mock.get_status()
        vaem_tcp_mock._mock_backend.get_status.assert_called_once()
        assert isinstance(status, dict)

    def test_status_contains_expected_keys(self, vaem_tcp_mock):
        """Test that status dictionary contains expected keys."""
        status = vaem_tcp_mock.get_status()
        expected_keys = {
            "Status",
            "Error",
            "Readiness",
            "OperatingMode",
            "Valve1",
            "Valve2",
            "Valve3",
            "Valve4",
            "Valve5",
            "Valve6",
            "Valve7",
            "Valve8",
        }
        assert set(status.keys()) == expected_keys

    def test_clear_error(self, vaem_tcp_mock):
        """Test clearing errors."""
        vaem_tcp_mock.clear_error()
        vaem_tcp_mock._mock_backend.clear_error.assert_called_once()


class TestVAEMInrushCurrent:
    """Test inrush current get/set operations."""

    def test_set_inrush_current(self, vaem_tcp_mock):
        """Test setting inrush current."""
        valve_id = 1
        inrush_current = 150
        vaem_tcp_mock.set_inrush_current(valve_id=valve_id, inrush_current=inrush_current)
        vaem_tcp_mock._mock_backend.set_inrush_current.assert_called_with(valve_id, inrush_current)

    def test_get_inrush_current(self, vaem_tcp_mock):
        """Test getting inrush current."""
        valve_id = 1
        result = vaem_tcp_mock.get_inrush_current(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_inrush_current.assert_called_with(valve_id)
        assert result == 150  # From conftest.py mock return value

    def test_set_inrush_current_all_valves(self, vaem_tcp_mock):
        """Test setting inrush current for all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_inrush_current(valve_id=valve_id, inrush_current=100 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_inrush_current.call_count == 8

    def test_get_inrush_current_all_valves(self, vaem_tcp_mock):
        """Test getting inrush current for all valves."""
        for valve_id in range(1, 9):
            result = vaem_tcp_mock.get_inrush_current(valve_id=valve_id)
            assert result == 150
        assert vaem_tcp_mock._mock_backend.get_inrush_current.call_count == 8


class TestVAEMNominalVoltage:
    """Test nominal voltage get/set operations."""

    def test_set_nominal_voltage(self, vaem_tcp_mock):
        """Test setting nominal voltage."""
        valve_id = 1
        voltage = 12000
        vaem_tcp_mock.set_nominal_voltage(valve_id=valve_id, voltage=voltage)
        vaem_tcp_mock._mock_backend.set_nominal_voltage.assert_called_with(valve_id, voltage)

    def test_get_nominal_voltage(self, vaem_tcp_mock):
        """Test getting nominal voltage."""
        valve_id = 1
        result = vaem_tcp_mock.get_nominal_voltage(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_nominal_voltage.assert_called_with(valve_id)
        assert result == 12000  # From conftest.py mock return value

    def test_set_nominal_voltage_range(self, vaem_tcp_mock):
        """Test setting nominal voltage with different values."""
        valve_id = 1
        voltage_values = [8000, 10000, 12000, 15000, 24000]
        for voltage in voltage_values:
            vaem_tcp_mock.set_nominal_voltage(valve_id=valve_id, voltage=voltage)
        assert vaem_tcp_mock._mock_backend.set_nominal_voltage.call_count == len(voltage_values)


class TestVAEMDelayTime:
    """Test delay time get/set operations."""

    def test_set_delay_time(self, vaem_tcp_mock):
        """Test setting delay time."""
        valve_id = 1
        delay_time = 50
        vaem_tcp_mock.set_delay_time(valve_id=valve_id, delay_time=delay_time)
        vaem_tcp_mock._mock_backend.set_delay_time.assert_called_with(valve_id, delay_time)

    def test_get_delay_time(self, vaem_tcp_mock):
        """Test getting delay time."""
        valve_id = 1
        result = vaem_tcp_mock.get_delay_time(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_delay_time.assert_called_with(valve_id)
        assert result == 20  # From conftest.py mock return value

    def test_set_delay_time_all_valves(self, vaem_tcp_mock):
        """Test setting delay time for all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_delay_time(valve_id=valve_id, delay_time=10 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_delay_time.call_count == 8


class TestVAEMPickupTime:
    """Test pickup time get/set operations."""

    def test_set_pickup_time(self, vaem_tcp_mock):
        """Test setting pickup time."""
        valve_id = 1
        pickup_time = 100
        vaem_tcp_mock.set_pickup_time(valve_id=valve_id, pickup_time=pickup_time)
        vaem_tcp_mock._mock_backend.set_pickup_time.assert_called_with(valve_id, pickup_time)

    def test_get_pickup_time(self, vaem_tcp_mock):
        """Test getting pickup time."""
        valve_id = 1
        result = vaem_tcp_mock.get_pickup_time(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_pickup_time.assert_called_with(valve_id)
        assert result == 50  # From conftest.py mock return value

    def test_set_pickup_time_all_valves(self, vaem_tcp_mock):
        """Test setting pickup time for all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_pickup_time(valve_id=valve_id, pickup_time=50 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_pickup_time.call_count == 8


class TestVAEMHoldingCurrent:
    """Test holding current get/set operations."""

    def test_set_holding_current(self, vaem_tcp_mock):
        """Test setting holding current."""
        valve_id = 1
        holding_current = 100
        vaem_tcp_mock.set_holding_current(valve_id=valve_id, holding_current=holding_current)
        vaem_tcp_mock._mock_backend.set_holding_current.assert_called_with(valve_id, holding_current)

    def test_get_holding_current(self, vaem_tcp_mock):
        """Test getting holding current."""
        valve_id = 1
        result = vaem_tcp_mock.get_holding_current(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_holding_current.assert_called_with(valve_id)
        assert result == 100  # From conftest.py mock return value

    def test_set_holding_current_all_valves(self, vaem_tcp_mock):
        """Test setting holding current for all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_holding_current(valve_id=valve_id, holding_current=80 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_holding_current.call_count == 8


class TestVAEMCurrentReductionTime:
    """Test current reduction time get/set operations."""

    def test_get_current_reduction_time(self, vaem_tcp_mock):
        """Test getting current reduction time."""
        valve_id = 1
        result = vaem_tcp_mock.get_current_reduction_time(valve_id=valve_id)
        vaem_tcp_mock._mock_backend.get_current_reduction_time.assert_called_with(valve_id)

    def test_set_current_reduction_time(self, vaem_tcp_mock):
        """Test setting current reduction time."""
        valve_id = 1
        reduction_time = 75
        vaem_tcp_mock.set_current_reduction_time(valve_id=valve_id, reduction_time=reduction_time)
        vaem_tcp_mock._mock_backend.set_current_reduction_time.assert_called_with(valve_id, reduction_time)

    def test_set_current_reduction_time_all_valves(self, vaem_tcp_mock):
        """Test setting current reduction time for all valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_current_reduction_time(valve_id=valve_id, reduction_time=60 + valve_id)
        assert vaem_tcp_mock._mock_backend.set_current_reduction_time.call_count == 8


class TestVAEMErrorHandling:
    """Test error handling functionality."""

    def test_get_error_handling_status(self, vaem_tcp_mock):
        """Test getting error handling status."""
        result = vaem_tcp_mock.get_error_handling_status()
        vaem_tcp_mock._mock_backend.get_error_handling_status.assert_called_once()
        assert result == 1  # From conftest.py mock return value

    def test_set_error_handling_enabled(self, vaem_tcp_mock):
        """Test enabling error handling."""
        vaem_tcp_mock.set_error_handling(activate=1)
        vaem_tcp_mock._mock_backend.set_error_handling.assert_called_with(1)

    def test_set_error_handling_disabled(self, vaem_tcp_mock):
        """Test disabling error handling."""
        vaem_tcp_mock.set_error_handling(activate=0)
        vaem_tcp_mock._mock_backend.set_error_handling.assert_called_with(0)


class TestVAEMSettingsPersistence:
    """Test settings persistence functionality."""

    def test_save_settings(self, vaem_tcp_mock):
        """Test saving settings to non-volatile memory."""
        vaem_tcp_mock.save_settings()
        vaem_tcp_mock._mock_backend.save_settings.assert_called_once()


class TestVAEMComplexScenarios:
    """Test complex usage scenarios."""

    def test_configure_and_operate_single_valve(self, vaem_tcp_mock):
        """Test a complete sequence for configuring and operating a single valve."""
        valve_id = 1

        # Configure valve
        vaem_tcp_mock.set_nominal_voltage(valve_id=valve_id, voltage=12000)
        vaem_tcp_mock.set_inrush_current(valve_id=valve_id, inrush_current=150)
        vaem_tcp_mock.set_holding_current(valve_id=valve_id, holding_current=100)
        vaem_tcp_mock.set_valve_switching_time(valve_id=valve_id, opening_time=100)

        # Select and operate valve
        vaem_tcp_mock.select_valve(valve_id=valve_id)
        vaem_tcp_mock.open_selected_valves()
        vaem_tcp_mock.close_valves()

        # Verify calls were made
        assert vaem_tcp_mock._mock_backend.set_nominal_voltage.called
        assert vaem_tcp_mock._mock_backend.select_valve.called
        assert vaem_tcp_mock._mock_backend.open_selected_valves.called
        assert vaem_tcp_mock._mock_backend.close_valves.called

    def test_configure_all_valves(self, vaem_tcp_mock):
        """Test configuring all 8 valves."""
        for valve_id in range(1, 9):
            vaem_tcp_mock.set_nominal_voltage(valve_id=valve_id, voltage=12000)
            vaem_tcp_mock.set_inrush_current(valve_id=valve_id, inrush_current=150)
            vaem_tcp_mock.set_holding_current(valve_id=valve_id, holding_current=100)
            vaem_tcp_mock.set_pickup_time(valve_id=valve_id, pickup_time=50)
            vaem_tcp_mock.set_current_reduction_time(valve_id=valve_id, reduction_time=75)

        # Verify calls for each valve
        assert vaem_tcp_mock._mock_backend.set_nominal_voltage.call_count == 8
        assert vaem_tcp_mock._mock_backend.set_inrush_current.call_count == 8
        assert vaem_tcp_mock._mock_backend.set_holding_current.call_count == 8

    def test_get_all_valve_parameters(self, vaem_tcp_mock):
        """Test retrieving all parameters for all valves."""
        for valve_id in range(1, 9):
            voltage = vaem_tcp_mock.get_nominal_voltage(valve_id=valve_id)
            current = vaem_tcp_mock.get_inrush_current(valve_id=valve_id)
            switching_time = vaem_tcp_mock.get_valve_switching_time(valve_id=valve_id)
            delay_time = vaem_tcp_mock.get_delay_time(valve_id=valve_id)
            pickup_time = vaem_tcp_mock.get_pickup_time(valve_id=valve_id)
            holding_current = vaem_tcp_mock.get_holding_current(valve_id=valve_id)

            assert voltage is not None
            assert current is not None
            assert switching_time is not None
            assert delay_time is not None
            assert pickup_time is not None
            assert holding_current is not None

    def test_error_handling_workflow(self, vaem_tcp_mock):
        """Test error handling workflow."""
        # Get initial error handling status
        status = vaem_tcp_mock.get_error_handling_status()
        assert status == 1

        # Disable error handling
        vaem_tcp_mock.set_error_handling(activate=0)

        # Clear any errors
        vaem_tcp_mock.clear_error()

        # Verify calls
        assert vaem_tcp_mock._mock_backend.set_error_handling.called
        assert vaem_tcp_mock._mock_backend.clear_error.called

    def test_sequential_valve_operations(self, vaem_tcp_mock):
        """Test sequential operations on multiple valves."""
        valve_timings = {
            1: 100,
            2: 100,
            3: 100,
            4: 100,
            5: 100,
            6: 100,
            7: 100,
            8: 100,
        }

        # Open all valves with timings
        vaem_tcp_mock.open_valves(timings=valve_timings)

        # Get status
        status = vaem_tcp_mock.get_status()

        # Close valves
        vaem_tcp_mock.close_valves()

        assert vaem_tcp_mock._mock_backend.open_valves.called
        assert vaem_tcp_mock._mock_backend.get_status.called
        assert vaem_tcp_mock._mock_backend.close_valves.called
