"""Metratec Pulsar LR UHF reader
"""

import platform
import re
from .reader import ExpectedReaderInfo
from .reader_at import ReaderATIO
from .connection.socket_connection import SocketConnection
from .connection.serial_connection import SerialConnection
from .uhf_reader_at import UhfReaderATMulti


class PulsarLRBase(UhfReaderATMulti, ReaderATIO):
    """Metratec Pulsar LR base class
    """

    def __init__(self, instance: str, address: str, port: int = 10001) -> None:
        """Create a new PulsarLR object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            address (str): The IP address or serial port of the reader.
                An empty string will try to determine the serial port
                automatically during `connect()`.

            port (int): The TCP port to use.

        """
        try:
            os = platform.system().lower()
            if (os in ("linux", "darwin") and address.strip().startswith("/") or
                    (os == "windows" and re.compile("com[0-9]+").match(address.lower()))):
                super().__init__(instance, SerialConnection(address))
            else:
                super().__init__(instance, SocketConnection(address, port))
        except ValueError:
            super().__init__(instance, SerialConnection(address))


@ExpectedReaderInfo("PULSAR_LR", "PULSAR_LR", 01.06)
class PulsarLR(PulsarLRBase):
    """Metratec Pulsar LR class
    """
