# Release Notes

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
