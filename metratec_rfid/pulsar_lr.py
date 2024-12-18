"""Metratec Pulsar LR UHF reader
"""

from ipaddress import ip_address

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

            port (int): The TCP port to use.

        """
        try:
            # this will raise ValueError if IP address is invalid
            ip_address(address)
            super().__init__(instance, SocketConnection(address, port))
        except ValueError:
            super().__init__(instance, SerialConnection(address))


@ExpectedReaderInfo("PULSAR_LR", "PULSAR_LR", 1.0)
class PulsarLR(PulsarLRBase):
    """Metratec Pulsar LR class
    """
