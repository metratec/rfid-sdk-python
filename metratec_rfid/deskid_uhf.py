"""Metratec DeskID UHF legacy and v2 UHF readers
"""

from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .uhf_reader_ascii import UhfReaderAscii
from .uhf_reader_at import UhfReaderAT
from .reader_at import ReaderATSound


@ExpectedReaderInfo("DESKID_UHF", "DESKID_UHF", 3.15)
class DeskIdUhf(UhfReaderAscii):
    """Metratec DeskID UHF (legacy) class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskID UHF (legacy) object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0


class DeskIdUhfv2Base(UhfReaderAT, ReaderATSound):
    """Metratec DeskID UHF v2 base class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskID UHF v2 object.

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


@ExpectedReaderInfo("DeskID_UHF_v2_E", "DeskID_UHF_v2_E", 1.0)
class DeskIdUhfv2(DeskIdUhfv2Base):
    """Metratec DeskID UHF v2 (ETSI) class
    """


@ExpectedReaderInfo("DeskID_UHF_v2_F", "DeskID_UHF_v2_F", 1.0)
class DeskIdUhfv2FCC(DeskIdUhfv2Base):
    """Metratec DeskID UHF v2 (FCC) class
    """
