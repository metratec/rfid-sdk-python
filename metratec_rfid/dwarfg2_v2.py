"""Metratec DwarfG2 v2 UHF reader
"""

from .reader import ExpectedReaderInfo
from .reader_at import ReaderATIO
from .connection.serial_connection import SerialConnection
from .uhf_reader_at import UhfReaderATMulti


class DwarfG2v2Base(UhfReaderATMulti, ReaderATIO):
    """Metratec DwarfG2 v2 base class
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DwarfG2 v2 object.

        Args:
            instance (str): The reader name. This is purely for
                identification within the software and can be anything,
                even an empty string.

            serial_port (str): The serial port to use. Leave empty (`""`)
                to determine automatically during `connect()`.

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0


@ExpectedReaderInfo("DwarfG2_v2", "DWARFG2_V2", 1.0)
class DwarfG2v2(DwarfG2v2Base):
    """Metratec DwarfG2 v2 class
    """

    async def set_power(self, power: int) -> None:
        """Set the antenna power of the reader for all antennas.

        Args:
            power (int): Power value in dBm [0,21].

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await super().set_power(power)


@ExpectedReaderInfo("DwarfG2-Mini_v2", "DWARFG2_MINI_V2", 1.0)
class DwarfG2Miniv2(DwarfG2v2Base):
    """Metratec DwarfG2-Mini v2 class
    """

    async def set_power(self, power: int) -> None:
        """Set the antenna power of the reader for all antennas.

        Args:
            power (int): Power value in dBm [0,9].

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await super().set_power(power)


@ExpectedReaderInfo("DwarfG2_XR_v2", "DwarfG2_XR_v2", 1.0)
class DwarfG2XRv2(DwarfG2v2Base):
    """Metratec DwarfG2-XR v2 class
    """

    async def set_power(self, power: int) -> None:
        """Set the antenna power of the reader for all antennas.

        Args:
            power (int): Power value in dBm [0,27].

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await super().set_power(power)
