"""
This file contains software utility functions that are not directly related
to reader functionality and are thus independent from the reader objects.
"""

import importlib
from serial.tools import list_ports

from .reader_at import ReaderAT
from .reader_ascii import ReaderAscii
from .reader_exception import RfidReaderException
from .connection.serial_connection import SerialConnection


# firmware name to reader class lookup table
FW_READER_LUT = {
        # UHF ASCII reader (legacy)
        "DESKID_UHF": importlib.import_module("metratec_rfid.deskid_uhf").DeskIdUhf,
        "PULSAR_MX": importlib.import_module("metratec_rfid.pulsar_mx").PulsarMX,
        # HF ASCII reader (legacy)
        "DESKID_ISO": importlib.import_module("metratec_rfid.deskid_iso").DeskIdIso,
        "QuasarLR": importlib.import_module("metratec_rfid.quasar_lr").QuasarLR,
        "QUASAR_MX": importlib.import_module("metratec_rfid.quasar_mx").QuasarMX,
        # UHF AT reader
        "PULSAR_LR": importlib.import_module("metratec_rfid.pulsar_lr").PulsarLR,
        "PLRM": importlib.import_module("metratec_rfid.plrm").Plrm,
        "DeskID_UHF_v2_E": importlib.import_module("metratec_rfid.deskid_uhf").DeskIdUhfv2,
        "DeskID_UHF_v2_F": importlib.import_module("metratec_rfid.deskid_uhf").DeskIdUhfv2FCC,
        "QRG2_ETSI": importlib.import_module("metratec_rfid.qrg2").QRG2,
        "QRG2_FCC": importlib.import_module("metratec_rfid.qrg2").QRG2FCC,
        "DwarfG2_v2": importlib.import_module("metratec_rfid.dwarfg2_v2").DwarfG2v2,
        "DwarfG2-Mini_v2": importlib.import_module("metratec_rfid.dwarfg2_v2").DwarfG2Miniv2,
        "DwarfG2_XR_v2": importlib.import_module("metratec_rfid.dwarfg2_v2").DwarfG2XRv2,
        # NFC AT reader
        "DeskID_NFC": importlib.import_module("metratec_rfid.deskid_nfc").DeskIdNfc,
        "QR_NFC": importlib.import_module("metratec_rfid.qr_nfc").QrNfc,
    }


async def detect_readers(port_re="USB", verbose=False, legacy=False):
    """
    Detect Metratec RFID readers connected to the system via USB.

    The RFID readers cannot be identified by USB information alone, therefore
    this function will try to establish a connection on all potential ports
    and query the reader firmware information by sending a command.

    Make sure this process does not interrupt any other serial devices
    that may be connected to your PC.

    Args:
        port_re (str, optional): Regular expression for filtering ports. Defaults to "USB".
        verbose (bool, optional): Whether to print debug information. Defaults to False.
        legacy (bool, optional): Whether to include legacy reader support. Defaults to False.

    Returns:
        dict: Dictionary mapping port names to reader objects.
    """
    # FIXME USB vs embedded serial -> include both in re
    # disable 'expression-not-assigned' warning - pylint: disable=W0106

    # get list of ports where port name, description or hardware ID match port_re
    ports = list(list_ports.grep(port_re))
    print(f"Found {len(ports)} ports matching '{port_re}'") if verbose else lambda: None

    # must use different reader class for legacy readers to get reader info
    classes = {}
    for port in ports:
        p = port[0]
        reader = ReaderAT("", SerialConnection(p))
        classes[p] = [reader]

        if legacy:
            reader = ReaderAscii("", SerialConnection(p))
            classes[p].append(reader)

    # determine on which port an RFID is connected
    readers = {}
    for p, reader_list in classes.items():
        # try to open a connection and query device information
        info = None
        for reader in reader_list:
            print(f"Try {type(reader).__name__} connection on port {p}") if verbose else lambda: None
            reader.get_logger().setLevel("WARNING" if verbose else "CRITICAL")
            try:
                await reader.connect(timeout=3.0)
                info = await reader.get_reader_info()
                await reader.disconnect()
                break
            except RfidReaderException as e:
                # connection failed or unexpected reader info
                print(e) if verbose else lambda: None

        # create reader object from firmware name
        if info is None:
            continue
        fwname = info["firmware"]
        try:
            reader = FW_READER_LUT[fwname](fwname, p)
        except KeyError:
            # firmware name not contained in LUT
            print(f"WARNING: Unknown reader firmware on port {p}: {fwname}")
            continue

        # add reader object to output
        readers[p] = reader

    return readers
