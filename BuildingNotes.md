# Building the library

## Generate the library

For building the library the setup.py script is used.

You need at first install the the python packages wheel,twine and setuptools. You can install them with the following command `python -m pip install wheel twine setuptools`

To build the lib call the command `python setup.py sdist bdist_wheel`

## Generate documentation

The library documentation is generated with the python documentation generator sphinx.

### Requirements

To install sphinx and the special project dependencies call following commands:

```bash
cd docs
python -m pip install -r requirements.txt
```

### Build the documentation

To build the documentation run the command `make html` in the docs folder
