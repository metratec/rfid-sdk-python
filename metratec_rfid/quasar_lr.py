"""Metratec QuasarLR HF reader
"""
from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .connection.socket_connection import SocketConnection
from .reader_exception import RfidReaderException
from .hf_reader_ascii import HfReaderAscii


@ExpectedReaderInfo("QuasarLR", "QuasarLR", 2.2)
class QuasarLR(HfReaderAscii):
    """Metratec QuasarLR class
    """

    def __init__(self, instance: str, hostname: str = "", port: int = 10001, serial_port: str = "") -> None:
        """Create a new QuasarLR object.

        If the reader is connected via an Ethernet cable, the hostname
        attribute must be set. If the reader is connected via a USB cable,
        the serial port must be set.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            hostname (str, optional): The hostname of the reader.

            port (int): The TCP connection port of the reader, defaults to 10001.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        if hostname == "" and serial_port == "":
            raise RfidReaderException("IP address or serial port must be set")
        super().__init__(instance,
                         SerialConnection(serial_port) if serial_port != "" else SocketConnection(hostname, port))

    async def set_antenna_multiplex(self, antennas: int, switch_delay: int = 0) -> None:
        await self._set_command("SAP", "AUT", antennas)
        self._config['multiplexing_antennas'] = antennas
        self._config['antenna_mode'] = "MULTIPLEX"
