# Changelog

All relevant changes to the VAEM driver package will be documented in this file.

The format is derived from [Keep A Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/)


## [Unreleased]


## [0.1.0] - 2022-2026
### Added

- Unify existing Modbus-based VAEM support libraries into one development stream

- Generate documentation using mkdocs + gitlab pages. API documentation generated automatically usage Python docstrings.

- Separate out unified interface for VAEM commands from the implmentation details in the communication backends (ModbusTCP vs. ModbusSerial)

- Make VAEM communication backend mode dynamically generatable based on a config passed in at runtime 

- Separate out ENUM-type register mappings from communication backend for reliable usage and modification

- Initial pass at tests -- to be developed further in concert with physical infrastructure to test on actual dev-dependencies

- Apply Gitlab CI to test, package, and deplot to Gitlab native PyPI

- Construct usage examples and make usage example configurable usage environment variables for input parameters

- Update project to src directory structure

- Implement usage of modern python tooling, using ruff for linting/formatting and uv for project management and build/deploy

- Rename library install name to "festo-vaem"
