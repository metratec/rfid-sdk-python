"""
This script imports all reader objects and provides utility functions
to create instances based on commandline arguments.

If you write your own applications using this library, it is sufficient
to import the specific reader class you are using.

For example:
reader = DeskIdUhfv2("MyDeskID", "COM41")
"""

import argparse

# UHF ASCII reader (legacy)
from metratec_rfid import DeskIdUhf, PulsarMX
# HF ASCII reader (legacy)
from metratec_rfid import DeskIdIso, QuasarLR, QuasarMX
# UHF AT reader
from metratec_rfid import PulsarLR, Plrm, DeskIdUhfv2, DeskIdUhfv2FCC
from metratec_rfid import QRG2, QRG2FCC, DwarfG2v2, DwarfG2Miniv2, DwarfG2XRv2
# NFC AT reader
from metratec_rfid import DeskIdNfc, QrNfc


HF_READER = {
    "deskidiso": DeskIdIso,
    "deskidnfc": DeskIdNfc,
    "quasarlr": QuasarLR,
    "quasarmx": QuasarMX,
    "qrnfc": QrNfc,
}

UHF_READER = {
    "deskiduhf": DeskIdUhf,
    "pulsarmx": PulsarMX,
    "pulsarlr": PulsarLR,
    "plrm": Plrm,
    "deskiduhfv2": DeskIdUhfv2,
    "deskiduhfv2fcc": DeskIdUhfv2FCC,
    "qrg2": QRG2,
    "qrg2fcc": QRG2FCC,
    "dwarfg2v2": DwarfG2v2,
    "dwarfg2miniv2": DwarfG2Miniv2,
    "dwarfg2xrv2": DwarfG2XRv2
}


def get_reader(hf=True, uhf=True):
    # Create reader list for help text.
    readers = []
    if hf:
        readers.extend(list(HF_READER.keys()))
    if uhf:
        readers.extend(list(UHF_READER.keys()))

    parser = argparse.ArgumentParser(description="Metratec RFID examples")

    # Define positional arguments.
    parser.add_argument("reader", help=f"Reader name, must be one of the \
        following: {readers}")
    parser.add_argument("address", help="Serial port (e.g. '/dev/ttyUSB0' \
        or 'COM41') or IP address (e.g. '192.168.2.153')")

    # Parse arguments.
    args = parser.parse_args()

    # Init and return reader object.
    reader = args.reader.lower()
    if hf and reader in HF_READER.keys():
        return HF_READER[reader](reader, args.address)
    if uhf and reader in UHF_READER.keys():
        return UHF_READER[reader](reader, args.address)
    
    exit(f"ERROR: Use one of the following readers: {readers}")


def get_hf_reader():
    return get_reader(uhf=False)


def get_uhf_reader():
    return get_reader(hf=False)