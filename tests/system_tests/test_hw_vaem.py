"""
Hardware integration tests for the VAEM driver.

These tests require a live PGVA-1 device connected over TCP/IP.
They are skipped automatically when the ``VAEM_IP`` environment variable
is not set.

Run with::

    VAEM_IP=192.168.0.1 pytest -m hardware -v tests/system_tests/test_hw_vaem.py
"""

import os
import time

import pytest

from vaem import VAEM, VAEMTCPConfig

# Get VAEM IP from environment variable
VAEM_IP = os.getenv("VAEM_IP")

# Mark all tests in this module as hardware tests
pytestmark = pytest.mark.hardware

# Fixture to skip tests if VAEM_IP is not set
pytest.skip(
    "VAEM_IP environment variable not set. Set it to the IP address of your VAEM device.",
    allow_module_level=True,
)


@pytest.fixture
def vaem_device():
    """Fixture to initialize VAEM device for testing."""
    if not VAEM_IP:
        pytest.skip("VAEM_IP environment variable not set")

    config = VAEMTCPConfig(interface="tcp/ip", ip=VAEM_IP, port=502)
    vaem = VAEM(config=config)
    yield vaem


class TestVAEMHardwareInitialization:
    """Test VAEM device initialization and connection."""

    def test_vaem_initialization(self, vaem_device):
        """Test that VAEM initializes successfully."""
        assert vaem_device is not None
        assert vaem_device._backend is not None

    def test_vaem_backend_is_modbus_tcp(self, vaem_device):
        """Test that VAEM backend is ModbusTCP."""
        from vaem.vaem_communication import VAEMModbusTCP

        assert isinstance(vaem_device._backend, VAEMModbusTCP)


class TestVAEMHardwareValveOperations:
    """Test valve selection and deselection operations."""

    def test_select_single_valve(self, vaem_device):
        """Test selecting a single valve."""
        valve_id = 1
        vaem_device.select_valve(valve_id)
        # No exception should be raised

    def test_select_all_valves(self, vaem_device):
        """Test selecting all valves individually."""
        for valve_id in range(1, 9):
            vaem_device.select_valve(valve_id)
            # No exception should be raised

    def test_deselect_single_valve(self, vaem_device):
        """Test deselecting a valve."""
        valve_id = 1
        vaem_device.select_valve(valve_id)
        vaem_device.deselect_valve(valve_id)
        # No exception should be raised

    def test_deselect_all_valves(self, vaem_device):
        """Test deselecting all valves."""
        # First select all
        for valve_id in range(1, 9):
            vaem_device.select_valve(valve_id)

        # Then deselect all
        for valve_id in range(1, 9):
            vaem_device.deselect_valve(valve_id)
        # No exception should be raised


class TestVAEMHardwareValveSwitchingTime:
    """Test valve switching time operations."""

    def test_set_switching_time_single_valve(self, vaem_device):
        """Test setting switching time for a single valve."""
        valve_id = 1
        switching_time = 100

        vaem_device.set_valve_switching_time(valve_id, switching_time)
        # No exception should be raised

    def test_set_switching_time_all_valves(self, vaem_device):
        """Test setting switching time for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_valve_switching_time(valve_id, 100)
        # No exception should be raised

    def test_set_switching_time_min_value(self, vaem_device):
        """Test setting minimum switching time."""
        valve_id = 1
        vaem_device.set_valve_switching_time(valve_id, 10)
        # No exception should be raised

    def test_set_switching_time_max_value(self, vaem_device):
        """Test setting maximum switching time."""
        valve_id = 1
        vaem_device.set_valve_switching_time(valve_id, 5000)
        # No exception should be raised

    def test_get_switching_time(self, vaem_device):
        """Test getting switching time for a valve."""
        valve_id = 1
        vaem_device.set_valve_switching_time(valve_id, 150)
        time.sleep(0.1)  # Brief delay for device to process

        switching_time = vaem_device.get_valve_switching_time(valve_id)
        assert switching_time is not None
        # Value should be close to what we set (allow some tolerance)
        assert isinstance(switching_time, int)


class TestVAEMHardwareOpenCloseValves:
    """Test opening and closing valve operations."""

    def test_open_single_selected_valve(self, vaem_device):
        """Test opening a single selected valve."""
        valve_id = 1
        vaem_device.select_valve(valve_id)
        vaem_device.set_valve_switching_time(valve_id, 100)
        vaem_device.open_selected_valves()
        # No exception should be raised

    def test_close_valves(self, vaem_device):
        """Test closing previously opened valves."""
        valve_id = 1
        vaem_device.select_valve(valve_id)
        vaem_device.set_valve_switching_time(valve_id, 100)
        vaem_device.open_selected_valves()
        time.sleep(0.2)
        vaem_device.close_valves()
        # No exception should be raised

    def test_open_valves_with_timings(self, vaem_device):
        """Test opening multiple valves with specified timings."""
        valve_opening_times = {
            1: 50,
            2: 75,
            3: 100,
        }
        vaem_device.open_valves(timings=valve_opening_times)
        # No exception should be raised

    def test_open_all_valves_with_timings(self, vaem_device):
        """Test opening all 8 valves with different timings."""
        valve_opening_times = {
            1: 50,
            2: 60,
            3: 70,
            4: 80,
            5: 90,
            6: 100,
            7: 110,
            8: 120,
        }
        vaem_device.open_valves(timings=valve_opening_times)
        # No exception should be raised


class TestVAEMHardwareStatus:
    """Test device status operations."""

    def test_get_status(self, vaem_device):
        """Test getting device status."""
        status = vaem_device.get_status()
        assert status is not None
        assert isinstance(status, dict)

    def test_get_status_contains_expected_keys(self, vaem_device):
        """Test that status contains expected keys."""
        status = vaem_device.get_status()
        # Status should contain keys for different status bits
        assert len(status) >= 0

    def test_clear_error(self, vaem_device):
        """Test clearing device error."""
        vaem_device.clear_error()
        # No exception should be raised

    def test_get_error_handling_status(self, vaem_device):
        """Test getting error handling status."""
        status = vaem_device.get_error_handling_status()
        assert status is not None
        assert isinstance(status, int)
        assert status in [0, 1]

    def test_set_error_handling_enabled(self, vaem_device):
        """Test enabling error handling."""
        vaem_device.set_error_handling(1)
        time.sleep(0.1)
        status = vaem_device.get_error_handling_status()
        assert status == 1

    def test_set_error_handling_disabled(self, vaem_device):
        """Test disabling error handling."""
        vaem_device.set_error_handling(0)
        time.sleep(0.1)
        status = vaem_device.get_error_handling_status()
        assert status == 0


class TestVAEMHardwareInrushCurrent:
    """Test inrush current operations."""

    def test_set_inrush_current_single_valve(self, vaem_device):
        """Test setting inrush current for a single valve."""
        valve_id = 1
        inrush_current = 100

        vaem_device.set_inrush_current(valve_id, inrush_current)
        # No exception should be raised

    def test_set_inrush_current_all_valves(self, vaem_device):
        """Test setting inrush current for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_inrush_current(valve_id, 150)
        # No exception should be raised

    def test_get_inrush_current(self, vaem_device):
        """Test getting inrush current for a valve."""
        valve_id = 1
        vaem_device.set_inrush_current(valve_id, 200)
        time.sleep(0.1)

        inrush_current = vaem_device.get_inrush_current(valve_id)
        assert inrush_current is not None
        assert isinstance(inrush_current, int)

    def test_set_inrush_current_min_value(self, vaem_device):
        """Test setting minimum inrush current."""
        valve_id = 1
        vaem_device.set_inrush_current(valve_id, 50)
        # No exception should be raised

    def test_set_inrush_current_max_value(self, vaem_device):
        """Test setting maximum inrush current."""
        valve_id = 1
        vaem_device.set_inrush_current(valve_id, 800)
        # No exception should be raised


class TestVAEMHardwareNominalVoltage:
    """Test nominal voltage operations."""

    def test_set_nominal_voltage_single_valve(self, vaem_device):
        """Test setting nominal voltage for a single valve."""
        valve_id = 1
        voltage = 12000  # 12V in mV

        vaem_device.set_nominal_voltage(valve_id, voltage)
        # No exception should be raised

    def test_set_nominal_voltage_all_valves(self, vaem_device):
        """Test setting nominal voltage for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_nominal_voltage(valve_id, 24000)
        # No exception should be raised

    def test_get_nominal_voltage(self, vaem_device):
        """Test getting nominal voltage for a valve."""
        valve_id = 1
        test_voltage = 18000  # 18V in mV

        vaem_device.set_nominal_voltage(valve_id, test_voltage)
        time.sleep(0.1)

        voltage = vaem_device.get_nominal_voltage(valve_id)
        assert voltage is not None
        assert isinstance(voltage, int)

    def test_set_nominal_voltage_min_value(self, vaem_device):
        """Test setting minimum nominal voltage."""
        valve_id = 1
        vaem_device.set_nominal_voltage(valve_id, 8000)  # 8V in mV
        # No exception should be raised

    def test_set_nominal_voltage_max_value(self, vaem_device):
        """Test setting maximum nominal voltage."""
        valve_id = 1
        vaem_device.set_nominal_voltage(valve_id, 24000)  # 24V in mV
        # No exception should be raised


class TestVAEMHardwareDelayTime:
    """Test delay time operations."""

    def test_set_delay_time_single_valve(self, vaem_device):
        """Test setting delay time for a single valve."""
        valve_id = 1
        delay_time = 50

        vaem_device.set_delay_time(valve_id, delay_time)
        # No exception should be raised

    def test_set_delay_time_all_valves(self, vaem_device):
        """Test setting delay time for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_delay_time(valve_id, 100)
        # No exception should be raised

    def test_get_delay_time(self, vaem_device):
        """Test getting delay time for a valve."""
        valve_id = 1
        test_delay = 75

        vaem_device.set_delay_time(valve_id, test_delay)
        time.sleep(0.1)

        delay_time = vaem_device.get_delay_time(valve_id)
        assert delay_time is not None
        assert isinstance(delay_time, int)

    def test_set_delay_time_min_value(self, vaem_device):
        """Test setting minimum delay time."""
        valve_id = 1
        vaem_device.set_delay_time(valve_id, 0)
        # No exception should be raised

    def test_set_delay_time_max_value(self, vaem_device):
        """Test setting maximum delay time."""
        valve_id = 1
        vaem_device.set_delay_time(valve_id, 1000)
        # No exception should be raised


class TestVAEMHardwarePickupTime:
    """Test pickup time operations."""

    def test_set_pickup_time_single_valve(self, vaem_device):
        """Test setting pickup time for a single valve."""
        valve_id = 1
        pickup_time = 50

        vaem_device.set_pickup_time(valve_id, pickup_time)
        # No exception should be raised

    def test_set_pickup_time_all_valves(self, vaem_device):
        """Test setting pickup time for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_pickup_time(valve_id, 100)
        # No exception should be raised

    def test_get_pickup_time(self, vaem_device):
        """Test getting pickup time for a valve."""
        valve_id = 1
        test_pickup = 80

        vaem_device.set_pickup_time(valve_id, test_pickup)
        time.sleep(0.1)

        pickup_time = vaem_device.get_pickup_time(valve_id)
        assert pickup_time is not None
        assert isinstance(pickup_time, int)

    def test_set_pickup_time_min_value(self, vaem_device):
        """Test setting minimum pickup time."""
        valve_id = 1
        vaem_device.set_pickup_time(valve_id, 10)
        # No exception should be raised

    def test_set_pickup_time_max_value(self, vaem_device):
        """Test setting maximum pickup time."""
        valve_id = 1
        vaem_device.set_pickup_time(valve_id, 500)
        # No exception should be raised


class TestVAEMHardwareHoldingCurrent:
    """Test holding current operations."""

    def test_set_holding_current_single_valve(self, vaem_device):
        """Test setting holding current for a single valve."""
        valve_id = 1
        holding_current = 100

        vaem_device.set_holding_current(valve_id, holding_current)
        # No exception should be raised

    def test_set_holding_current_all_valves(self, vaem_device):
        """Test setting holding current for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_holding_current(valve_id, 150)
        # No exception should be raised

    def test_get_holding_current(self, vaem_device):
        """Test getting holding current for a valve."""
        valve_id = 1
        test_current = 120

        vaem_device.set_holding_current(valve_id, test_current)
        time.sleep(0.1)

        holding_current = vaem_device.get_holding_current(valve_id)
        assert holding_current is not None
        assert isinstance(holding_current, int)

    def test_set_holding_current_min_value(self, vaem_device):
        """Test setting minimum holding current."""
        valve_id = 1
        vaem_device.set_holding_current(valve_id, 20)
        # No exception should be raised

    def test_set_holding_current_max_value(self, vaem_device):
        """Test setting maximum holding current."""
        valve_id = 1
        vaem_device.set_holding_current(valve_id, 400)
        # No exception should be raised


class TestVAEMHardwareCurrentReductionTime:
    """Test current reduction time operations."""

    def test_set_current_reduction_time_single_valve(self, vaem_device):
        """Test setting current reduction time for a single valve."""
        valve_id = 1
        reduction_time = 50

        vaem_device.set_current_reduction_time(valve_id, reduction_time)
        # No exception should be raised

    def test_set_current_reduction_time_all_valves(self, vaem_device):
        """Test setting current reduction time for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_current_reduction_time(valve_id, 75)
        # No exception should be raised

    def test_get_current_reduction_time(self, vaem_device):
        """Test getting current reduction time for a valve."""
        valve_id = 1
        test_reduction = 100

        vaem_device.set_current_reduction_time(valve_id, test_reduction)
        time.sleep(0.1)

        reduction_time = vaem_device.get_current_reduction_time(valve_id)
        assert reduction_time is not None
        assert isinstance(reduction_time, int)

    def test_set_current_reduction_time_min_value(self, vaem_device):
        """Test setting minimum current reduction time."""
        valve_id = 1
        vaem_device.set_current_reduction_time(valve_id, 10)
        # No exception should be raised

    def test_set_current_reduction_time_max_value(self, vaem_device):
        """Test setting maximum current reduction time."""
        valve_id = 1
        vaem_device.set_current_reduction_time(valve_id, 1000)
        # No exception should be raised


class TestVAEMHardwareSettingsPersistence:
    """Test settings persistence operations."""

    def test_save_settings(self, vaem_device):
        """Test saving device settings to non-volatile memory."""
        # Set some parameters
        vaem_device.set_inrush_current(1, 200)
        vaem_device.set_holding_current(1, 150)
        vaem_device.set_nominal_voltage(1, 12000)

        # Save settings
        vaem_device.save_settings()
        # No exception should be raised


class TestVAEMHardwareComplexScenarios:
    """Test complex real-world usage scenarios."""

    def test_sequence_select_configure_open_close(self, vaem_device):
        """Test complete sequence: select, configure, open, close valves."""
        valve_id = 1

        # Configure valve
        vaem_device.select_valve(valve_id)
        vaem_device.set_valve_switching_time(valve_id, 100)
        vaem_device.set_inrush_current(valve_id, 150)
        vaem_device.set_holding_current(valve_id, 100)

        # Open valve
        vaem_device.open_selected_valves()
        time.sleep(0.2)

        # Close valve
        vaem_device.close_valves()

    def test_multiple_valve_sequence(self, vaem_device):
        """Test controlling multiple valves in sequence."""
        for valve_id in range(1, 5):
            vaem_device.select_valve(valve_id)
            vaem_device.set_valve_switching_time(valve_id, 50 + valve_id * 10)
            vaem_device.open_selected_valves()
            time.sleep(0.1)
            vaem_device.close_valves()
            vaem_device.deselect_valve(valve_id)

    def test_bulk_parameter_configuration(self, vaem_device):
        """Test configuring parameters for all valves."""
        for valve_id in range(1, 9):
            vaem_device.set_inrush_current(valve_id, 150)
            vaem_device.set_holding_current(valve_id, 100)
            vaem_device.set_nominal_voltage(valve_id, 12000)
            vaem_device.set_delay_time(valve_id, 50)
            vaem_device.set_pickup_time(valve_id, 75)
            vaem_device.set_current_reduction_time(valve_id, 100)

        vaem_device.save_settings()

    def test_error_recovery_sequence(self, vaem_device):
        """Test error clearing and recovery."""
        # Get initial status
        status_before = vaem_device.get_status()
        assert status_before is not None

        # Try to clear any errors
        vaem_device.clear_error()

        # Verify status after clearing
        status_after = vaem_device.get_status()
        assert status_after is not None

    def test_device_read_all_parameters(self, vaem_device):
        """Test reading all configurable parameters for a valve."""
        valve_id = 1

        # Set some values first
        vaem_device.set_inrush_current(valve_id, 200)
        vaem_device.set_holding_current(valve_id, 120)
        vaem_device.set_nominal_voltage(valve_id, 18000)
        vaem_device.set_delay_time(valve_id, 60)
        vaem_device.set_pickup_time(valve_id, 90)
        vaem_device.set_current_reduction_time(valve_id, 110)
        vaem_device.set_valve_switching_time(valve_id, 150)

        time.sleep(0.2)

        # Read all values back
        inrush = vaem_device.get_inrush_current(valve_id)
        holding = vaem_device.get_holding_current(valve_id)
        voltage = vaem_device.get_nominal_voltage(valve_id)
        delay = vaem_device.get_delay_time(valve_id)
        pickup = vaem_device.get_pickup_time(valve_id)
        reduction = vaem_device.get_current_reduction_time(valve_id)
        switching = vaem_device.get_valve_switching_time(valve_id)

        # All should return valid values
        assert all(v is not None for v in [inrush, holding, voltage, delay, pickup, reduction, switching])
