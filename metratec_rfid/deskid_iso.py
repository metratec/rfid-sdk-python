"""metratec DeskID ISO HF reader
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .hf_reader_ascii import HfReaderAscii


@ExpectedReaderInfo("DESKID_ISO", "DESKID_ISO", 2.18)
class DeskIdIso(HfReaderAscii):
    """metraTec DeskID Iso Hf reader
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskIdIso object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0
