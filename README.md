# RFID SDK Python

An Asyncio based library to control Metratec RFID readers with Python 3.

## Using the Library

### Create virtual environment

To use the library without installing it into your global Python packages, you can create a virtual environment.

#### Linux

* Create virtual environment in the subfolder env: `python3 -m venv env`  
* Activate the virtual environment: `source env/bin/activate`  
(* Deactivate: `deactivate`)

#### Windows

* Create virtual environment in the subfolder env: `python -m venv env`  
* Activate the virtual environment: `env\Scripts\activate.bat`  
(* Deactivate: `env\Scripts\deactivate.bat`)

### Install the library

To install this library call the setup.py file with the following command:

`python setup.py install`

### Call the example files

Go into the "example" folder and call in the console following command:

`python inventory_simple_deskid_iso.py`

### Uninstall library

* `python -m pip uninstall metratec_rfid`

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
