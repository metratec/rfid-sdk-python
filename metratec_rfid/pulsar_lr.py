"""Pulsar LR class
"""

from typing import Any, Dict, List, Union

from .reader import ExpectedReaderInfo
from .reader_exception import RfidReaderException
from .connection.socket_connection import SocketConnection
from .uhf_reader_at import UhfReaderAT


class PulsarLRBase(UhfReaderAT):
    """Pulsar LR"""

    def __init__(self, instance: str, address: str, port: int = 10001) -> None:
        """Create a new PulsarLR object

        Args:
            instance (str): The reader name

            serial_port (str): The serial port to use

        """

        super().__init__(instance, SocketConnection(address, port))

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

    async def set_antenna_multiplex(self, antennas: Union[int, List[int]]) -> None:
        """Number of antennas to be multiplexed

        Args:
            antennas (int or List): Number of antennas to be multiplexed or the antenna sequence list

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if isinstance(antennas, int):
            await self._send_command("AT+MUX", antennas)
        elif isinstance(antennas, List):
            await self._send_command("AT+MUX", *antennas)

    async def get_antenna_multiplex(self) -> List[int]:
        """Gets the antenna multiplex sequence

        Returns:
            sequence (List[int]): the antenna sequence

        Raises:
            RfidReaderException: if an error occurs
        """
        responses: List[str] = await self._send_command("AT+MUX?")
        # +MUX: 1,2,3,....
        data: List[str] = responses[0][6:].split(',')
        if len(data) == 1:
            return [int(i) for i in data]
        return list(map(int, data))

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

    async def set_antenna_powers(self, antenna_powers: List[int]) -> None:
        """set the power values for the antennas

        Args:
            antenna_powers (List[int]): list with the multiplexer size for each antenna
            (the index 0 corresponds to the antenna 1)
        """
        await self._send_command("AT+PWR", *antenna_powers)

    async def get_high_on_tag_output(self) -> Dict[str, Any]:
        """Return the current high on tag output pin

        Returns:
            dict: with 'enable', 'pin' and 'duration' entries
        """
        responses = await self._send_command("AT+HOT?")
        # +HOT: 1
        # +HOT: OFF
        data: List[str] = responses[0][6:].split(',')
        if data[0] == 'OFF':
            return {'enable': False}
        # return int(data[0]), int(data[1])
        return {'enable': True, 'pin': int(data[0]), 'duration': int(data[1])}

    async def set_high_on_tag_output(self, output_pin: int, duration: int = 100):
        """Enable the "high on tag" feature which triggers the selected output to go to the "high" state,
        when a tag is found. This allows to trigger an external device whenever a tag is in the field.
        This corresponds to the blue LED.

        Args:
            output_pin (int): Output pin [1,4]
            duration (int, optional): High duration in milliseconds [10, 10000]. Defaults to 100.
        """
        await self._send_command("AT+HOT", output_pin, duration)

    async def disable_high_on_tag(self):
        """Disable the "high on tag" feature
        """
        await self._send_command("AT+HOT", 0)

    async def call_impinj_authentication_service(self) -> List[Dict[str, Any]]:
        """This command tags to an Impinj M775 tag using the proprietory authencation command.
        It sends a random challenge to the transponder and gets the authentication payload in return.
        You can use this to check the authenticity of the transponder with Impinj Authentication Service.
        For further details, please contact Impinj directly.

        Raises:
            RfidReaderException: if an error occurs

        Returns:
            List[Dict[str, Any]]: a list with the transponders. The transponders contains the keys:
            'epc', 'has_error','short_tid', 'response', 'challenge'
        """
        responses: List[str] = await self._send_command("AT+IAS")
        # +IAS: EPC,OK,SHORT_TID,RESPONSE,CHALLENGE
        # +IAS: EPC,ERROR
        # +IAS: <NO TAGS FOUND>
        tags: List[Dict[str, Any]] = []
        try:
            if responses[0][6] == '<':
                if responses[0][7] == 'N':  # NO TAGS FOUND
                    return tags
                raise RfidReaderException(responses[0][7:-1])
            for response in responses:
                data: List[str] = response[6:].split(',')
                if data[1] == 'OK':
                    tags.append({'epc': data[0], 'has_error': False, 'short_tid': data[2], 'response': data[3],
                                'challenge': data[4]})
                else:
                    tags.append({'epc': data[0], 'has_error': True, 'message': data[1]})
            return tags
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+IAS? - {responses}") from exc

    async def get_selected_session(self) -> str:
        """Returns the current selected session. See set_selected_session for more details.

        Returns:
            str: the current selected session
        """
        responses: List[str] = await self._send_command("AT+SES?")
        # +SES: AUTO
        return responses[0][6:]

    async def set_selected_session(self, session: str = "AUTO"):
        """Manually select the session according to the EPC Gen 2 Protocol to use during inventory scan.
        Default value is "auto" and in most cases this should stay auto.
        Only change this if you absolutely know what you are doing and if you can control the types of tags you scan.
        Otherwise, unexpected results during inventory scans with "only new tags" active might happen.

        Args:
            session (str, optional): Session to set ["0", "1", "2", "3", "AUTO"]. Defaults to "AUTO".

        """
        await self._send_command("AT+SES", session)

    async def get_custom_impinj_settings(self) -> Dict[str, Any]:
        """Returns the custom impinj settings. See set_custom_settings for more detail.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'fast_id' and 'tag_focus' entries
        """
        responses: List[str] = await self._send_command("AT+ICS?")
        # +ICS: 0,0
        data: List[str] = responses[0][6:].split(',')
        try:
            config: Dict[str, bool] = {'fast_id': data[0] == '1',
                                       'tag_focus': data[1] == '1'}
            return config
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+ICS? - {responses}") from exc

    async def set_custom_impinj_settings(self, fast_id: bool = False, tag_focus: bool = False) -> None:
        """The RFID tag IC manufacturer Impinj has added two custom features to its tag ICs that are not compatible
        with tag ICs from other manufacturers. Activate these features with this command - but make sure that you
        only use tags with Impinj ICs like Monza6 or M7xx or M8xx series. Tags from other manufacturers will most
        likely not answer at all when those options are active!

        Args:
            fast_id (bool, optional): True, to allows to read the TagID together with the EPC and can speed up getting
            TID data. Defaults to False.

            tag_focus (bool, optional): True, to use a proprietory tag feature where each tag only answers once until
            it is repowered. This allows to scan a high number of tags because each tag only answers once and makes
            anti-collision easier for the following tags.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await self._send_command("AT+ICS", 1 if fast_id else 0, 1 if tag_focus else 0)

    async def get_rf_mode(self) -> int:
        """Return the rf mode id. Each mode ID corresponds to a set of RF parameters that fit together.
        Not all devices support all modes and not all modes can be access in all regions.
        See reader description for more detail.

        Returns:
            int: the current rf mode id
        """
        responses: List[str] = await self._send_command("AT+RFM?")
        # +RFM: 223
        return int(responses[0][6:])

    async def set_rf_mode(self, mode_id: int) -> None:
        """Configure the internal RF communication settings between tag and reader. Each mode ID corresponds
        to a set of RF parameters that fit together. Not all devices support all modes and not all modes can
        be access in all regions.
        See reader description for more detail.

        Args:
            mode_id (int): the rf mode id to set

        Returns:
            int: the current rf mode id
        """
        await self._send_command("AT+RFM", mode_id)

    ###############################################################################################
    # Internal methods
    ###############################################################################################

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


@ExpectedReaderInfo("PULSAR_LR", "PULSAR_LR", 1.0)
class PulsarLR(PulsarLRBase):
    """Pulsar LR"""
