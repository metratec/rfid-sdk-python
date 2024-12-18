# RFID SDK Python

An Asyncio based library to control Metratec RFID readers with Python 3.

## Documentation

The folder `metratec_rfid-doc` contains the HTML documentation of the
library. Simply open the `index.html` file to view it.

## Installation

### Requirements

It is assumed that Python 3 is already installed on the system, including the package installer *pip*.

In case of installation issues, consider upgrading the build tools to the latest version:

```
pip install -U pip setuptools
```

### Create virtual environment

To use the library without installing it into your global Python packages, it is recommended to use a virtual environment.

#### Linux / Mac

* Create virtual environment in the subfolder env: `python3 -m venv env`  
* Activate the virtual environment: `source env/bin/activate`  
(* Deactivate: `deactivate`)

#### Windows

* Create virtual environment in the subfolder env: `python -m venv env`  
* Activate the virtual environment: `env\Scripts\activate.bat`  
(* Deactivate: `env\Scripts\deactivate.bat`)

### Install RFID SDK

The library is packaged into an archive and can be installed via pip:

```
python -m pip install metratec_rfid-1.3.2.tar.gz
```

## Usage

The main part of the library are the reader objects:

- UHF ASCII reader (legacy): `DeskIdUhf`, `PulsarMX`
- HF ASCII reader (legacy): `DeskIdIso`, `QuasarLR`, `QuasarMX`
- UHF AT reader: `PulsarLR`, `Plrm`, `DeskIdUhfv2`, `DeskIdUhfv2FCC`, `QRG2`, `QRG2FCC`, `DwarfG2v2`, `DwarfG2Miniv2`, `DwarfG2XRv2`
- NFC AT reader: `DeskIdNfc`, `QrNfc`

Import the reader class matching your device and create a new object by giving it a name and specifying the connection port.

```python
from metratec_rfid import DeskIdUhfv2
reader = DeskIdUhfv2("MyReader", "COM41")
```

Afterwards, connect the reader once and call whatever reader functions you wish to execute.

```python
await reader.connect()
await reader.get_inventory()
```

See the code examples for complete sample applications and reference the documentation for more info and a complete list of reader methods.

### Example files

The `examples` folder contains sample applications using this library.

#### Minimal example
To get started right away, identify the proper reader class for your device and run the following example. The given arguments are examples and have to be adapted. The first argument must match the reader class name and the second argument specifies the connection port.

```
python examples/inventory_minimal_cmd.py DeskIdUhfv2 /dev/ttyUSB0
```

This will create the appropriate reader object, run a single inventory and print the result.

The following example executes the same reader functions but does not use commandline arguments. It explicitly shows how to import and initialize a single reader object. This means, in order to run this example, you will have to adapt some lines inside the file to fit your device.

```
python examples/inventory_minimal.py
```

#### General examples

The following examples show different base features of the library in isolation.
They all use the same commandline utility as the minimal example and are designed to work with any RFID reader device. 

How to use inventory callbacks:

```
python examples/inventory_callback_example.py DeskIdUhfv2 COM41
```

How to fetch results from a continuous inventory:

```
python examples/inventory_fetch_example.py PulsarLR 192.168.2.153
```

How to change the EPC value of a tag that is specified by its tag ID
(for UHF readers).

```
python examples/write_epc_uhf.py QRG2 /dev/ttyUSB0
```

#### Other examples

Any other examples may only work on specific readers. Take a look at the individual files to learn more.

While many reader methods are shared among different reader types, there are some key differences between them. For a comprehensive list of functions for any specific reader, reference the documentation.

## Uninstalling the library

```
python -m pip uninstall metratec_rfid
```

## License

MIT License

Copyright (c) 2023 metratec GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
