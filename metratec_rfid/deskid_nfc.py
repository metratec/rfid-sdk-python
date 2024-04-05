"""metratec DeskID ISO HF reader
"""

from metratec_rfid.nfc_reader_at import NfcReaderAT
from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection


@ExpectedReaderInfo("DeskID_NFC", "DeskID_NFC", 1.0)
class DeskIdNfc(NfcReaderAT):
    """metraTec DeskID NFC reader
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskIdNfc object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0
