"""Pulsar LR class
"""

from typing import List

from .reader import ExpectedReaderInfo
from .reader_exception import RfidReaderException
from .connection.socket_connection import SocketConnection
from .uhf_reader_gen2 import UhfReaderGen2


@ExpectedReaderInfo("PULSAR_LR", "PULSAR_LR", 1.0)
class PulsarLR(UhfReaderGen2):
    """Pulsar LR"""

    def __init__(self, instance: str, address: str, port: int = 10001) -> None:
        """Create a new PulsarLR object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """

        super().__init__(instance, SocketConnection(address, port))

    async def _get_connected_multiplexer(self) -> List[int]:
        """the configured multiplexer size per antenna (index 0 == antenna 1)

        Returns:
            List[int]: with the configured multiplexer size
        """
        responses: List[str] = await self._send_command("AT+EMX?")
        # +EMX: 3,0,0,0
        data: List[str] = responses[0][6:].split(',')
        return [int(i) for i in data]

    async def _set_connected_multiplexer(self, connected_multiplexer: List[int]) -> None:
        """define the connected multiplexer

        Args:
            connected_multiplexer (List[int]): list with the multiplexer size for each antenna
        """
        await self._send_command("AT+EMX", *connected_multiplexer)

    async def get_multiplexer(self, antenna_port: int) -> int:
        """Get the connected multiplexer (connected antennas per antenna port)

        Args:
            antenna_port (int): the antenna port to which the multiplexer is connected

        Raises:
            RfidReaderException: if an error occurs

        Returns:
            int: the multiplexer size
        """
        if 1 > antenna_port or antenna_port > 5:
            raise RfidReaderException(f"Wrong antenna port {antenna_port} - [1,4] expected")
        connected_multiplexer = await self._get_connected_multiplexer()
        return connected_multiplexer[antenna_port - 1]

    async def set_multiplexer(self, antenna_port: int, multiplexer_size: int):
        """Sets the connected multiplexer (connected antennas per antenna port)

        Args:
            antenna_port (int): the antenna port to which the multiplexer is connected
            multiplexer_size (int): the multiplexer size

        Raises:
            RfidReaderException: if an error occurs
        """
        if 1 > antenna_port or antenna_port > 5:
            raise RfidReaderException(f"Wrong antenna port {antenna_port} - [1,4] expected")
        connected_multiplexer = await self._get_connected_multiplexer()
        connected_multiplexer[antenna_port - 1] = multiplexer_size
        await self._set_connected_multiplexer(connected_multiplexer)

    async def set_antenna_multiplex_sequence(self, sequence: List[int]) -> None:
        """Sets the antenna multiplex sequence

        Raises:
            RfidReaderException: if an error occurs

        Returns:
            sequence (List[int]): the antenna sequence
        """
        await self._send_command("AT+MUX", *sequence)

    async def get_antenna_multiplex_sequence(self) -> List[int]:
        """Gets the antenna multiplex sequence

        R:
            sequence (List[int]): the antenna sequence

        Raises:
            RfidReaderException: if an error occurs
        """
        responses: List[str] = await self._send_command("AT+MUX?")
        # +MUX: 1,2,3,....
        data: List[str] = responses[0][6:].split(',')
        if len(data) == 1:
            raise RfidReaderException("No multiplex sequence activated")
        # return [int(i) for i in data]
        return list(map(int, data))

    async def get_antenna_multiplex(self) -> int:
        responses: List[str] = await self._send_command("AT+MUX?")
        # +MUX: 4
        try:
            data: List[str] = responses[0][6:].split(',')
            if len(data) > 1:
                raise RfidReaderException("a multiplex sequence is activated, please use " +
                                          "'get_antenna_multiplex_sequence' command")
            return int(data[0])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+MUX? - {responses}") from exc

    async def get_antenna_powers(self) -> List[int]:
        """the power value per antenna (index 0 == antenna 1)

        Returns:
            List[int]: list with the power values
        """
        responses: List[str] = await self._send_command("AT+PWR?")
        # +PWR: 12,12,12,12
        data: List[str] = responses[0][6:].split(',')
        # return [int(i) for i in data]
        return list(map(int, data))

    async def set_antenna_powers(self, antenna_powers: List[int]) -> None:
        """set the power values for the antennas

        Args:
            antenna_powers (List[int]): list with the multiplexer size for each antenna
            (the index 0 corresponds to the antenna 1)
        """
        await self._send_command("AT+PWR", *antenna_powers)

    async def set_antenna_power(self, antenna: int, power: int) -> None:
        """Sets the antenna power

        Args:
            antenna (int): antenna
            power (int): antenna power in dbm [0,30]

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if antenna <= 0:
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers = await self.get_antenna_powers()
        if antenna > len(powers):
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers[antenna - 1] = power
        await self.set_antenna_powers(powers)

    async def get_antenna_power(self, antenna: int) -> int:
        """Return the current antenna power

        Args:
            antenna (int): antenna

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the current antenna power
        """
        powers = await self.get_antenna_powers()
        try:
            return powers[antenna - 1]
        except IndexError as exc:
            raise RfidReaderException(f"Antenna {antenna} not available") from exc
