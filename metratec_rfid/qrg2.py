"""Metratec QRG2 UHF reader
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .uhf_reader_at import UhfReaderAT


class QRG2Base(UhfReaderAT):
    """Metratec QRG2 base class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new QRG2 object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0

    async def set_power(self, power: int) -> None:
        """Set the antenna power of the reader.

        Args:
            power (int): Power value in dBm [0,9].

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await super().set_power(power)


@ExpectedReaderInfo("QRG2_ETSI", "QRG2_ETSI", 1.0)
class QRG2(QRG2Base):
    """Metratec QRG2 (ETSI) class
    """


@ExpectedReaderInfo("QRG2_FCC", "QRG2_FCC", 1.0)
class QRG2FCC(QRG2Base):
    """Metratec QRG2 (FCC) class
    """
