.. Change log

Release Notes
#############

1.4.0
=====

:Release Date: 2025-06-18

* Adds a method for miscellaneous settings to the UHF readers
* Update minimum reader firmware versions

  * DeskID NFC 2.4
  * DeskID UHF ETSI 1.5
  * DeskID UHF FCC 1.6
  * PLRM 1.13
  * PulsarLR 1.6
  * QR NFC 1.3
  * QRG2 ETSI 1.10
  * QRG2 FCC 1.9
  * DWARFG2 V2 1.4
  * DWARFG2 MINI V2 1.5
  * DwarfG2 XR v2 1.4

* PulsarLR: Fixed connecting via hostname
* UHF Gen 2: set_inventory_settings() now supports configuring the
  RSSI threshold.
* Support the reset() method both for ASCII and AT readers
* UhfTag.get_inventory_epc() returns the EPC originally reported
  by the inventory, which may differ from the EPC reported by
  a read operation.
* Python 3.9 is the new minimum supported version
* Fixed repeated calls to UhfReaderAT.set_inventory_settings().
  If not all settings were passed every time the method could fail.

1.3.4
=====

:Release Date: 2024-12-19

* Fixed the send_custom_commands method on legacy readers

1.3.3
=====

:Release Date: 2024-12-19

* Fixed the send_custom_commands method on legacy readers

1.3.2
=====

:Release Date: 2024-11-06

* Fixed read and write requests on legacy readers
* Added new NFC reader features

  * HID keyboard mode
  * NDEF read/write functions

1.3.1
=====

* Reserved memory (RES) usable for read, write and (un)lock
* Added `NfcMode` enum of NfcReaderAT to public module
* Added automatic reader detection (USB)

1.3.0
=====

:Release Date: 2024-09-16

* Added new reader classes
* Updated class and method descriptions
* Updated code examples
* Added new UHF reader features

  * Select tag function
  * Short range and protected mode
  * Channel mask settting
  * Device temperature query

* Various bugfixes and improved error handling

1.2.0
=====

:Release Date: 2023-10-19

* nfc reader added (DeskID NFC)
* transponder exceptions added
* tag getter and setter methods updated
* uhf ascii reader - inventory bug fixed
* uhf at reader

  * phase information now available
  * mask commands updated

1.1.3
=====

:Release Date: 2023-10-19

* UHF Acsii reader - Memory Access Errors will now be handled correctly

1.1.2
=====

:Release Date: 2023-10-16

* UHF Acsii reader - reading the reserved transponder memory now works as expected

1.1.1
=====

:Release Date: 2023-09-29

* reader type check updated
* bug fixes

1.1.0
=====

:Release Date: 2023-08-30

* Reader GRU300 and QRG2 added
* special impinj tag methods added
* bug fixes
* send_custom_command method added

1.0.0
=====

:Release Date: 2023-07-07

Version 1.0 is the public release of the project, under the terms of the `MIT license`.


0.3.2
=====

* UHF Reader Gen2 - write epc method also update the tag epc length

0.3.1
=====

:Release Date: 2023-07-06

* UHF Reader Gen2 - read_tag_data correctly stores the read values as data in the returned transponder

0.3.0
=====

:Release Date: 2023-07-04

Supports following Metratec rfid readers:

* HF Reader

  * DeskID Iso

  * QuasarMx

  * QuasarLR

* UHF Reader

  * DeskID UHF

  * PulsarMX

  * PulsarLR