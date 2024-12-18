.. currentmodule:: metratec_rfid

.. _transponder:

Transponder
===========

Reader functions that operate on tags usually return a list of Tag objects.
These objects contain all available data of each individual
transponder and information about the command execution.

There are two different classes, one for UHF readers and for HF readers.

UHF Transponder
---------------

This class is returned by most inventory-related functions of UHF readers.

.. autoclass:: metratec_rfid.UhfTag
    :members: get_id, get_epc, get_rssi, get_data, get_antenna,
      get_error_message, get_first_seen, get_last_seen, get_tid,
      has_error, get_seen_count

HF Transponder
--------------

This class is returned by most inventory-related functions of HF readers.

.. autoclass:: metratec_rfid.HfTag
    :members: get_id, get_data, get_antenna, get_error_message,
      get_first_seen, get_last_seen, get_tid, has_error, get_seen_count

HF Tag Info
^^^^^^^^^^^

This class is returned by some functions of specific HF readers
(DeskID ISO, QuasarLR, QuasarMX).

It inherits the basic `HfTag` and all of its members but additionally
implements the listed methods.

.. autoclass:: metratec_rfid.HfTagInfo
    :members: is_dsfid, get_dsfid, is_afi, get_afi, is_vicc,
      get_vicc_number_of_block, get_vicc_block_size, is_icr, get_icr

ISO14443-A Tag
^^^^^^^^^^^^^^

This class is returned by NFC readers (DeskID NFC, QR-NFC), depending
on their mode setting.

It inherits the basic `HfTag` and all of its members but additionally
implements the listed methods.

.. autoclass:: metratec_rfid.ISO14ATag
    :members: get_sak, get_atqa

ISO15693 Tag
^^^^^^^^^^^^

This class is returned by NFC readers (DeskID NFC, QR-NFC), depending
on their mode setting.

It inherits the basic `HfTag` and all of its members but additionally
implements the listed methods.

.. autoclass:: metratec_rfid.ISO15Tag
    :members: get_dsfid
