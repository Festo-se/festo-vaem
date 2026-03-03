from os import getenv
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
