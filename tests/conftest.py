"""
Shared pytest fixtures for the festo-vaem testing suite.

Fixtures:
vaem_tcp_mock
    A ```VAEM``` instance where the backend is replaced by
    ```MagicMock```. This allows all unit test to run without
    the need for hardware of a network connection.

vaem_hw
    A real ```VAEM``` instance connected to the device. These
    hardware tests are automatically skipped when the ```VAEM_IP```
    env variable is not set.
"""

from unittest.mock import MagicMock

import pytest

from vaem import VAEM, VAEMTCPConfig


# ---------------------------------------------------------------------------
# Mock fixture — no hardware required
# ---------------------------------------------------------------------------


@pytest.fixture()
def vaem_tcp_mock(mocker):
    """
    Returns a VAEM instance with it's backend communication replaced with MagicMock OBJ.

    The mock backend communication is defined with a standard set of return values for
    all 'get' methods so the test methods can assert without the requirement of a physical
    Modbus TCP connection.
    """
    mock_backend = MagicMock()

    mock_backend.get_status.return_value = {
        "Status": 1,
        "Error": 0,
        "Readiness": 1,
        "OperatingMode": 1,
        "Valve1": 0,
        "Valve2": 0,
        "Valve3": 0,
        "Valve4": 0,
        "Valve5": 0,
        "Valve6": 0,
        "Valve7": 0,
        "Valve8": 0,
    }

    mock_backend.get_error_handling_status.return_value = 1

    # -------- Valve parameter getters --------
    mock_backend.get_inrush_current.return_value = 150  # mA
    mock_backend.get_nominal_voltage.return_value = 12000  # mV
    mock_backend.get_valve_switching_time.return_value = 135  # ms
    mock_backend.get_delay_time.return_value = 20  # ms
    mock_backend.get_pickup_time.return_value = 50  # ms
    mock_backend.get_holding_current.return_value = 100  # mA
    mock_backend.get_current_reduction_time.return_value = 75  # ms
    mock_backend.select_valve.return_value = None
    mock_backend.deselect_valve.return_value = None
    mock_backend.set_valve_switching_time.return_value = None
    mock_backend.open_selected_valves.return_value = None
    mock_backend.open_valves.return_value = None
    mock_backend.close_valves.return_value = None
    mock_backend.set_nominal_voltage.return_value = None
    mock_backend.set_inrush_current.return_value = None
    mock_backend.set_delay_time.return_value = None
    mock_backend.set_pickup_time.return_value = None
    mock_backend.set_holding_current.return_value = None
    mock_backend.set_current_reduction_time.return_value = None
    mock_backend.set_error_handling.return_value = None
    mock_backend.save_settings.return_value = None
    mock_backend.clear_error.return_value = None

    mocker.patch("vaem.vaem.VAEMModbusTCP", return_value=mock_backend)

    config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1", port=502, unit_id=1)
    instance = VAEM(config=config)
    instance._mock_backend = mock_backend
    return instance


# ---------------------------------------------------------------------------
# Real backend fixture for communication layer testing
# ---------------------------------------------------------------------------


@pytest.fixture()
def vaem_tcp_backend(mocker):
    """
    Returns a real VAEMModbusTCP instance for testing the communication layer.
    
    The Modbus client connection is mocked to prevent actual network calls,
    but the backend logic remains real for proper unit testing.
    """
    from vaem.vaem_communication import VAEMModbusTCP
    
    config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1", port=502, unit_id=1)
    
    # Mock the ModbusTcpClient before creating VAEMModbusTCP instance
    mock_client = MagicMock()
    mock_client.connect.return_value = True
    mock_client.read_holding_registers.return_value = MagicMock(registers=[0x0001])
    mock_client.write_register.return_value = MagicMock(isError=lambda: False)
    mock_client.write_registers.return_value = MagicMock(isError=lambda: False)
    
    mocker.patch("vaem.vaem_communication.ModbusTcpClient", return_value=mock_client)
    
    backend = VAEMModbusTCP(config=config)
    backend._client = mock_client
    
    return backend
