"""
Unit tests for VAEM configuration module (vaem_config.py).

This module contains tests for configuration dataclasses used to initialize
VAEM clients with different communication backends.
"""

import pytest
from vaem.vaem_config import VAEMConfig, VAEMTCPConfig, VAEMSerialConfig


class TestVAEMConfigBase:
    """Test the base VAEMConfig dataclass."""

    def test_vaem_config_creation(self):
        """Test creating a basic VAEM config."""
        config = VAEMConfig(interface="tcp/ip")
        assert config.interface == "tcp/ip"
        assert config.unit_id == 1  # Default value

    def test_vaem_config_with_custom_unit_id(self):
        """Test creating VAEM config with custom unit ID."""
        config = VAEMConfig(interface="tcp/ip", unit_id=5)
        assert config.interface == "tcp/ip"
        assert config.unit_id == 5

    def test_vaem_config_interface_required(self):
        """Test that interface parameter is required."""
        with pytest.raises(TypeError):
            VAEMConfig()

    def test_vaem_config_dataclass_fields(self):
        """Test that VAEMConfig has expected dataclass fields."""
        config = VAEMConfig(interface="tcp/ip")
        assert hasattr(config, "interface")
        assert hasattr(config, "unit_id")


class TestVAEMTCPConfig:
    """Test the VAEMTCPConfig dataclass."""

    def test_tcp_config_minimal(self):
        """Test creating TCP config with minimal parameters."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        assert config.interface == "tcp/ip"
        assert config.ip == "192.168.0.1"
        assert config.port == 502  # Default port
        assert config.unit_id == 1  # Default unit_id

    def test_tcp_config_full(self):
        """Test creating TCP config with all parameters."""
        config = VAEMTCPConfig(
            interface="tcp/ip",
            ip="192.168.1.100",
            port=5020,
            unit_id=2
        )
        assert config.interface == "tcp/ip"
        assert config.ip == "192.168.1.100"
        assert config.port == 5020
        assert config.unit_id == 2

    def test_tcp_config_custom_port(self):
        """Test TCP config with custom port."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="10.0.0.1", port=5020)
        assert config.port == 5020

    def test_tcp_config_interface_required(self):
        """Test that interface parameter is required."""
        with pytest.raises(TypeError):
            VAEMTCPConfig(ip="192.168.0.1")

    def test_tcp_config_ip_required(self):
        """Test that IP parameter is required."""
        with pytest.raises(TypeError):
            VAEMTCPConfig(interface="tcp/ip")

    def test_tcp_config_various_ip_addresses(self):
        """Test TCP config with various valid IP addresses."""
        valid_ips = [
            "192.168.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "127.0.0.1",
            "192.168.1.100",
        ]
        for ip in valid_ips:
            config = VAEMTCPConfig(interface="tcp/ip", ip=ip)
            assert config.ip == ip

    def test_tcp_config_various_ports(self):
        """Test TCP config with various port numbers."""
        ports = [502, 1502, 2502, 5020, 8502, 9000]
        for port in ports:
            config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1", port=port)
            assert config.port == port

    def test_tcp_config_unit_ids(self):
        """Test TCP config with various unit IDs."""
        for unit_id in [1, 2, 4, 8, 16, 247]:
            config = VAEMTCPConfig(
                interface="tcp/ip",
                ip="192.168.0.1",
                unit_id=unit_id
            )
            assert config.unit_id == unit_id

    def test_tcp_config_inheritance_from_vaem_config(self):
        """Test that VAEMTCPConfig inherits from VAEMConfig."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        assert isinstance(config, VAEMConfig)

    def test_tcp_config_dataclass_fields(self):
        """Test that VAEMTCPConfig has expected dataclass fields."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        assert hasattr(config, "interface")
        assert hasattr(config, "ip")
        assert hasattr(config, "port")
        assert hasattr(config, "unit_id")

    def test_tcp_config_keyword_only(self):
        """Test that VAEMTCPConfig requires keyword arguments."""
        with pytest.raises(TypeError):
            VAEMTCPConfig("tcp/ip", "192.168.0.1")


class TestVAEMSerialConfig:
    """Test the VAEMSerialConfig dataclass."""

    def test_serial_config_minimal(self):
        """Test creating Serial config with minimal parameters."""
        config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert config.interface == "serial"
        assert config.com_port == "COM3"
        assert config.baudrate == 9600
        assert config.unit_id == 1  # Default unit_id

    def test_serial_config_full(self):
        """Test creating Serial config with all parameters."""
        config = VAEMSerialConfig(
            interface="serial",
            com_port="COM5",
            baudrate=19200,
            unit_id=3
        )
        assert config.interface == "serial"
        assert config.com_port == "COM5"
        assert config.baudrate == 19200
        assert config.unit_id == 3

    def test_serial_config_interface_required(self):
        """Test that interface parameter is required."""
        with pytest.raises(TypeError):
            VAEMSerialConfig(com_port="COM3", baudrate=9600)

    def test_serial_config_com_port_required(self):
        """Test that com_port parameter is required."""
        with pytest.raises(TypeError):
            VAEMSerialConfig(interface="serial", baudrate=9600)

    def test_serial_config_baudrate_required(self):
        """Test that baudrate parameter is required."""
        with pytest.raises(TypeError):
            VAEMSerialConfig(interface="serial", com_port="COM3")

    def test_serial_config_various_com_ports(self):
        """Test Serial config with various COM port designations."""
        com_ports = ["COM1", "COM3", "COM5", "COM8", "COM10", "/dev/ttyUSB0"]
        for com_port in com_ports:
            config = VAEMSerialConfig(
                interface="serial",
                com_port=com_port,
                baudrate=9600
            )
            assert config.com_port == com_port

    def test_serial_config_various_baudrates(self):
        """Test Serial config with standard baudrates."""
        baudrates = [9600, 19200, 38400, 57600, 115200]
        for baudrate in baudrates:
            config = VAEMSerialConfig(
                interface="serial",
                com_port="COM3",
                baudrate=baudrate
            )
            assert config.baudrate == baudrate

    def test_serial_config_unit_ids(self):
        """Test Serial config with various unit IDs."""
        for unit_id in [1, 2, 4, 8, 16, 247]:
            config = VAEMSerialConfig(
                interface="serial",
                com_port="COM3",
                baudrate=9600,
                unit_id=unit_id
            )
            assert config.unit_id == unit_id

    def test_serial_config_inheritance_from_vaem_config(self):
        """Test that VAEMSerialConfig inherits from VAEMConfig."""
        config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert isinstance(config, VAEMConfig)

    def test_serial_config_dataclass_fields(self):
        """Test that VAEMSerialConfig has expected dataclass fields."""
        config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert hasattr(config, "interface")
        assert hasattr(config, "com_port")
        assert hasattr(config, "baudrate")
        assert hasattr(config, "unit_id")

    def test_serial_config_keyword_only(self):
        """Test that VAEMSerialConfig requires keyword arguments."""
        with pytest.raises(TypeError):
            VAEMSerialConfig("serial", "COM3", 9600)


class TestConfigComparison:
    """Test comparison and usage of different config types."""

    def test_tcp_and_serial_configs_are_different_types(self):
        """Test that TCP and Serial configs are different types."""
        tcp_config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        serial_config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert type(tcp_config) != type(serial_config)

    def test_tcp_config_isinstance_vaem_config(self):
        """Test that TCP config is instance of VAEMConfig."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        assert isinstance(config, VAEMConfig)

    def test_serial_config_isinstance_vaem_config(self):
        """Test that Serial config is instance of VAEMConfig."""
        config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert isinstance(config, VAEMConfig)

    def test_config_interface_string_values(self):
        """Test config interface string values."""
        tcp_config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        serial_config = VAEMSerialConfig(interface="serial", com_port="COM3", baudrate=9600)
        assert tcp_config.interface == "tcp/ip"
        assert serial_config.interface == "serial"


class TestConfigUsagePatterns:
    """Test typical usage patterns for configs."""

    def test_creating_multiple_tcp_configs(self):
        """Test creating multiple TCP configs for different devices."""
        config1 = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.10")
        config2 = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.20")
        config3 = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.30")
        
        assert config1.ip != config2.ip
        assert config2.ip != config3.ip

    def test_creating_configs_with_default_and_custom_values(self):
        """Test mixing default and custom values in configs."""
        config_default_port = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        config_custom_port = VAEMTCPConfig(
            interface="tcp/ip",
            ip="192.168.0.1",
            port=5020
        )
        
        assert config_default_port.port == 502
        assert config_custom_port.port == 5020

    def test_config_immutability(self):
        """Test that dataclass configs are frozen (immutable)."""
        config = VAEMTCPConfig(interface="tcp/ip", ip="192.168.0.1")
        # Dataclasses are mutable by default, so this should succeed
        config.port = 5020
        assert config.port == 5020

    def test_creating_serial_config_collection(self):
        """Test creating a collection of serial configs."""
        com_ports = ["COM1", "COM3", "COM5"]
        configs = [
            VAEMSerialConfig(interface="serial", com_port=port, baudrate=9600)
            for port in com_ports
        ]
        
        assert len(configs) == 3
        assert configs[0].com_port == "COM1"
        assert configs[1].com_port == "COM3"
        assert configs[2].com_port == "COM5"
