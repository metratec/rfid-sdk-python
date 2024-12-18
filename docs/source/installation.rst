Installation
============

.. note::

   This library is known to support Python versions 3.10 and higher.

Requirements
^^^^^^^^^^^^

It is assumed that Python 3 is already installed on the system, including the package installer *pip*.

In case of installation issues, consider upgrading the build tools to the latest version:

.. code:: bash

   pip install -U pip setuptools

Create virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

To use the library without installing it into your global Python packages, it is recommended to use a virtual environment.

Linux / Mac
"""""""""""

* Create virtual environment in the subfolder env: ``python3 -m venv env``  

* Activate the virtual environment: ``source env/bin/activate``

(* Deactivate: ``deactivate``)

Windows
"""""""

* Create virtual environment in the subfolder env: ``python -m venv env`` 

* Activate the virtual environment: ``env\Scripts\activate.bat``

(* Deactivate: ``env\Scripts\deactivate.bat``)

Install RFID SDK
^^^^^^^^^^^^^^^^

Clone the repository and change into its directory: 

.. code:: bash

   git clone https://github.com/metratec/rfid-sdk-python.git
   cd rfid-sdk-python

Preferably check out a release version (see `Github tags <https://github.com/metratec/rfid-sdk-python/tags>`_), for example: 

.. code:: bash

   git checkout r1.3.2

Install the *metratec_rfid* library: 

.. code:: bash

   python -m pip install .

Alternatively, install a specific version from Github directly:

.. code:: bash

   python -m pip install git+https://github.com/metratec/rfid-sdk-python@r1.3.2
