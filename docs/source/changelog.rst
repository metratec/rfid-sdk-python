.. Change log

Release Notes
#############

1.3.0
=====

:Release Date: TBD

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