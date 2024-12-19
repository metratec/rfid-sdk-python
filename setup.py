'''
Setup file for the Metratec RFID SDK
'''
# Always prefer setuptools over distutils
from os import path
from codecs import open  # pylint: disable=redefined-builtin
from setuptools import setup


# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="metratec_rfid",
    version="1.3.4",
    description="Metratec RFID SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.metratec.com/",
    author="Matthias Neumann",
    author_email="neumann@metratec.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=["metratec_rfid", "metratec_rfid.connection"],
    include_package_data=True,
    package_dir={'metratec_rfid': 'metratec_rfid'},
    package_data={'metratec_rfid': ['py.typed', 'connection/py.typed']},
    install_requires=["pyserial==3.5", "pyserial_asyncio==0.6"]
)
