# RFID SDK Python

An Asyncio based library to control Metratec RFID readers with Python 3.

## Using the Library

### Create virtual environment

* Create virtual environment in the subfolder env: `python3 -m venv env`  
* Activate the virtual environment: `source env/bin/activate`  
(* Deactivate: `deactivate`)

### Build the library

``` bash
# install dependencies
pip install wheel twine setuptools

# build library
python setup.py sdist bdist_wheel
```

### Install the library

* `python -m pip install wheel`
* `python -m pip install metratec_rfid-0.3.0.tar.gz`

### Call the example files

Go into the "example" folder and call in the console following command:

`python inventory_simple_deskid_iso.py`

### Uninstall library

* `python -m pip uninstall metratec_rfid`
