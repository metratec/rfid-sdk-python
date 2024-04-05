"""metratec Pulsar MX Uhf reader
"""


from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .connection.socket_connection import SocketConnection
from .reader_exception import RfidReaderException
from .uhf_reader_ascii import UhfReaderAscii


@ExpectedReaderInfo("PULSAR_MX", "PULSAR_MX", 3.15)
class PulsarMX(UhfReaderAscii):
    """metraTec Pulsar MX Uhf reader
    """

    def __init__(self, instance: str, hostname: str = "", port: int = 10001, serial_port: str = "") -> None:
        """Create a new PulsarMX instance. If the reader is connected via an Ethernet cable,
        the hostname attribute must be set. If the reader is connected via a USB cable, the serial port must be set.

        Args:
            instance (str): The reader name
            hostname (str): The hostname of the reader
            port (int): the tcp connection port of the reader, defaults to 10001
            serial_port (str): The serial port of the reader

        """
        if hostname == "" and serial_port == "":
            raise RfidReaderException("IP address or serial port must be set")
        super().__init__(instance,
                         SerialConnection(serial_port) if serial_port != "" else SocketConnection(hostname, port))
