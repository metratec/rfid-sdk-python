"""metratec DeskID UHF
"""


from .reader import ExpectedReaderInfo
from .connection.serial_connection import SerialConnection
from .uhf_reader_ascii import UhfReaderAscii
from .uhf_reader_at import UhfReaderAT


@ExpectedReaderInfo("DESKID_UHF", "DESKID_UHF", 3.15)
class DeskIdUhf(UhfReaderAscii):
    """metraTec DeskID Uhf
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskIdUhf object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0


@ExpectedReaderInfo("DeskID_UHF_v2_E", "DeskID_UHF_v2_E", 1.0)
class DeskIdUhf2(UhfReaderAT):
    """metraTec DeskID Uhf
    """

    def __init__(self, instance: str, serial_port: str) -> None:
        """Create a new DeskIdUhf object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """
        super().__init__(instance, SerialConnection(serial_port))
        self._config["heartbeat"] = 0

    async def set_power(self, power: int) -> None:
        """Sets the antenna power of the reader for all antennas

        Args:
            power (int): antenna power in dbm [0,9]

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await super().set_power(power)

    async def get_power(self) -> int:
        """Return the current power level

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the current power level
        """
        return await super().get_power()
