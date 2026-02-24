# VAEM

`festo-vaem` is a python package which allows for driver like capabilites and usage over Festo's 8 Channel Valve controller (VAEM) device.

Documentation can be found [here](https://festo-se.github.io/festo-vaem/). 

Examples can be found [here](https://github.com/Festo-se/festo-vaem/tree/main/examples) and [here](https://festo-se.github.io/festo-vaem/examples/examples)

## Installation

### Release (PENDING)

The lastest released version of this package can be found on the PyPi repo.
Install using pip:

```
pip install festo-vaem
```

### From git repository

The `festo-vaem` source code can also be installed directly from Github. Users can then choose to package it with pip locally if they wish
```
pip install git+https://github.com/Festo-se/festo-vaem.git
```
or using [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
```
uv add "festo-vaem @ git+https://github.com/Festo-se/festo-vaem.git"
```