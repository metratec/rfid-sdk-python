.. currentmodule:: metratec_rfid

.. _deskidnfc:

DeskID NFC Desktop Reader
=========================

.. image:: ./../../_static/deskid-hf.jpg
   :alt: DeskId NFC
   :align: right

With the DeskID NFC Metratec presents its first multi-protocol RFID reader/writer device. The slim housing looks good on every desktop and
can read and write any 13.56 MHz RFID transponder. This includes ISO15693 tags (NFC Type 5) and all ISO14443-based transponders including
all products from the NXP Mifare® series. This includes not only Mifare Classic and Ultralight® but also NTAG transponders as well as the
very secure Mifare DESFire® tags.

.. autoclass:: metratec_rfid.DeskIdNfc
    :members:
    :inherited-members:
    :special-members: __init__
    :exclude-members: check_antennas, enable_input_events, get_antenna, get_antenna_multiplex, get_input, get_inputs, get_inventory_multi, get_output, get_outputs, set_antenna, set_antenna_multiplex, set_cb_input_changed, set_output, set_outputs, start_inventory_multi, stop_inventory_multi