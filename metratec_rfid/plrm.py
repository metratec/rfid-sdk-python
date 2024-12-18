"""Metratec PLRM UHF reader
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .uhf_reader_at import UhfReaderATMulti


class PlrmBase(UhfReaderATMulti):
    """Metratec PLRM base class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new PLRM object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0


@ExpectedReaderInfo("PLRM", "PLRM", 1.0)
class Plrm(PlrmBase):
    """Metratec PLRM class
    """
