"""Abstracting internal file structure for VAEM package."""

import logging
from vaem.vaem import VAEM
from vaem.vaem_config import VAEMConfig, VAEMSerialConfig, VAEMTCPConfig

# Ensure the package logger is silent by default when used as a library.
logging.getLogger("vaem").addHandler(logging.NullHandler())

__all__ = [
    "VAEM",
    "VAEMConfig",
    "VAEMTCPConfig",
    "VAEMSerialConfig",
]
