# Release Notes

## 1.3.4

* Fixed the send_custom_commands method on legacy readers

## 1.3.3

* Fixed the send_custom_commands method on legacy readers

## 1.3.2

* Fixed read and write requests on legacy readers
* Added new NFC reader features
  * HID keyboard mode
  * NDEF read/write functions

## 1.3.1

* Reserved memory (RES) usable for read, write and (un)lock
* Added `NfcMode` enum of NfcReaderAT to public module
* Added automatic reader detection (USB)

## 1.3.0

* Added new reader classes
* Updated class and method descriptions
* Updated code examples
* Added new UHF reader features
  * Select tag function
  * Short range and protected mode
  * Channel mask settting
  * Device temperature query
* Various bugfixes and improved error handling

## 1.2.0

* nfc reader added
* transponder exceptions added
* tag getter and setter methods updated
* uhf ascii reader - inventory bug fixed
* uhf at reader
  * phase information now available
  * mask commands updated

## 1.1.3

* Gen1 UHF - Memory Access Errors will now be handled correctly

## 1.1.2

* Gen1 UHF - reading the reserved transponder memory now works as expected

## 1.1.1

* reader type check updated
* bug fixes

## 1.1.0

* Gen2 UHF
  * reader GRU300 and QRG2 added
  * special impinj tag methods added
  * bug fixes
* send_custom_command method added

## 1.0.0

Public release

## 0.3.2

* UHF Reader Gen2 - write epc method also update the tag epc length

## 0.3.1

* UHF Reader Gen2 - read_tag_data correctly stores the read values as data in the returned transponder

## 0.3.0

Supports following Metratec rfid readers:

* HF Reader

  * DeskID Iso

  * QuasarMx

  * QuasarLR

* UHF Reader

  * DeskID UHF

  * PulsarMX

  * PulsarLR
