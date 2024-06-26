"""
metratec uhf reader gen2
"""

from time import time
from typing import Callable, Optional, Any, Dict, List

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
        """
        Set the callback for a new inventory. The callback has the following arguments:
        * tags (List[UhfTag]) - the tags

        Returns:
            Optional[Callable]: the old callback
        """
        return super().set_cb_inventory(callback)

    def set_cb_inventory_report(self, callback: Optional[Callable[[List[UhfTag]], None]]
                                ) -> Optional[Callable[[List[UhfTag]], None]]:
        """
        Set the callback for a new inventory report. The callback has the following arguments:
        * tags (List[Tag]) - the tags

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_inventory_report
        self._cb_inventory_report = callback
        return old

    def enable_fire_empty_reports(self, enable: bool):
        """If the event handler for new inventory report is set and this value is true,
        an empty report also triggers the event handler

        Args:
            enable (bool): Set to true, to trigger empty reports events as well. Defaults to false
        """
        self._fire_empty_reports = enable

    async def set_region(self, region: str) -> None:
        """Sets the used uhf region

        Args:
            region (Region): the uhf region

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await self._send_command("AT+REG", region)

    async def get_region(self) -> str:
        """Return the configured uhf region

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Region: the used uhf region
        """
        response: List[str] = await self._send_command("AT+REG?")
        # +REG: ETSI_LOWER
        try:
            return response[0][6:]
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+REG? - {response}") from exc

    async def set_tag_size(self, tags_size: int, min_tags: int = -1, max_tags: int = -1) -> None:
        """Configure the expected numbers of transponders in the field.
        Alternatively, the set_q_value method can be used.

        Args:
            tags_size (int): expected numbers of transponders

            min_tags (int, optional): minimum numbers of transponders.

            max_tags (int, optional): maximum numbers of transponders.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if not (min_tags >= 0 and max_tags >= 0 or min_tags < 0 and max_tags < 0):
            raise RfidReaderException("min_tags and max_tags must be set, or none of the these")
        q_start: int = 0
        q_min: Optional[int] = None
        q_max: Optional[int] = None
        while tags_size > pow(2, q_start):
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
        """Returns the configured tag size

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the configured tag size
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
        """Configure the expected numbers of transponders in the field as q value. Alternatively, the set_tag_size
        method can be used.
        The Q value is the exponent of 2 and should be around or above the expected number of tags.
        Setting this value too low will result in tags being missed. Setting the value too high will lead to
        unnecessary slow inventories.

        Args:
            q_start (int): start q value

            q_min (int, optional): minimum q value

            q_max (int, optional): maximum q value

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if not (q_min >= 0 and q_max >= 0 or q_max < 0 and q_min < 0):
            raise RfidReaderException("q_min and q_max must be set, or none of the these")
        await self._send_command("AT+Q", q_start, q_min if q_min >= 0 else None, q_max if q_max >= 0 else None,)

    async def get_q_value(self) -> Dict:
        """Returns the configured q value. See set_q_value for more details.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'q_start', 'q_min' and 'q_max' entries
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
        """Returns the configured tag size

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'tag_size', 'min_tags' and 'max_tags' entries
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
        """Set a mask

        Args:
            mask (str): the mask (hex)

            start (int, optional): start byte. Defaults to 0.

            memory (str, optional): the memory for the mask. ['PC','EPC','USR','TID'] Defaults to "EPC".

            bit_length (int, optional): Bits from the mask to check. Defaults to 0, means use the complete mask

        Raises:
            RfidReaderException: if an reader error occurs

        """
        if bit_length > 0:
            await self._send_command('AT+BMSK', memory, start, mask, bit_length)
        else:
            await self._send_command('AT+MSK', memory, start, mask)

    async def get_mask(self) -> Dict[str, Any]:
        """Gets current reader mask.


        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: dictionary with the mask settings
                  available entries: memory (str), start (int), mask (str)
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
        """Remove the mask
        """
        await self._send_command('AT+MSK', "OFF")

    async def set_power(self, power: int) -> None:
        """Sets the antenna power of the reader for all antennas

        Args:
            power (int): antenna power in dbm

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
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+PWR? - {response}") from exc

    async def get_inventory_settings(self) -> Dict[str, Any]:
        """Gets the current reader inventory settings

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'only_new_tag', 'with_rssi' and 'with_tid' entries
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
        """Configure the inventory response

        Args:
            only_new_tag (bool, optional): Only return new tags. Defaults to False.

            with_rssi (bool, optional): Append the rssi value to the response. Defaults to True.

            with_tid (bool, optional): Append the tid to the response. Defaults to False.

            fast_start (bool, optional): Does an inventory without putting all tags into session
            state A at the start. This can speed up the start of the inventory, but it requires
            that all tags are in "reset state".

            phase (bool, optional): Append the the phase information to the inventory

            select (str, optional): Use to set witch tag should respond. 'ALL' for all, 'SL' for select asserted,
            'NSL' for select not asserted

            target (str, optional): Use to set witch tag should respond. Can be 'A' or 'B'

        Raises:
            RfidReaderException: if an reader error occurs
        """
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

    # @override
    async def get_inventory_multi(self, ignore_error: bool = False) -> List[UhfTag]:
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

    async def get_inventory_report(self, duration: float = 0.0, ignore_error: bool = False) -> List[UhfTag]:
        """gets an inventory report from the current antenna (see set_antenna)

        Args:
            duration (int, optional): inventory report duration in seconds. Defaults to 0.1 seconds.
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.


        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[Tag]: An array with the transponder found
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
        """Start the inventory report. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            duration (float, optional): inventory report duration in seconds. Defaults to 0.25
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.


        Raises:
            RfidReaderException: if an reader error occurs
        """
        self._ignore_errors = ignore_error
        await self._send_command('AT+CINVR', int(duration * 1000), timeout=2.0 + duration)

    async def stop_inventory_report(self) -> None:
        """stop the inventory report

        Raises:
            RfidReaderException: if an reader error occurs
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
        """read the memory of the transponder found

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

            memory (str, optional): Memory bank to read ["PC","EPC","USR","TID"]. Defaults to "USR".

        Raises:
            RfidReaderException: if an reader error occurs

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
        """read the usr memory of the transponder found

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[UhfTag]: A list with the transponder found.
        """
        return await self.read_tag_data(start, length, 'USR', epc_mask)

    async def read_tag_tid(self, start: int = 0, length: int = 4, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """read the tid of the transponder found

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[UhfTag]: A list with the transponder found.
        """
        return await self.read_tag_data(start, length, 'TID', epc_mask)

    async def write_tag_data(self, data: str, start: int = 0,  memory: str = 'USR',
                             epc_mask: Optional[str] = None) -> List[UhfTag]:
        """write the data to the transponder found

        Args:
            data (str): data to write

            start (int, optional): Start address. Defaults to 0.

            memory (str, optional): Memory bank to read ["PC","EPC","USR"]. Defaults to "USR".

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """

        # disable 'Too many arguments' warning - pylint: disable=R0913

        responses = await self._send_command("AT+WRT", memory, start, data, epc_mask)
        return self._parse_tag_responses(responses, 6)

    async def write_tag_usr(self, data: str, start: int = 0, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """write the data to the transponder found

        Args:
            data (str): _description_

            start (int, optional): Start address. Defaults to 0.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """
        if not data:
            raise RfidReaderException("Data must be set")
        return await self.write_tag_data(data, start, 'USR', epc_mask)

    async def write_tag_epc(self, tid: str, new_epc: str, start: int = 0) -> List[UhfTag]:
        """write the tag epc

        Args:
            tid (str): the tag id

            new_epc: the new epc

            start (int, optional): Start address. Defaults to 0.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """

        # disable 'Too many branches' warning - pylint: disable=R0912
        # disable 'Too many arguments' warning - pylint: disable=R0913
        # disable 'Too many local variables' warning - pylint: disable=R0914
        if len(new_epc) % 4:
            raise RfidReaderException(" The new epc length must be a multiple of 4")
        tags: dict[str, UhfTag] = {}
        epc_words: int = int(len(new_epc) / 4)
        epc_length_byte = int(epc_words / 2) << 12
        if 1 == epc_words % 2:
            epc_length_byte |= 0x0800

        mask_settings: dict = {}
        if tid:
            mask_settings = await self.get_mask()  # get current mask
            await self.set_mask(tid, memory="TID")
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
                        tag_epc.set_error_message("epc written, epc length not updated!")
                    else:
                        # both not successful:
                        tag_epc.set_error_message(f"epc not written - {tag_epc.get_error_message()}")
            elif not tag_pc.has_error():
                # tag epc length was updated
                tag_pc.set_error_message("epc not written, but epc length updated!")
                tags[tag_pc.get_id()] = tag_pc
            # else: both epc write and epc length was not successful...ignore tag
        # Note: The field is active during these two write commands
        #       ...so both commands return the old epc and can be compared
        if tid:
            if mask_settings['enabled']:
                # reset to the last mask setting
                await self.set_mask(mask_settings['memory'], mask_settings['start'], mask_settings['mask'])
            else:
                await self.reset_mask()
        return list(tags.values())

    async def kill_tag(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Kill a transponder

        Args:
            password (str): the kill password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the kill was not successful
        """
        responses: List[str] = await self._send_command("AT+KILL", password, epc_mask)
        # AT+KILL: 1234ABCD<CR><LF>
        # +KILL: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def lock_tag(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Locking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
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
        """Locking of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return await self.lock_tag("USR", password, epc_mask)

    async def lock_epc_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Locking of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return await self.lock_tag("EPC", password, epc_mask)

    async def unlock_tag(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlocking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: List[str] = await self._send_command("AT+ULCK", membank, password, epc_mask)
        # AT+LCK: USR,1234ABCD<CR>
        # <LF>
        # +ULCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def unlock_user_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlocking of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        return await self.unlock_tag("USR", password, epc_mask)

    async def unlock_epc_memory(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Unlocking of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        return await self.unlock_tag("EPC", password, epc_mask)

    async def lock_tag_permament(self, membank: str, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permament locking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: List[str] = await self._send_command("AT+PLCK", membank, password, epc_mask)
        # AT+PLCK: USR,1234ABCD<CR>
        # <LF>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    async def lock_user_memory_permament(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permament l of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return await self.lock_tag_permament("USR", password, epc_mask)

    async def lock_epc_memory_permament(self, password: str, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """Permament l of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return await self.lock_tag_permament("EPC", password, epc_mask)

    async def set_lock_password(self, password: str, new_password, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """sets the lock password

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            new_password (_type_): the new access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the password change was not successful
        """
        responses: List[str] = await self._send_command("AT+PWD", "LCK", password, new_password, epc_mask)
        # AT+PWD: LCK,1234ABCD,1234ABCD<CR><LF>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    async def set_kill_password(self, password: str, new_password, epc_mask: Optional[str] = None) -> List[UhfTag]:
        """sets the kill password

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            new_password (_type_): the new access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            List[UhfTag]: List with handled tag. If the tag has error, the password change was not successful
        """
        responses: List[str] = await self._send_command("AT+PWD", "KILL", password, new_password, epc_mask)
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
        and returns all currently scanned transponders from a continuous scan

        Args:
            wait_for_tags (bool): Set to true, to wait until transponders are available

        Returns:
            List[UhfTag]: a list with the transponder found
        """
        return await super().fetch_inventory(wait_for_tags)  # type: ignore

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

    def _parse_error_response(self, response: str) -> RfidReaderException:
        """analyse the reader error and return the resulting exception

        Args:
            response (str): error response

        Returns:
            RfidReaderException: resulting exception
        """
        return RfidReaderException(response)
