"""Metratec DeskID NFC reader
"""

from metratec_rfid.nfc_reader_at import NfcReaderAT
from metratec_rfid.reader_at import ReaderATSound
from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection


@ExpectedReaderInfo("DeskID_NFC", "DeskID_NFC", 1.0)
class DeskIdNfc(NfcReaderAT, ReaderATSound):
    """Metratec DeskID NFC class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskID NFC object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0
