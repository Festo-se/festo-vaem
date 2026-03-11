"""
Unit tests for VAEM helper module (vaem_helper.py).

This module contains tests for helper enums and utilities used throughout the VAEM driver.
"""

import pytest
from vaem.vaem_helper import (
    VaemAccess,
    VaemDataType,
    VaemIndex,
    VaemControlWords,
    VaemOperatingMode,
    vaemValveIndex,
)


class TestVaemAccess:
    """Test VaemAccess enum."""

    def test_vaem_access_read_value(self):
        """Test READ access value."""
        assert VaemAccess.READ.value == 0

    def test_vaem_access_write_value(self):
        """Test WRITE access value."""
        assert VaemAccess.WRITE.value == 1

    def test_vaem_access_enum_type(self):
        """Test that VaemAccess is an IntEnum."""
        assert isinstance(VaemAccess.READ, int)
        assert isinstance(VaemAccess.WRITE, int)

    def test_vaem_access_members(self):
        """Test VaemAccess has expected members."""
        members = [member.name for member in VaemAccess]
        assert "READ" in members
        assert "WRITE" in members

    def test_vaem_access_comparison(self):
        """Test comparison of VaemAccess values."""
        assert VaemAccess.READ < VaemAccess.WRITE
        assert VaemAccess.WRITE > VaemAccess.READ
        assert VaemAccess.READ != VaemAccess.WRITE


class TestVaemDataType:
    """Test VaemDataType enum."""

    def test_vaem_datatype_uint8(self):
        """Test UINT8 data type value."""
        assert VaemDataType.UINT8.value == 1

    def test_vaem_datatype_uint16(self):
        """Test UINT16 data type value."""
        assert VaemDataType.UINT16.value == 2

    def test_vaem_datatype_uint32(self):
        """Test UINT32 data type value."""
        assert VaemDataType.UINT32.value == 3

    def test_vaem_datatype_uint64(self):
        """Test UINT64 data type value."""
        assert VaemDataType.UINT64.value == 4

    def test_vaem_datatype_enum_type(self):
        """Test that VaemDataType is an IntEnum."""
        assert isinstance(VaemDataType.UINT8, int)
        assert isinstance(VaemDataType.UINT16, int)
        assert isinstance(VaemDataType.UINT32, int)
        assert isinstance(VaemDataType.UINT64, int)

    def test_vaem_datatype_members(self):
        """Test VaemDataType has all expected members."""
        members = [member.name for member in VaemDataType]
        assert "UINT8" in members
        assert "UINT16" in members
        assert "UINT32" in members
        assert "UINT64" in members

    def test_vaem_datatype_ordering(self):
        """Test ordering of data type sizes."""
        assert VaemDataType.UINT8 < VaemDataType.UINT16
        assert VaemDataType.UINT16 < VaemDataType.UINT32
        assert VaemDataType.UINT32 < VaemDataType.UINT64


class TestVaemIndex:
    """Test VaemIndex enum."""

    def test_vaem_index_control_word(self):
        """Test CONTROLWORD index value."""
        assert VaemIndex.CONTROLWORD.value == 0x01

    def test_vaem_index_status_word(self):
        """Test STATUSWORD index value."""
        assert VaemIndex.STATUSWORD.value == 0x02

    def test_vaem_index_nominal_voltage(self):
        """Test NOMINALVOLTAGE index value."""
        assert VaemIndex.NOMINALVOLTAGE.value == 0x04

    def test_vaem_index_inrush_current(self):
        """Test INRUSHCURRENT index value."""
        assert VaemIndex.INRUSHCURRENT.value == 0x05

    def test_vaem_index_holding_current(self):
        """Test HOLDINGCURRENT index value."""
        assert VaemIndex.HOLDINGCURRENT.value == 0x06

    def test_vaem_index_switching_time(self):
        """Test SWITCHINGTIME index value."""
        assert VaemIndex.SWITCHINGTIME.value == 0x07

    def test_vaem_index_pickup_time(self):
        """Test PICKUPTIME index value."""
        assert VaemIndex.PICKUPTIME.value == 0x08

    def test_vaem_index_operating_mode(self):
        """Test OPERATINGMODE index value."""
        assert VaemIndex.OPERATINGMODE.value == 0x09

    def test_vaem_index_save_parameters(self):
        """Test SAVEPARAMETERS index value."""
        assert VaemIndex.SAVEPARAMETERS.value == 0x11

    def test_vaem_index_select_valve(self):
        """Test SELECTVALVE index value."""
        assert VaemIndex.SELECTVALVE.value == 0x13

    def test_vaem_index_time_delay(self):
        """Test TIMEDELAY index value."""
        assert VaemIndex.TIMEDELAY.value == 0x16

    def test_vaem_index_error_handling(self):
        """Test ERRORHANDLING index value."""
        assert VaemIndex.ERRORHANDLING.value == 0x2D

    def test_vaem_index_current_reduction_time(self):
        """Test CURRENTREDUCTIONTIME index value."""
        assert VaemIndex.CURRENTREDUCTIONTIME.value == 0x2E

    def test_vaem_index_members(self):
        """Test VaemIndex has all expected members."""
        members = [member.name for member in VaemIndex]
        assert "CONTROLWORD" in members
        assert "STATUSWORD" in members
        assert "INRUSHCURRENT" in members
        assert "HOLDINGCURRENT" in members
        assert "SWITCHINGTIME" in members
        assert "PICKUPTIME" in members
        assert "OPERATINGMODE" in members

    def test_vaem_index_uniqueness(self):
        """Test that all VaemIndex values are unique."""
        values = [member.value for member in VaemIndex]
        assert len(values) == len(set(values))


class TestVaemControlWords:
    """Test VaemControlWords enum."""

    def test_vaem_control_words_start_valves(self):
        """Test STARTVALVES control word value."""
        assert VaemControlWords.STARTVALVES.value == 0x01

    def test_vaem_control_words_stop_valves(self):
        """Test STOPVALVES control word value."""
        assert VaemControlWords.STOPVALVES.value == 0x04

    def test_vaem_control_words_reset_errors(self):
        """Test RESETERRORS control word value."""
        assert VaemControlWords.RESETERRORS.value == 0x08

    def test_vaem_control_words_start_and_reset(self):
        """Test STARTVALVESRESETERROR control word value."""
        expected = VaemControlWords.STARTVALVES.value + VaemControlWords.RESETERRORS.value
        assert VaemControlWords.STARTVALVESRESETERROR.value == expected
        assert VaemControlWords.STARTVALVESRESETERROR.value == 0x09

    def test_vaem_control_words_members(self):
        """Test VaemControlWords has all expected members."""
        members = [member.name for member in VaemControlWords]
        assert "STARTVALVES" in members
        assert "STOPVALVES" in members
        assert "RESETERRORS" in members
        assert "STARTVALVESRESETERROR" in members

    def test_vaem_control_words_bitwise_operations(self):
        """Test bitwise operations on control words."""
        combined = VaemControlWords.STARTVALVES | VaemControlWords.RESETERRORS
        assert combined == 0x09


class TestVaemOperatingMode:
    """Test VaemOperatingMode enum."""

    def test_vaem_operating_mode_opmode1(self):
        """Test OPMODE1 operating mode value."""
        assert VaemOperatingMode.OPMODE1.value == 0x00

    def test_vaem_operating_mode_opmode2(self):
        """Test OPMODE2 operating mode value."""
        assert VaemOperatingMode.OPMODE2.value == 0x01

    def test_vaem_operating_mode_opmode3(self):
        """Test OPMODE3 operating mode value."""
        assert VaemOperatingMode.OPMODE3.value == 0x02

    def test_vaem_operating_mode_members(self):
        """Test VaemOperatingMode has all expected members."""
        members = [member.name for member in VaemOperatingMode]
        assert "OPMODE1" in members
        assert "OPMODE2" in members
        assert "OPMODE3" in members

    def test_vaem_operating_mode_count(self):
        """Test that there are exactly 3 operating modes."""
        modes = list(VaemOperatingMode)
        assert len(modes) == 3

    def test_vaem_operating_mode_sequential_values(self):
        """Test that operating mode values are sequential."""
        modes = [member.value for member in VaemOperatingMode]
        assert modes == [0x00, 0x01, 0x02]


class TestVaemValveIndex:
    """Test vaemValveIndex dictionary."""

    def test_vaem_valve_index_is_dict(self):
        """Test that vaemValveIndex is a dictionary."""
        assert isinstance(vaemValveIndex, dict)

    def test_vaem_valve_index_all_valves_exist(self):
        """Test that all 8 valves are in the index."""
        for valve_id in range(1, 9):
            assert valve_id in vaemValveIndex

    def test_vaem_valve_index_valve_values(self):
        """Test valve index values are correct powers of 2."""
        for i, valve_id in enumerate(range(1, 9)):
            expected_value = 2 ** i
            assert vaemValveIndex[valve_id] == expected_value

    def test_vaem_valve_index_specific_values(self):
        """Test specific valve index values."""
        assert vaemValveIndex[1] == 0x01
        assert vaemValveIndex[2] == 0x02
        assert vaemValveIndex[3] == 0x04
        assert vaemValveIndex[4] == 0x08
        assert vaemValveIndex[5] == 0x10
        assert vaemValveIndex[6] == 0x20
        assert vaemValveIndex[7] == 0x40
        assert vaemValveIndex[8] == 0x80

    def test_vaem_valve_index_all_valves(self):
        """Test AllValves key value."""
        assert vaemValveIndex["AllValves"] == 255

    def test_vaem_valve_index_all_valves_is_or_of_all_valves(self):
        """Test that AllValves is OR of all valve bits."""
        all_valves_calculated = 0
        for valve_id in range(1, 9):
            all_valves_calculated |= vaemValveIndex[valve_id]
        assert vaemValveIndex["AllValves"] == all_valves_calculated

    def test_vaem_valve_index_count(self):
        """Test that vaemValveIndex has expected number of entries."""
        expected_count = 8 + 1  # 8 valves + AllValves
        assert len(vaemValveIndex) == expected_count

    def test_vaem_valve_index_invalid_valve_id_raises_key_error(self):
        """Test that invalid valve ID raises KeyError."""
        with pytest.raises(KeyError):
            _ = vaemValveIndex[0]

    def test_vaem_valve_index_invalid_valve_id_9_raises_key_error(self):
        """Test that valve ID 9 raises KeyError."""
        with pytest.raises(KeyError):
            _ = vaemValveIndex[9]

    def test_vaem_valve_index_bitwise_operations(self):
        """Test bitwise operations on valve indices."""
        valve1_and_valve2 = vaemValveIndex[1] | vaemValveIndex[2]
        assert valve1_and_valve2 == 0x03

    def test_vaem_valve_index_bitwise_and(self):
        """Test bitwise AND operations on valve indices."""
        combined = vaemValveIndex[1] | vaemValveIndex[2]
        assert combined & vaemValveIndex[1] == vaemValveIndex[1]


class TestHelperIntegration:
    """Test integration of helper enums and values."""

    def test_access_values_used_for_operations(self):
        """Test that access values can be used for read/write operations."""
        read_access = VaemAccess.READ.value
        write_access = VaemAccess.WRITE.value
        assert read_access == 0
        assert write_access == 1
        assert read_access != write_access

    def test_index_values_for_communication(self):
        """Test that index values can be used in communication."""
        indices = [VaemIndex.STATUSWORD.value, VaemIndex.CONTROLWORD.value]
        assert all(isinstance(idx, int) for idx in indices)

    def test_data_type_values_for_frame_construction(self):
        """Test that data type values can be used in frames."""
        data_types = [
            VaemDataType.UINT8.value,
            VaemDataType.UINT16.value,
            VaemDataType.UINT32.value,
        ]
        assert len(data_types) == 3
        assert all(isinstance(dt, int) for dt in data_types)

    def test_control_words_for_operations(self):
        """Test control words can be combined for complex operations."""
        start_and_reset = (
            VaemControlWords.STARTVALVES.value | VaemControlWords.RESETERRORS.value
        )
        assert start_and_reset == 0x09

    def test_operating_modes_for_device_configuration(self):
        """Test operating modes can be used for device configuration."""
        modes = [
            VaemOperatingMode.OPMODE1.value,
            VaemOperatingMode.OPMODE2.value,
            VaemOperatingMode.OPMODE3.value,
        ]
        assert all(isinstance(mode, int) for mode in modes)

    def test_valve_index_for_selection(self):
        """Test valve indices can be used for valve selection."""
        for valve_id in range(1, 9):
            valve_bit = vaemValveIndex[valve_id]
            assert isinstance(valve_bit, int)
            assert valve_bit > 0
