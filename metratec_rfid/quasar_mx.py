"""Metratec QuasarMX HF reader
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .connection.socket_connection import SocketConnection
from .reader_exception import RfidReaderException
from .hf_reader_ascii import HfReaderAscii


@ExpectedReaderInfo("QUASAR_MX", "QUASAR_MX", 2.18)
class QuasarMX(HfReaderAscii):
    """Metratec QuasarMX class
    """

    def __init__(self, instance: str, hostname: str = "", port: int = 10001, serial_port: str = "") -> None:
        """Create a new QuasarMX object.

        If the reader is connected via an Ethernet cable, the hostname
        attribute must be set. If the reader is connected via a USB cable,
        the serial port must be set.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            hostname (str): The hostname of the reader.

            port (int): The TCP connection port of the reader, defaults to 10001.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

    """
        if hostname == "" and serial_port == "":
            raise RfidReaderException("IP address or serial port must be set")
        super().__init__(instance,
                         SerialConnection(serial_port) if serial_port != "" else SocketConnection(hostname, port))
