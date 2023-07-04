"""metratec DeskID UHF
"""


from typing import List

from .reader import ExpectedReaderInfo
from .reader_exception import RfidReaderException
from .connection.serial_connection import SerialConnection
from .uhf_reader_gen1 import UhfReaderGen1
from .uhf_reader_gen2 import UhfReaderGen2


@ExpectedReaderInfo("DESKID_UHF", "DESKID_UHF", 3.15)
class DeskIdUhf(UhfReaderGen1):
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


@ExpectedReaderInfo("DESKID_UHF_V2", "DESKID_UHF_V2", 1.0)
class DeskIdUhf2(UhfReaderGen2):
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
        await self._send_command("AT+PWR", power)

    async def get_power(self) -> int:
        """Return the current power level

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the current power level
        """
        response: List[str] = await self._send_command("AT+PWR?")
        # +PWR: 12
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+PWR? - {response}") from exc
