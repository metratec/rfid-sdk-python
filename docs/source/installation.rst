Installation
============

.. note::

   This library is known to support Python versions 3.9 and higher.

Basic Installation
------------------

Installing PyLink with **pip**:

.. code:: bash

   $ pip install metratec_rfid


Building From Source
--------------------

Clone the project into a local repository, then navigate to that directory and run:

.. code:: bash

   $ python setup.py install

This will give you the tip of **main** (the development branch).  While we
strive for this to be stable at all times, some bugs may be introduced, so it is
best to check out a release branch first before installing.

.. code:: bash

   $ git checkout r{major}.{minor}.{patch}
   $ python setup.py install

