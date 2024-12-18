"""
metratec uhf reader gen2
"""

from time import time
from typing import Callable, Optional, Any, Dict, List, Union

from .connection.connection import Connection

from .reader_exception import RfidReaderException
from .reader_at import ReaderAT
from .reader import RfidReader
from .uhf_tag import UhfTag


# disable 'Too many lines in module' warning - pylint: disable=C0302


class UhfReaderAT(ReaderAT):
    """The implementation of the uhf gen2 reader with the **AT-protocol.**
    """

    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes' warning - pylint: disable=R0902
    # disable 'Too many arguments' warning - pylint: disable=R0913

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(instance, connection)
        self._cb_inventory_report: Optional[Callable[[List[UhfTag]], None]] = None
        self._fire_empty_reports = False
        self._config: dict = {}
        self._ignore_errors = False

    # @override
    def set_cb_inventory(self, callback: Optional[Callable[[List[UhfTag]], None]]
                         ) -> Optional[Callable[[List[UhfTag]], None]]:
        """Set the callback for a new inventory.

        Define a callback which will be triggered whenever a new inventory
        result is available. The callback has the following arguments:

        * tags (List[UhfTag]) - List of transponders found in the inventory.

        Args:
            callback (Callable): Reference to the callback function to use.

        Returns:
            Optional[Callable]: The old callback.

        Example:
            >>> def my_callback(tags)
            >>>     for tag in tags:
            >>>         print(tag.get_epc())
            >>> set_cb_inventory(my_callback)
        """
        return super().set_cb_inventory(callback)

    def set_cb_inventory_report(self, callback: Optional[Callable[[List[UhfTag]], None]]
                                ) -> Optional[Callable[[List[UhfTag]], None]]:
        """Set the callback for a new inventory report.

        Define a callback which will be triggered whenever a new inventory
        report is available. The callback has the following arguments:

        * tags (List[UhfTag]) - List of transponders found in the inventory.

        Args:
            callback (Callable): Reference to the callback function to use.

        Returns:
            Optional[Callable]: The old callback.
        """
        old = self._cb_inventory_report
        self._cb_inventory_report = callback
        return old

    def enable_fire_empty_reports(self, enable: bool):
        """En-/disable callbacks for empty inventory reports.

        By default, the event handler for inventory reports, which can be defined
        with `set_cb_inventory_report()`, is not called when a report was
        technically successful but no tags have been found.
        If this is set to `True`, empty reports will also trigger
        the defined callback.

        Args:
            enable (bool): Set to True, to enable empty report events.
        """
        self._fire_empty_reports = enable

    async def set_region(self, region: str) -> None:
        """Set the used UHF region.

        This has to match the region you are in as well as the antenna(s)
        that are connected to the reader.

        Args:
            region (str): The UHF region, e.g. "ETSI" or "FCC".

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+REG", region)

    async def get_region(self) -> str:
        """Return the configured UHF region.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            str: The currently used UHF region.
        """
        response: List[str] = await self._send_command("AT+REG?")
        # +REG: ETSI_LOWER
        try:
            return response[0][6:]
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+REG? - {response}") from exc

    async def set_tag_size(self, tag_size: int, min_tags: int = -1, max_tags: int = -1) -> None:
        """Configure the expected numbers of transponders in the field.

        Alternatively, the `set_q_value()` method can be used.

        Args:
            tag_size (int): Expected number of transponders.

            min_tags (int, optional): Minimum numbers of transponders.

            max_tags (int, optional): Maximum numbers of transponders.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        if not (min_tags >= 0 and max_tags >= 0 or min_tags < 0 and max_tags < 0):
            raise RfidReaderException("Must set both min_tags and max_tags or none of them.")
        q_start: int = 0
        q_min: Optional[int] = None
        q_max: Optional[int] = None
        while tag_size > pow(2, q_start):
            q_start += 1
        if min_tags >= 0:
            q_min = 0
            while min_tags > pow(2, q_min):
                q_min += 1
        if max_tags >= 0:
            q_max = 0
            while max_tags > pow(2, q_max):
                q_max += 1
        await self._send_command("AT+Q", q_start, q_min, q_max)

    async def get_tag_size(self) -> int:
        """Return the configured expected tag size.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            int: The expected number of tags.
        """
        response: List[str] = await self._send_command("AT+Q?")
        # +Q: 4,2,15
        try:
            setting: List[str] = response[0][4:].split(",")
            return pow(2, int(setting[0]))
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+Q? - {response}") from exc

    async def set_q_value(self, q_start: int, q_min: int = -1, q_max: int = -1) -> None:
        """Configure the expected number of transponders in the field as Q value.

        The Q value is the exponent of 2 and the product should be around
        or above the expected number of tags. Setting this value too low
        will result in tags being missed. Setting the value too high will
        lead to unnecessarily slow inventories.

        The value can be adapted automatically during operation, hence
        the three different arguments.

        Alternatively, the `set_tag_size()` method can be used.

        Args:
            q_start (int): Start Q value.

            q_min (int, optional): Minimum Q value.

            q_max (int, optional): Maximum Q value.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        if not (q_min >= 0 and q_max >= 0 or q_max < 0 and q_min < 0):
            raise RfidReaderException("Must set both q_min and q_max or none of the them")
        await self._send_command("AT+Q", q_start, q_min if q_min >= 0 else None, q_max if q_max >= 0 else None,)

    async def get_q_value(self) -> Dict:
        """Return the configured Q value.

        See `set_q_value()` for more details.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            dict: Dictionary with keys 'q_start', 'q_min' and 'q_max'.
        """
        response: List[str] = await self._send_command("AT+Q?")
        # +Q: 4,2,15
        try:
            setting: List[str] = response[0][4:].split(",")
            return {'q_start': int(setting[0]),
                    'q_min': int(setting[1]),
                    'q_max': int(setting[2])}
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+Q? - {response}") from exc

    async def get_tag_size_settings(self) -> Dict[str, Any]:
        """Returns the expected tag size settings.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with 'tag_size', 'min_tags' and 'max_tags' entries.
        """
        response: List[str] = await self._send_command("AT+Q?")
        # +Q: 4,2,15
        try:
            setting: List[str] = response[0][4:].split(",")
            return {'tag_size': pow(2, int(setting[0])),
                    'min_tags': pow(2, int(setting[1])),
                    'max_tags': pow(2, int(setting[2]))}
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+Q? - {response}") from exc

    async def set_mask(self, mask: str, start: int = 0, memory: str = "EPC", bit_length: int = 0) -> None:
        """Set a mask for all inventory operations.

        If this is enabled, inventories will filter transponders and
        only operate on tags whose data match the specified mask.

        Args:
            mask (str): The mask data (hex).

            start (int, optional): Start byte (or bit). Defaults to 0.

            memory (str, optional): The memory for the mask
                ['PC','EPC','USR','TID']. Defaults to 'EPC'.

            bit_length (int, optional): Bits from the mask to check.
                Defaults to 0, which will use the complete mask.
                If used, 'start' is interpreted in bits.

        Raises:
            RfidReaderException: If a reader error occurs.

        """
        if bit_length > 0:
            await self._send_command('AT+BMSK', memory, start, mask, bit_length)
        else:
            await self._send_command('AT+MSK', memory, start, mask)

    async def get_mask(self) -> Dict[str, Any]:
        """Get the current transponder mask for inventories.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Mask settings with keys 'memory', 'start',
            'mask' and 'bit_length'.
        """
        responses: List[str] = await self._send_command('AT+BMSK?')
        # +BMSK: EPC,0,0000
        # +BMSK: OFF
        data: List[str] = responses[0][7:].split(',')
        return_value: Dict[str, Any] = {'enabled': data[0] != "OFF"}
        if return_value['enabled']:
            return_value.update({'memory': data[0], 'start': int(data[1]), 'mask': data[2], 'bit_length': int(data[3])})
        return return_value

    async def reset_mask(self) -> None:
        """Reset and disable inventory mask.
        """
        await self._send_command('AT+MSK', "OFF")

    async def set_channel_mask(self, mask: str) -> None:
        """Define which RF channels of the current region are used.

        Channel 1 is en-/disabled by the LSB of the mask, so a value
        of "3" will enable channels 1 and 2.

        Args:
            mask (str): 64-bit hex string that encodes the channel mask.

        Raises:
            RfidReaderException: If a reader error occurs.

        """

        # TODO take list of channel numbers -> set bits in bit string?
        await self._send_command('AT+CMSK', mask)

    async def get_channel_mask(self) -> str:
        """Get the enabled RF channels of the current region.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            str: 64-bit hex string resembling the channel mask. The LSB
            represents channel 1.

        """

        response: List[str] = await self._send_command('AT+CMSK?')

        # +CMSK: 0000FFFFFFFFFFFF
        try:
            cmsk: str = response[0][7:]
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+CMSK? - {response}") from exc

        # TODO return list of enabled channels instead of hex value?
        return cmsk

    async def reset_channel_mask(self) -> None:
        """Reset the current channel mask to default.
        """
        await self._send_command('AT+CMSK', "0")

    async def send_select(self, mask: str, action: int, start: int = 0,
                          memory: str = "EPC", bit_length: int = 0,
                          target: str | int = "SL") -> None:
        """Modify a tags selected flag or inventoried state directly.

        Depending on the action parameter, the tags will modify their
        internal selected flag (SL=0/1) or inventoried state (INV=A/B) depending
        on whether its data matches the given mask or not.

        .. list-table:: Action Table
            :widths: 10 45 45
            :header-rows: 1

            * - action
              - TAG MATCHING
              - TAG NOT-MATCHING
            * - 0
              - SL = 1 or INV = A
              - SL = 0 or INV = B
            * - 1
              - SL = 1 or INV = A
              - do nothing
            * - 2
              - do nothing
              - SL = 0 or INV = B
            * - 3
              - negate SL or switch INV
              - do nothing
            * - 4
              - SL = 0 or INV = B
              - SL = 1 or INV = A
            * - 5
              - SL = 0 or INV = B
              - do nothing
            * - 6
              - do nothing
              - SL = 1 or INV = A
            * - 7
              - do nothing
              - negate SL or switch INV

        Args:
            mask (str): The mask data (hex).

            action (int): Index from the action table.

            start (int, optional): Start bit for matching. Defaults to 0.

            memory (str, optional): The memory for the mask
                ['PC','EPC','USR','TID']. Defaults to 'EPC'.

            bit_length (int, optional): Bits from the mask to check.
                Defaults to 0, which will use the complete mask.

            target (str|int, optional): The target for the select command.
                An integer [0,3] will modify the INV state in the matching session.
                By default "SL" is used to modify the tags Selected Flag.

        Raises:
            RfidReaderException: If a reader error occurs.

        """
        # disable 'Too many positional arguments' warning - pylint: disable=R0917
        # change session according to target
        session = "AUTO" if target == "SL" else target
        try:
            await self._send_command("AT+SES", session)
        except RfidReaderException as e:
            raise RfidReaderException("Switching target failed") from e

        # calculate mask length if not given
        if bit_length == 0:
            bit_length = len(mask) * 4

        # action index to binary string
        action_str = str(bin(action))[2:].zfill(3)

        # send command
        await self._send_command('AT+SEL', memory, start, mask, bit_length, action_str)

    async def set_power(self, power: int) -> None:
        """Set the antenna power of the reader for all antennas.

        Args:
            power (int): Power value in dBm.

        Raises:
            RfidReaderException: If a reader error occurs.

        """
        await self._send_command("AT+PWR", power)

    async def get_power(self) -> int:
        """Return the current power level.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            int: The current power level in dBm.
        """
        response: List[str] = await self._send_command("AT+PWR?")
        try:
            try:
                # assuming single value "+PWR: 20"
                return int(response[0][6:])
            except ValueError:
                # happens when response contains multiple antennas,
                # e.g. ["+PWR: 20,15,8,7"]
                # return power value of the current antenna
                ant: int = await self.get_antenna()
                data: List[str] = response[0][6:].split(",")
                return int(data[ant-1])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+PWR? - {response}") from exc

    async def get_inventory_settings(self) -> Dict[str, Any]:
        """Get the current reader inventory settings.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Inventory settings with keys 'only_new_tag', 'with_rssi',
            'with_tid', 'fast_start', 'phase', 'select' and 'target'.
        """
        responses: List[str] = await self._send_command("AT+INVS?")
        # AT+INVS=ONT, RSSI, TID, FastStart, PHASE
        # +INVS: 0,1,0
        data: List[str] = responses[0][7:].split(',')
        try:
            config: Dict[str, Any] = {'only_new_tag': data[0] == '1',
                                      'with_rssi': data[1] == '1',
                                      'with_tid': data[2] == '1'
                                      }
            if len(data) >= 4:
                config['fast_start'] = data[3] == '1'
            if len(data) >= 5:
                config['phase'] = data[4] == '1'
            if len(data) >= 6:
                config['select'] = data[5]
            if len(data) >= 7:
                config['target'] = data[6]
            return config
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+INVS? - {responses}") from exc

    async def set_inventory_settings(self, only_new_tag: Optional[bool] = None, with_rssi: Optional[bool] = None,
                                     with_tid: Optional[bool] = None, fast_start: Optional[bool] = None,
                                     phase: Optional[bool] = None, select: Optional[str] = None,
                                     target: Optional[str] = None) -> None:
        """Configure the inventory response.

        Args:
            only_new_tag (bool, optional): Only return new tags. Defaults to False.

            with_rssi (bool, optional): Append the RSSI value to the response. Defaults to True.

            with_tid (bool, optional): Append the TID to the response. Defaults to False.

            fast_start (bool, optional): Does an inventory without putting all tags into session
                state A at the start. This can speed up the start of the inventory, but it requires
                that all tags are in "reset state".

            phase (bool, optional): Append the phase information to the inventory.

            select (str, optional): Used to set which tags should respond. 'ALL'
                for all tags, 'SL' for tags with asserted selected flag or
                'NSL' for not-selected tags.

            target (str, optional): Used to set which tags should respond.
                Tags with inventoried state 'A' or 'B'.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        # disable 'Too many positional arguments' warning - pylint: disable=R0917
        def bti(value: bool):
            return '1' if value else '0'

        config: Dict[str, Any] = self._config['inventory']
        config_size = len(config)

        parameters: list[Any] = []
        parameters.append(bti(only_new_tag) if only_new_tag is not None else bti(config['only_new_tag']))
        parameters.append(bti(with_rssi) if with_rssi is not None else bti(config['with_rssi']))
        parameters.append(bti(with_tid) if with_tid is not None else bti(config['with_tid']))
        if config_size >= 4:
            parameters.append(bti(fast_start) if fast_start is not None else bti(config['fast_start']))
        if config_size >= 5:
            parameters.append(bti(phase) if phase is not None else bti(config['phase']))
        if config_size >= 6:
            parameters.append(select if select is not None else config['select'])
        if config_size >= 7:
            parameters.append(target if target is not None else config['target'])

        await self._send_command("AT+INVS", *parameters)

        # update configuration
        config['only_new_tag'] = only_new_tag
        config['with_rssi'] = with_rssi
        config['with_tid'] = with_tid
        if config_size >= 4:
            config['fast_start'] = fast_start
        if config_size >= 5:
            config['phase'] = phase
        if config_size >= 6:
            config['select'] = select
        if config_size >= 7:
            config['target'] = target

    # @override
    async def get_inventory(self) -> List[UhfTag]:
        responses: List[str] = await self._send_command("AT+INV")
        inventory: List[UhfTag] = self._parse_inventory(responses, time())
        current_antenna = self._config.get('antenna', 1)
        for tag in inventory:
            tag.set_antenna(current_antenna)
        self._fire_inventory_event(inventory, False)  # type: ignore
        return inventory

    async def get_inventory_report(self, duration: float = 0.0, ignore_error: bool = False) -> List[UhfTag]:
        """Get an inventory report from the current antenna.

        Args:
            duration (int, optional): Inventory report duration in seconds. Defaults to 0.1 seconds.
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: An array with the transponders found.
        """
        self._ignore_errors = ignore_error
        if duration == 0.0:
            responses: List[str] = await self._send_command('AT+INVR', timeout=2.0 + duration)
        else:
            responses = await self._send_command('AT+INVR', int(duration * 1000), timeout=2.0 + duration)
        timestamp: float = time()
        inventory: List[UhfTag] = self._parse_inventory(responses, timestamp, 7, True)
        self._fire_inventory_report_event(inventory, False)
        return inventory

    async def start_inventory_report(self, duration: float = 0.25, ignore_error: bool = False) -> None:
        """Start a continuous inventory report on multiple antennas.

        This will cause the reader to perform inventory reports continuously
        until the `stop_inventory_report()` function is called.
        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Args:
            duration (float, optional): Inventory report duration in seconds.
                Defaults to 0.25.
            ignore_error (bool, optional): Set to True to ignore antenna
                errors. Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        self._ignore_errors = ignore_error
        await self._send_command('AT+CINVR', int(duration * 1000), timeout=2.0 + duration)

    async def stop_inventory_report(self) -> None:
        """Stop the continuous inventory report.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        try:
            await self._send_command('AT+BINVR')
        except RfidReaderException as err:
            msg = str(err)
            if not msg or "is not running" in msg:
                return
            raise err

    async def read_tag_data(self, start: int = 0, length: int = 1, memory: str = 'USR',
                            epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Read data from all transponders found.

        Args:
            start (int, optional): Start byte. Defaults to 0.

            length (int, optional): Number of bytes to read. Defaults to 1.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

            memory (str, optional): Memory bank to read ["PC","EPC","USR","TID", "RES"].
                Defaults to "USR".

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]:  A list of transponders found.
        """
        responses: List[str] = await self._send_command("AT+READ", memory, start, length, epc_mask)
        timestamp: float = time()
        inventory: List[UhfTag] = []
        for response in responses:
            # +READ: 3034257BF468D480000003EE,OK,0000
            # +READ: <No tags found>
            if response[7] == '<':
                # inventory message, no tag
                # messages: Antenna Error / NO TAGS FOUND / ROUND FINISHED ANT=2
                if response[8] == 'N':  # NO TAGS FOUND
                    pass
                continue
            info: List[str] = response[7:].split(',')
            tag: UhfTag = UhfTag(info[0], timestamp)
            try:
                if info[1] == 'OK':
                    tag.set_value(memory.lower(), info[2])
                    tag.set_data(info[2])
                else:
                    tag.set_error_message(info[1])
            except IndexError:
                # ignore index errors ... response not valid (+READ: <No tags found during inventory>)
                pass
            inventory.append(tag)
        return inventory

    async def read_tag_usr(self, start: int = 0, length: int = 1, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Read the user memory (USR) of all transponders found.

        Args:
            start (int, optional): Start byte. Defaults to 0.

            length (int, optional): Number of bytes to read. Defaults to 1.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: A list with the transponders found.
        """
        return await self.read_tag_data(start, length, 'USR', epc_mask)

    async def read_tag_tid(self, start: int = 0, length: int = 4, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Read the tag ID (TID) of all transponders found.

        Args:
            start (int, optional): Start byte. Defaults to 0.

            length (int, optional): Number of bytes to read. Defaults to 1.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: A list with the transponders found.
        """
        return await self.read_tag_data(start, length, 'TID', epc_mask)

    async def write_tag_data(self, data: str, start: int = 0,  memory: str = 'USR',
                             epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Write data to all transponders found.

        Args:
            data (str): Data to write (hex).

            start (int, optional): Start byte. Defaults to 0.

            memory (str, optional): Memory bank to write ["PC","EPC","USR", "RES"].
                Defaults to "USR".

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: List with handled tags. If a tag was not written
            successfully, the `has_error()` function of the tag will return True.

        Example:
            Assuming the EPC of a tag starts with "ABCD", the following
            command will change it to "AB01".

            >>> write_tag_data("01", start=1, memory="EPC")
        """

        # disable 'Too many arguments' warning - pylint: disable=R0913

        responses = await self._send_command("AT+WRT", memory, start, data, epc_mask, timeout=5.0)
        return self._parse_tag_responses(responses, 6)

    async def write_tag_usr(self, data: str, start: int = 0, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """write data into the user memory (USR) of all transponders found.

        Args:
            data (str): Date to write (hex).

            start (int, optional): Start byte. Defaults to 0.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: List with handled tags. If a tag was not written
            successfully, the `has_error()` function of the tag will return True.
        """
        if not data:
            raise RfidReaderException("Data argument must be set")
        return await self.write_tag_data(data, start, 'USR', epc_mask)

    async def write_tag_epc(self, tid: str, new_epc: str, start: int = 0) -> List[UhfTag]:
        """Write data into the EPC memory of a specific transponder.

        Change the Electronic Product Code (EPC) of a specific tag, identified
        by its unique tag ID (TID).

        Args:
            tid (str): The tag ID of the transponder.

            new_epc: The new EPC data to write (hex).

            start (int, optional): Start byte. Defaults to 0.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: List with handled tags. If a tag was not written
            successfully, the `has_error()` function of the tag will return True.
        """

        # check EPC input length
        if len(new_epc) % 4:
            raise RfidReaderException("The new EPC length must be a multiple of 4")

        # store current mask setting and set new mask to TID argument
        mask_settings: dict = {}
        if tid:
            mask_settings = await self.get_mask()
            await self.set_mask(tid, memory="TID")

        # run write operation
        tag_list = []
        write_error = None
        try:
            tag_list = await self._write_tag_epc(new_epc, start)
        except RfidReaderException as e:
            write_error = e

        # reset previous mask
        if tid:
            try:
                if mask_settings['enabled']:
                    # reset to the last mask setting
                    await self.set_mask(mask_settings['memory'], mask_settings['start'], mask_settings['mask'])
                else:
                    await self.reset_mask()
            except RfidReaderException as e:
                self.get_logger().warning("Mask reset failed: %s", e)

        # re-raise write error after mask cleanup
        if write_error:
            raise write_error

        # return results
        return tag_list

    async def _write_tag_epc(self, new_epc: str, start: int) -> List[UhfTag]:
        # disable 'Too many branches' warning - pylint: disable=R0912
        tags: dict[str, UhfTag] = {}

        epc_words: int = int(len(new_epc) / 4)
        epc_length_byte = int(epc_words / 2) << 12
        if 1 == epc_words % 2:
            epc_length_byte |= 0x0800

        inventory_pc: list[UhfTag] = await self.read_tag_data(0, 2, 'PC')
        if not inventory_pc:
            # no tags found
            return inventory_pc
        pc_byte = 0
        for tag in inventory_pc:
            data = int(str(tag.get_data()), 16) & 0x07FF
            if not pc_byte:
                pc_byte = data
            elif data != pc_byte:
                raise RfidReaderException("Different tags are in the field, which would result in"
                                          " data loss when writing. Please edit individually.")
        # write epc
        inventory_epc: list[UhfTag] = await self.write_tag_data(new_epc, start, 'EPC')
        for tag in inventory_epc:
            tags[tag.get_id()] = tag
            if not tag.has_error():
                old_epc: str = tag.get_id()
                tag.set_epc(new_epc)
                tag.set_value("old_epc", old_epc)
        # write length
        pc_byte |= epc_length_byte
        inventory_pc = await self.write_tag_data(f"{pc_byte:04X}", 0, 'PC')
        for tag_pc in inventory_pc:
            tag_epc = tags.get(tag_pc.get_id())
            if tag_epc:
                if tag_pc.has_error():
                    if not tag_epc.has_error():
                        # write new epc length not ok
                        tag_epc.set_error_message(f"EPC written, EPC length not updated: {tag_pc.get_error_message()}")
                    else:
                        # both not successful:
                        tag_epc.set_error_message(f"EPC not written: {tag_epc.get_error_message()}")
            elif not tag_pc.has_error():
                # tag epc length was updated but tag not found in write EPC
                tag_pc.set_error_message("EPC length updated, but EPC not written")
                tags[tag_pc.get_id()] = tag_pc
            # else: both epc write and epc length was not successful...ignore tag
        return list(tags.values())

    async def kill_tag(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permanently disable a transponder.

        Args:
            password (str): The kill password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        responses: List[str] = await self._send_command("AT+KILL", password, epc_mask)
        # AT+KILL: 1234ABCD<CR><LF>
        # +KILL: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def lock_tag(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Lock a memory bank of a transponder.

        Args:
            membank (str): The memory to lock ['EPC', 'USR', 'LCK', 'KILL', 'RES'].

            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: List[str] = await self._send_command("AT+LCK", membank, password, epc_mask)
        # AT+ULCK: USR,1234ABCD<CR>
        # <LF>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    async def lock_user_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Lock the USER memory bank of a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.lock_tag("USR", password, epc_mask)

    async def lock_epc_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Lock the EPC memory bank of a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.lock_tag("EPC", password, epc_mask)

    async def unlock_tag(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlock a memory bank of a transponder.

        Args:
            membank (str): The memory to unlock ['EPC', 'USR', 'LCK', 'KILL', 'RES'].

            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: List[str] = await self._send_command("AT+ULCK", membank, password, epc_mask)
        # AT+LCK: USR,1234ABCD<CR>
        # <LF>
        # +ULCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def unlock_user_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlock the USER memory bank a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.unlock_tag("USR", password, epc_mask)

    async def unlock_epc_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlock the EPC memory bank of a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.unlock_tag("EPC", password, epc_mask)

    async def lock_tag_permament(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permamently lock a memory bank of a transponder.

        Args:
            membank (str): The memory to lock ['EPC', 'USR', 'LCK', 'KILL', 'RES'].

            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        # membank: KILL,LCK,EPC,TID,USR,RES
        responses: List[str] = await self._send_command("AT+PLCK", membank, password, epc_mask)
        # AT+PLCK: USR,1234ABCD<CR>
        # <LF>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def lock_user_memory_permament(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permanently lock the USER memory bank a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.lock_tag_permament("USR", password, epc_mask)

    async def lock_epc_memory_permament(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permanently lock the EPC memory bank a transponder.

        Args:
            password (str): The access password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        return await self.lock_tag_permament("EPC", password, epc_mask)

    async def set_lock_password(self, password: str, new_password, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Change the lock/access password of a tag.

        This will automatically read- and write-lock the memory bank.

        Args:
            password (str): The current access password (32 bit, 8 hex digits)
                or an empty string (`""`) if memory is unlocked.

            new_password (_type_): The new password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        responses: List[str] = await self._send_command("AT+PWD", "LCK", password, new_password, epc_mask, timeout=5.0)
        # AT+PWD: LCK,1234ABCD,1234ABCD<CR><LF>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    async def set_kill_password(self, password: str, new_password, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Change the kill password of a tag.

        This will automatically read- and write-lock the memory bank.

        Args:
            password (str): The access password (32 bit, 8 hex digits)
                or an empty string (`""`) if memory is unlocked.

            new_password (_type_): The kill password (32 bit, 8 hex digits).

            epc_mask (str, optional): EPC mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tags. If a tag `has_error()`,
            the command was not successful.
        """
        responses: List[str] = await self._send_command("AT+PWD", "KILL", password, new_password, epc_mask, timeout=5.0)
        # AT+PWD: LCK,1234ABCD,1234ABCD<CR><LF>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    # @override
    async def disconnect(self) -> None:
        # stop the continuous report
        if self.get_status()['status'] >= 1:
            try:
                await self.stop_inventory_report()
            except RfidReaderException:
                # ignore reader exceptions
                pass
        return await super().disconnect()

    # @override
    async def fetch_inventory(self, wait_for_tags: bool = True) -> List[UhfTag]:  # type: ignore
        """
        Can be called when an inventory has been started. Waits until at least one tag is found
        and returns all currently scanned transponders from a continuous scan.

        Args:
            wait_for_tags (bool): Set to true, to wait until transponders are available.

        Returns:
            List[UhfTag]: A list with the transponders found.
        """
        return await super().fetch_inventory(wait_for_tags)  # type: ignore

    async def call_impinj_authentication_service(self) -> List[Dict[str, Any]]:
        """Run the Impinj Authentication Service.

        This command talks to an Impinj M775 tag using the proprietary
        authentication command. It sends a random challenge to the
        transponder and gets the authentication payload in return. You
        can use this to check the authenticity of the transponder with
        Impinj Authentication Service. For further details, please
        contact Impinj directly.

        Raises:
            RfidReaderException: If an error occurs.

        Returns:
            List[Dict[str, Any]]: A list with the transponders. The
            transponders dictionaries contain the keys 'epc',
            'has_error', 'short_tid', 'response' and 'challenge'.

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
        """Returns the currently selected session.

        See set_selected_session() for more details.

        Returns:
            str: The currently selected session.

        """
        responses: List[str] = await self._send_command("AT+SES?")
        # +SES: AUTO
        return responses[0][6:]

    async def set_selected_session(self, session: str = "AUTO"):
        """Set the EPC Gen2 session to perform inventories in.

        Manually select the session according to the EPC Gen 2 Protocol
        to use during inventory scan. Default value is `AUTO` and in
        most cases it should stay this way. Only change this if you
        absolutely know what you are doing and if you can control the
        types of tags you scan. Otherwise, unexpected results during
        inventory scans with "Only New Tags" active might happen.

        Args:
            session (str, optional): Session to set
                ["0", "1", "2", "3", "AUTO"]. Defaults to "AUTO".

        """
        await self._send_command("AT+SES", session)

    async def get_custom_impinj_settings(self) -> Dict[str, Any]:
        """Returns the custom Impinj settings.

        See `set_custom_settings()` for more details.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, bool]: Settings 'fast_id' and 'tag_focus'.

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
        """De-/activate proprietary Impinj features.

        The RFID tag IC manufacturer Impinj has added two custom features
        to its tag ICs that are not compatible with tag ICs from other
        manufacturers. Activate these features with this command - but
        make sure that you only use tags with Impinj ICs like Monza6 or
        M7xx or M8xx series. Tags from other manufacturers will most
        likely not answer at all when those options are active!

        Args:
            fast_id (bool, optional): True, to allow reading the TagID
                together with the EPC which can speed up getting TID
                data. Defaults to False.

            tag_focus (bool, optional): True, to use a proprietory tag
                feature where each tag only answers once until it is
                repowered. This allows to scan a high number of tags
                because each tag only answers once and makes
                anti-collision easier for the following tags.

        Raises:
            RfidReaderException: If an reader error occurs.

        """
        await self._send_command("AT+ICS", 1 if fast_id else 0, 1 if tag_focus else 0)

    async def get_rf_mode(self) -> int:
        """Return the currently selected RF mode.

        See reader description for more detail.

        Returns:
            int: The currently set RF mode value.

        """
        responses: List[str] = await self._send_command("AT+RFM?")
        # +RFM: 223
        return int(responses[0][6:])

    async def set_rf_mode(self, mode_id: int) -> None:
        """Set RF mode value for inventories.

        Configure the internal RF communication settings between tag and
        reader. Each mode ID corresponds to a set of RF parameters that
        fit together. Not all devices support all modes and not all
        modes can be accessed in all regions.
        See reader description for more detail.

        Args:
            mode_id (int): The RF mode ID to set.

        """
        await self._send_command("AT+RFM", mode_id)

    async def activate_protected_mode(self, password: str) -> List[UhfTag]:
        """Activate a tags protected mode.

        Activate a tags protected mode which will make the tag untraceable
        and hide it from inventories. It requires a single tag to
        respond to inventory and the tag must have a non-zero lock password.

        Args:
            password (str): The access password (32 bit / 8 hex digits)

        Returns:
            List[UhfTag]: List with handled tag. If the tag has an
            error, the action was not successful.
        """
        responses = await self._send_command("AT+PMACT", password, 1)
        return self._parse_tag_responses(responses, 8)

    async def deactivate_protected_mode(self, password: str) -> List[UhfTag]:
        """Deactivate a tags protected mode.

        Args:
            password (str): The access password (32 bit / 8 hex digits)

        Returns:
            List[UhfTag]: List with handled tag. If the tag has an
            error, the action was not successful.
        """
        responses = await self._send_command("AT+PMACT", password, 0)
        return self._parse_tag_responses(responses, 8)

    async def activate_short_range_mode(self, password: str) -> List[UhfTag]:
        """Activate a tags short range mode.

        Activate a tags short range mode which will drastically reduce
        the range at which the tag will respond. It requires a single
        tag to respond to inventory and the tag must have a non-zero
        lock password.

        Args:
            password (str): The access password (32 bit / 8 hex digits)

        Returns:
            List[UhfTag]: List with handled tag. If the tag has an
            error, the action was not successful.
        """
        responses = await self._send_command("AT+SRACT", password, 1)
        return self._parse_tag_responses(responses, 8)

    async def deactivate_short_range_mode(self, password: str) -> List[UhfTag]:
        """Deactivate a tags short range mode.

        Args:
            password (str): The access password (32 bit / 8 hex digits)

        Returns:
            List[UhfTag]: List with handled tag. If the tag has an
            error, the action was not successful.
        """
        responses = await self._send_command("AT+SRACT", password, 0)
        return self._parse_tag_responses(responses, 8)

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    # @override
    async def _prepare_reader_communication(self) -> None:
        await super()._prepare_reader_communication()
        await self.stop_inventory_report()

    # @override
    async def _config_reader(self) -> None:
        self._config['inventory'] = await self.get_inventory_settings()
        await super()._config_reader()

    # @override
    def _handle_inventory_events(self, msg: str, timestamp: float):
        # continuous inventory event
        try:
            if msg[2] == 'M':  # +CMINV:
                # '+CMINV: '
                self._fire_inventory_event(self._parse_inventory(
                    msg.split("\r"), timestamp, 8))  # type: ignore
            elif msg[5] == 'R':
                # '+CINVR: '
                self._fire_inventory_report_event(self._parse_inventory(
                    msg.split("\r"), timestamp, 8, True))  # '+CINVR: '
            else:
                # '+CINV: '
                self._fire_inventory_event(self._parse_inventory(
                    msg.split("\r"), timestamp, 7))  # type: ignore
        except RfidReaderException as err:
            if self._status['status'] == RfidReader.WARNING and "antenna error" in self.get_status()['message'].lower():
                # error is already set
                return
            self._update_status(RfidReader.WARNING, str(err))

    def _parse_inventory(
            self, responses: List[str],
            timestamp: float, split_index: int = 6, is_report: bool = False) -> List[UhfTag]:
        # +CINV: 3034257BF468D480000003EC,E200600311753E33,1755 +CINV=<ROUND FINISHED, ANT=2>
        # +INV: 0209202015604090990000145549021C,E200600311753F23,1807
        # disable 'Too many branches' warning - pylint: disable=R0912
        # disable 'Too many local variables' warning - pylint: disable=R0914

        inventory: List[UhfTag] = []
        with_tid: bool = self._config['inventory']['with_tid']
        with_rssi: bool = self._config['inventory']['with_rssi']
        with_phase: bool = self._config['inventory'].get('phase', False)
        antenna: Optional[int] = None
        error: Optional[str] = None
        for response in responses:
            if response[0] != '+':
                continue
            if response[split_index] == '<':
                # inventory message, no tag
                # messages: <Antenna Error> / <NO TAGS FOUND> / <ROUND FINISHED ANT=2>
                if response[split_index+1] == 'N':  # NO TAGS FOUND
                    pass
                elif response[split_index+1] == 'R':
                    if len(response) > split_index + 16:
                        # ROUND FINISHED ANT2
                        try:
                            antenna = int(response[-2:-1])
                        except (IndexError, ValueError) as err:
                            self.get_logger().debug("Error parsing inventory response - %s", err)
                elif self._ignore_errors:
                    pass
                else:
                    print(f"error: {response[split_index+1:-1]} - {self._ignore_errors}")
                    error = response[split_index+1:-1]
                continue
            info: List[str] = response[split_index:].split(',')
            try:
                new_tag = UhfTag(info[0], timestamp, tid=info[1] if with_tid else None,
                                 rssi=int(info[2]) if with_rssi and with_tid else int(info[1]) if with_rssi else None,
                                 seen_count=int(info[-1]) if is_report else 1)
                if with_phase:
                    new_tag['phase'] = [info[-2], info[-1]]
                inventory.append(new_tag)
            except IndexError as err:
                self.get_logger().debug("Error parsing inventory transponder -%s", err)
        if error:
            error_detail = self._config.get('error', {})
            self._config.setdefault('error', error_detail)
            if antenna:
                error_detail[f"Antenna {antenna}"] = error
            else:
                error_detail['message'] = error
            raise RfidReaderException(f"{error}{f' - Antenna {antenna} ' if antenna else ''}")
        if antenna:
            for tag in inventory:
                tag.set_antenna(antenna)
        return inventory

    def _fire_inventory_report_event(self, inventory: List[UhfTag], continuous: bool = True) -> None:
        """ Checks the inventory and calls the inventory callback """
        if not self._cb_inventory_report:
            if continuous:
                self._update_inventory(inventory)  # type: ignore
            return
        if not self._fire_empty_reports and not inventory:
            return
        self._cb_inventory_report(inventory)

    def _parse_tag_responses(self, responses: list, prefix_length: int) -> List[UhfTag]:
        """Parsing the transponder responses. Used when the response list contains only the epc and the response code

        Args:
            responses (list): response list

            prefix_length (int): response command prefix length - len("+PREFIX: ")

            timestamp (float, optional): response timestamp.

        Returns:
            List[UhfTag]: list with handled tags
        """
        # +COMMAND: ABCD01237654321001234567,ACCESS ERROR<CR>
        # prefix_length = len("+COMMAND: ")
        timestamp: float = time()
        tags: List[UhfTag] = []
        for response in responses:
            if response[prefix_length] == '<':
                # inventory message, no tag
                # messages: Antenna Error / NO TAGS FOUND / ROUND FINISHED ANT=2
                if response[prefix_length+1] == 'N':  # NO TAGS FOUND
                    pass
                continue
            info: List[str] = response[prefix_length:].split(',')
            tag: UhfTag = UhfTag(info[0], timestamp)
            if info[1] != 'OK':
                tag.set_error_message(info[1])
            tags.append(tag)
        return tags


class UhfReaderATMulti(UhfReaderAT):
    """Base class for readers with antenna switching and multiplexing features

    For devices that have more than one integrated antenna or I/Os
    for external multiplexing.

    """

    # def __init__(self, instance: str, connection: Connection) -> None:
    #    super().__init__(instance, connection)

    async def set_antenna_multiplex(self, antennas: Union[int, List[int]]) -> None:
        """Configure automatic muxing of antennas during inventory.

        If this is set to higher values than 1, certain inventory
        operations will automatically multiplex antennas from 1-x by
        switching antennas during execution and performing an inventory
        with all of them. This affects:

        - get_inventory_multi()
        - start_inventory_multi()
        - get_inventory_report()
        - start_inventory_report()

        Instead of a single value, which will mux from 1-x, a list can
        be given to dictate a specific multiplexing sequence.

        Args:
            antennas (int or List): Number of antennas to be multiplexed
                or the antenna sequence list.

        Raises:
            RfidReaderException: If an reader error occurs.

        Example:
            This will use antennas 1,2,3,4

            >>> set_antenna_multiplex(4)

            and this will use antennas 3,2,4

            >>> set_antenna_multiplex([3, 2, 4])

        """
        if isinstance(antennas, int):
            await self._send_command("AT+MUX", antennas)
        elif isinstance(antennas, List):
            await self._send_command("AT+MUX", *antennas)

    async def get_antenna_multiplex(self) -> List[int]:
        """Get the current antenna multiplex sequence.

        Raises:
            RfidReaderException: If an error occurs.

        Returns:
            List[int]: The antenna port sequence.

        """
        responses: List[str] = await self._send_command("AT+MUX?")
        # +MUX: 1,2,3,....
        data: List[str] = responses[0][6:].split(',')
        if len(data) == 1:
            return [int(i) for i in data]
        return list(map(int, data))

    async def set_antenna_powers(self, antenna_powers: List[int]) -> None:
        """Set the RF power of all antennas.

        Index 0 in the list represents antenna port 1, and so on.

        Args:
            antenna_powers (List[int]): List of power values in dBm
                for each antenna.

        """
        await self._send_command("AT+PWR", *antenna_powers)

    async def get_antenna_powers(self) -> List[int]:
        """Return a list of current power values for each antenna.

        Index 0 in the list represents antenna port 1, and so on.

        Returns:
            List[int]: List with power values in dBm.

        """
        responses: List[str] = await self._send_command("AT+PWR?")
        # +PWR: 12,12,12,12
        data: List[str] = responses[0][6:].split(',')
        # return [int(i) for i in data]
        return list(map(int, data))

    async def get_antenna_power(self, antenna: int) -> int:
        """Return the current antenna power of the given port.

        Args:
            antenna (int): Antenna port index.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            int: The current antenna power in dBm.

        """
        powers = await self.get_antenna_powers()
        try:
            return powers[antenna - 1]
        except IndexError as exc:
            raise RfidReaderException(f"Antenna {antenna} not available") from exc

    async def set_antenna_power(self, antenna: int, power: int) -> None:
        """Set the RF power of a single antenna.

        Args:
            antenna (int): Antenna port index.
            power (int): Antenna power in dBm [0,30].

        Raises:
            RfidReaderException: If a reader error occurs.

        """
        if antenna <= 0:
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers = await self.get_antenna_powers()
        if antenna > len(powers):
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers[antenna - 1] = power
        await self.set_antenna_powers(powers)

    async def get_inventory_multi(self, ignore_error: bool = False) -> List[UhfTag]:
        """Get an inventory from multiple antennas.

        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[UhfTag]: An array with the transponders found.
        """

        self._ignore_errors = ignore_error
        responses: List[str] = await self._send_command("AT+MINV")
        # parse multiple inventory
        # +MINV: <Antenna Error><CR>
        # +MINV: <ROUND FINISHED, ANT=1><CR>
        # +MINV: 3034257BF468D480000003EB<CR>
        # +MINV: <ROUND FINISHED, ANT=2><CR>
        # +MINV: <Operation Error (6AC0B)><CR>
        # +MINV: <ROUND FINISHED, ANT=3><CR>
        # +MINV: <NO TAGS FOUND><CR>
        # +MINV: <ROUND FINISHED, ANT=4><CR>

        # split answers in antenna sections
        inventory: List[UhfTag] = []
        last_index: int = 0
        for index, item in enumerate(responses):
            if item.startswith("+MINV: <R"):
                index += 1
                inventory.extend(self._parse_inventory(
                    responses[last_index:index], time(), 7))
                last_index = index
        self._fire_inventory_event(inventory, False)  # type: ignore
        return inventory

    async def start_inventory_multi(self, ignore_error: bool = False) -> None:
        """Start a continuous inventory on multiple antennas.

        This will cause the reader to perform inventories continuously
        until the `stop_inventory_multi()` function is called.
        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        self._ignore_errors = ignore_error
        await self._send_command('AT+CMINV')

    async def stop_inventory_multi(self) -> None:
        """Stop the continuous multi inventory.

        Raises:
            RfidReaderException: If a reader error occurs.
        """

        await self.stop_inventory()
