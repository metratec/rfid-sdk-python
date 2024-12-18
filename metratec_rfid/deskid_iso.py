"""Metratec DeskID ISO HF reader
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .hf_reader_ascii import HfReaderAscii


@ExpectedReaderInfo("DESKID_ISO", "DESKID_ISO", 2.18)
class DeskIdIso(HfReaderAscii):
    """Metratec DeskID ISO class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskID ISO object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0
