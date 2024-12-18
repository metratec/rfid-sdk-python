"""Metratec QR NFC reader
"""

from metratec_rfid.nfc_reader_at import NfcReaderAT
from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection


@ExpectedReaderInfo("QR_NFC", "QR_NFC", 1.0)
class QrNfc(NfcReaderAT):
    """Metratec QR NFC class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new QR NFC object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0
