""" metraTec HF Reader Gen1"""
import asyncio
from time import time
from typing import Any, Callable, Dict, List, Optional

from .reader_exception import RfidReaderException
from .connection import Connection
from .uhf_tag import UhfTag
from .reader_ascii import ReaderAscii


class UhfReaderAscii(ReaderAscii):
    """The implementation of the uhf gen1 reader with the **ASCII-protocol.**
    """
    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes' warning - pylint: disable=R0902

    def __init__(self, instance: str, connection: Connection, region: str = "ETS") -> None:
        super().__init__(instance, connection)
        self._region: str = region
        self._additional_epc: bool = True
        self._additional_trs: bool = True
        self._last_memory_call: str = ""
        self._last_write_data: str = ""
        self._inv_called: bool = False
        self._last_inventory: Dict[str, Any] = {'timestamp': None, 'memory': ""}
        self._input_debounce_time = 0.05
        self._tasks_input: Dict[int, asyncio.Task] = {}

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

    # @override
    async def enable_input_events(self, enable: bool = True) -> None:
        if "PULSAR_MX" in self._config['firmware']:
            await self._set_command("SEC", "COMM", "0", "#SPIN0#RIP 0")
            await self._set_command("SEC", "EDGE", "0", "BOTH")
            await self._set_command("SEC", "COMM", "1", "#SPIN1#RIP 1")
            await self._set_command("SEC", "EDGE", "1", "BOTH")
        else:
            await super().enable_input_events(enable)

    def set_input_debounce_time(self, debounce_time: float):
        """Set the input debounce time (for the input event).

        Args:
            debounce_time (float): The debounce time in partial seconds.
                Default is 0.05 seconds.
        """
        self._input_debounce_time = debounce_time if debounce_time >= 0.0 else 0.0

    async def set_region(self, region: str) -> None:
        """Set the used UHF region.

        This has to match the region you are in as well as the antenna(s)
        that are connected to the reader.

        Args:
            region (str): The UHF region, e.g. "ETS", "ISR" or "FCC".

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._set_command("STD", region)

    async def set_profile_parameter(self, parameter: str, value: Any) -> None:
        """Set a reader profile parameter.

        Args:
            parameter (str): The parameter name.

            value (Any): The parameter value.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._set_command("CFG", parameter, value if not isinstance(value, bool) else "ON" if value else "OFF")

    async def get_profile_parameter(self, parameter: str) -> str:
        """Get a reader profile parameter.

        Args:
            parameter (str): The parameter name.

        Returns:
            str: The parameter value.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        data: str = await self._get_command("CFG", "PRP")
        lines: List[str] = data.split('\r')
        if not lines[0].startswith("OK!"):
            raise RfidReaderException(f"Wrong get profile response - {data}")
        param_upper: str = parameter.upper()
        for line in lines[1:]:
            if line.startswith(param_upper):
                return line[len(param_upper)+1:]
        raise RfidReaderException(f"Unknown parameter - {parameter}")

    async def set_power(self, power: int) -> None:
        """Set the reader power.

        Args:
            power (int): The reader power.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        try:
            await self.set_profile_parameter("PWR", power)
        except RfidReaderException as err:
            if "NOR" in str(err):
                raise RfidReaderException(f"Power value {power} out of range") from err
            raise err

    async def get_power(self) -> int:
        """Get the current RF power value for inventories.

        Returns:
            int: The power value in dBm.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        value = await self.get_profile_parameter("PWR")
        return int(value)

    async def set_tag_size(self, tags_size: int) -> None:
        """Configure the expected numbers of transponders in the field.

        Args:
            tags_size (int): Expected number of transponders.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        q_start: int = 0
        while tags_size > pow(2, q_start):
            q_start += 1
        await self._set_command("SQV", q_start)

    # @override
    async def get_inventory(self, single_slot: bool = False, only_new_tags: bool = False) -> List[UhfTag]:
        if self._config['antenna_mode'][0] != "S":
            # Not in single antenna mode ... switch mode
            await self.set_antenna(await self.get_antenna())
        self._inv_called = True
        inv: Dict[str, Any] = await self._get_last_inventory("INV", "SSL" if single_slot else None,
                                                             "ONT" if only_new_tags else None)
        return inv['transponders']

    # @override
    async def get_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                  only_new_tags: bool = False) -> List[UhfTag]:
        if self._config['antenna_mode'][0] != "M":
            # Not in multiplex antenna mode ... switch mode
            await self.set_antenna_multiplex(await self.get_antenna_multiplex())
        inventory: List[UhfTag] = []
        for _ in range(0, await self.get_antenna_multiplex()):
            self._inv_called = True
            inv = await self._get_last_inventory("INV", "SSL" if single_slot else None,
                                                 "ONT" if only_new_tags else None)
            inventory.extend(inv['transponders'])
        return inventory

    # @override
    async def start_inventory(self, single_slot: bool = False, only_new_tags: bool = False) -> None:
        self._inv_called = True
        return await super().start_inventory(single_slot, only_new_tags)

    # @override
    async def start_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                    only_new_tags: bool = False) -> None:
        self._inv_called = True
        return await super().start_inventory_multi(ignore_error, single_slot, only_new_tags)

    async def set_mask(self, mask: str, memory: str = "EPC", start: int = 0, bit_length: Optional[int] = None) -> None:
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
        await self._set_command("SET", "MSK", memory, mask, f'{start:x}' if start >= 0 else None,
                                f'{bit_length:x}' if bit_length else None)

    async def set_epc_mask(self, mask: str, start: int = 0, bit_length: Optional[int] = None) -> None:
        """Set an EPC mask for inventories.

        Args:
            mask (str): The mask value (hex).

            start (int, optional): Start bit. Defaults to 0.

            bit_length (int, optional): Bits to check. Defaults to 0.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self.set_mask(mask, "EPC", 32 + start, bit_length)

    async def reset_mask(self) -> None:
        """Reset and disable inventory mask.
        """
        await self._set_command("SET", "MSK", "OFF")

    async def read_tag_memory(self, start: int = 0, length: int = 1, memory: str = 'USR',
                              ssl: bool = False) -> Dict[str, Any]:
        """Read the memory of the found transponder.

        Args:
            start (int, optional): Beginning at this word. Defaults to 0.

            length (int, optional): Words to read. Defaults to 1.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

            memory (str, optional): Memory bank to read ["EPC","RES", "TID", "USR"].
                Defaults to "USR".

           ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._inv_called = False
        return await self._get_last_inventory("RDT", "SSL" if ssl else None, memory, f'{start:x}', f'{length:x}')

    async def write_tag_memory(self, data: str, start: int = 0, memory: str = 'USR',
                               ssl: bool = False) -> Dict[str, Any]:
        """Write the data to the found transponder.

        Args:
            data (str): The data to write (hex).

            start (int, optional): Beginning at this word. Defaults to 0.

            memory (str, optional): Memory bank to write ["EPC", "RES", "USR"].
                Defaults to "USR".

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._last_write_data = data
        self._inv_called = False
        return await self._get_last_inventory("WDT", "SSL" if ssl else None, memory, f'{start:x}', data)

    async def read_tag_data(self, start: int = 0, length: int = 1, ssl: bool = False) -> Dict[str, Any]:
        """Read the USR memory of the found transponder.

        Args:
            start (int, optional): Beginning at this word. Defaults to 0.

            length (int, optional): Words to read. Defaults to 1.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.read_tag_memory(start, length, 'USR', ssl)

    async def write_tag_data(self, data: str, start: int = 0, ssl: bool = False) -> Dict[str, Any]:
        """Write the USR memory of the found transponder.

        Args:
            data (str): The data to write (hex).

            start (int, optional): Beginning at this word. Defaults to 0.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.write_tag_memory(data, start, 'USR', ssl)

    async def write_tag_epc(self, new_epc: str, ssl: bool = False) -> Dict[str, Any]:
        """Write the EPC memory of the found transponder.

        Args:
            epc (str): The new EPC value. The length must be a multiple
                of 4 hex characters.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        if len(new_epc) % 4:
            raise RfidReaderException(" The new EPC length must be a multiple of 4")
        # prepare new data block 01 with the epc length
        epc_words: int = int(len(new_epc) / 4)
        block01: int = int(epc_words / 2) << 12
        if 1 == epc_words % 2:
            block01 |= 0x0800
        # now get the old block from the current transponders
        response: Dict[str, Any] = await self.read_tag_memory(1, 1, "EPC", ssl)
        transponders: List[UhfTag] = response['transponders']
        if not transponders:
            # no tags found
            return response
        block01_old = None
        for transponder in transponders:
            data = int(str(transponder.get_data()), 16) & 0x7ff
            if not block01_old:
                block01_old = data
            elif data != block01_old:
                raise RfidReaderException("Different tags are in the field, which would result in"
                                          " data loss when writing. Please edit individually.")
        # copy old block data into the new block data
        block01 |= block01_old  # type: ignore
        epc_data = f'{block01:04x}{new_epc}'
        response = await self.write_tag_memory(epc_data, 1, 'EPC', ssl)
        # Deactivate rfid field - so that the transponders are reset
        await self.disable_rfid_field()
        # update transponders
        for transponder in response["transponders"]:
            transponder.set_value("old_epc", transponder.get_epc())
            transponder.set_epc(new_epc)
        return response

    async def read_tag_tid(self, start: int = 0, length: int = 2, ssl: bool = False) -> Dict[str, Any]:
        """Read the TID of the found transponder.

        Args:
            start (int, optional): Beginning at this word. Defaults to 0.

            length (int, optional): Words to read. Defaults to 4.

            epc_mask (str, optional): EPC mask filter. Defaults to None.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.read_tag_memory(start, length, 'TID', ssl)

    async def set_access_password(self, password: str) -> None:
        """Set the access password for authenticated access.

        Args:
            password (str): 8 characters long hexadecimal password
                (32bit access code).
        """
        await self._set_command("SET", "ACP", password)

    async def disable_access_password(self) -> None:
        """Disable the current access password.

        """
        await self._set_command("SET", "ACP", "OFF")

    async def save_access_password(self, slot: int, password: str) -> None:
        """Store an access password in a non-volatile memory of the
        reader for later use
        (so you don't have to transmit it over an unsecure line later).

        Args:
            slot (int): The slot number [0,7].

            password (str): 8 characters long hexadecimal password
                (32 bit access code).
        """
        await self._set_command("SET", "APS", password, slot)

    async def load_access_password(self, slot: int) -> None:
        """Load a stored access password from a non-volatile storage location.

        This is useful for higher security as the password is not sent
        over an insecure line.

        Args:
            slot (int): The slot number [0,7].
        """
        await self._set_command("SET", "APL", slot)

    async def read_tag_access_password(self, ssl: bool = False) -> Dict[str, Any]:
        """Read the access password of the found transponder.

        Args:
            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._inv_called = False
        return await self._get_last_inventory("RDT", "SSL" if ssl else None, "ACP")

    async def write_tag_access_password(self, password: str, ssl: bool = False) -> Dict[str, Any]:
        """Write the access password of the found transponder.

        Args:
            password (str): 8 characters long hexadecimal password
                (32bit access code).

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._last_write_data = password
        self._inv_called = False
        return await self._get_last_inventory("WDT", "SSL" if ssl else None, "ACP", password)

    async def lock_tag_memory(self, mode: int, memory: str, ssl: bool = False) -> Dict[str, Any]:
        """ Lock a memory bank of a transponder.

        The Lock command is used to set the access rights of the different
        data blocks, including the access password itself and the kill password.
        To use this command you have to be in the secured state
        (i.e. authenticated yourself with the correct password).

        Note: The 'EPC', 'TIC', 'USR' memory are in any case readable.

        Args:
            mode (int):
                '0': Data is writeable and readable in any case.

                '1': Data is writeable and readable and may never be locked.

                '2': Data is only writeable and readable in secured state.

                '3': Data is not writeable or readable.

            memory (str): Memory bank to lock.
                Available: ["EPC", "TID", "USR", "ACP", "KLP"].

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._last_write_data = "lock_tag"
        self._inv_called = False
        return await self._get_last_inventory("LCK", "SSL" if ssl else None, memory, mode)

    async def lock_tag_epc(self, mode: int, ssl: bool = False) -> Dict[str, Any]:
        """Lock the tag EPC memory.

        To use this command you have to be in the secured state
        (i.e. authenticated yourself with the correct password).

        Args:
            mode (int):
                '0': EPC is writeable in any case.

                '1': EPC is writeable and may never be locked.

                '2': EPC is only writeable in secured state.

                '3': EPC is not writeable.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.lock_tag_memory(mode, "EPC", ssl)

    async def lock_tag_data(self, mode: int, ssl: bool = False) -> Dict[str, Any]:
        """Lock the tag data memory.

        To use this command you have to be in the secured state
        (i.e. authenticated yourself with the correct password).

        Args:
            mode (int):
                '0': Data is writeable in any case.

                '1': Data is writeable and may never be locked.

                '2': Data is only writeable in secured state.

                '3': Data is not writeable.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.lock_tag_memory(mode, "USR", ssl)

    async def lock_tag_access_password(self, mode: int, ssl: bool = False) -> Dict[str, Any]:
        """Lock the tag access password memory.

        To use this command you have to be in the secured state
        (i.e. authenticated yourself with the correct password).

        Args:
            mode (int):
                '0': Access password is writeable and readable in any case.

                '1': Access password is writeable and readable and may never be locked.

                '2': Access password is only writeable and readable in secured state.

                '3': Access password is not writeable or readable.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.lock_tag_memory(mode, "ACP", ssl)

    async def lock_tag_kill_password(self, mode: int, ssl: bool = False) -> Dict[str, Any]:
        """Lock the tags kill password memory.

        To use this command you have to be in the secured state
        (i.e. authenticated yourself with the correct password).

        Args:
            mode (int):
                '0': Access password is writeable and readable in any case.

                '1': Access password is writeable and readable and may never be locked.

                '2': Access password is only writeable and readable in secured state.

                '3': Access password is not writeable or readable.

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        return await self.lock_tag_memory(mode, "KLP", ssl)

    async def set_kill_password(self, password: str) -> None:
        """Set the kill password.

        For further details on this topic please refer to the EPC Gen 2
        Protocol Description and the kill command.
        The default kill password is 00000000.

        Args:
            password (str): 8 characters long hexadecimal password
            (32bit access code).
        """
        await self._set_command("SET", "KLP", password)

    async def save_kill_password(self, slot: int, password: str) -> None:
        """Store a kill password in a non-volatile memory of the reader
        for later use
        (so you don't have to transmit it over an unsecure line later).

        Args:
            slot (int): The slot number [0,7].

            password (str): 8 characters long hexadecimal password
                (32bit access code).
        """
        await self._set_command("SET", "KPS", password, slot)

    async def load_kill_password(self, slot: int) -> None:
        """Load a stored kill password from a non-volatile storage location.

        This is useful for higher security as the password is not sent
        over an insecure line.

        Args:
            slot (int): The slot number [0,7].
        """
        await self._set_command("SET", "KPL", slot)

    async def read_tag_kill_password(self, ssl: bool = False) -> Dict[str, Any]:
        """Read the kill password of the found transponder.

        Args:
            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._inv_called = False
        return await self._get_last_inventory("RDT", "SSL" if ssl else None, "KPL")

    async def write_tag_kill_password(self, password: str, ssl: bool = False) -> Dict[str, Any]:
        """Write the kill password of the found transponder.

        Args:
            password (str): 8 characters long hexadecimal password
                (32bit access code).

            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._last_write_data = password
        self._inv_called = False
        return await self._get_last_inventory("WDT", "SSL" if ssl else None, "KLP", password)

    async def kill_tag(self, ssl: bool = False) -> Dict[str, Any]:
        """Permanently disable UHF Gen2 tags.

        You must set the kill password before using this command.

        ATTENTION! If you use this command incorrectly you can irreversibly
        kill a big number of UHF tags in a very short time.

        Args:
            ssl (bool, optional): When set to True, only one tag is expected.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            Dict[str, Any]: Dictionary with the read transponders
            `Dict['transponders', List[UhfTag]]`, the transponders with
            an error `Dict['errors', List[UhfTag]]` and the timestamp
            of the execution `Dict['timestamp', float]`.
        """
        self._last_write_data = "kill"
        self._inv_called = False
        return await self._get_last_inventory("KIL", "SSL" if ssl else None)

    async def disable_rfid_field(self) -> None:
        """Disable the RF Field. It is automatically activated at the next transponder scan.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await self._set_command("SRI", "OFF")

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

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    # @override
    async def _config_reader(self) -> None:
        await super()._config_reader()
        await self.set_region(self._region)
        await self._set_verbosity_level()
        await self._enable_additional_epc(self._additional_epc)
        await self._enable_transponder_receive_strength(self._additional_trs)

    # @override
    def _data_received(self, data: str, timestamp: float):
        self.get_logger().debug("data received %s", data.replace(
            "\r", "<CR>").replace("\n", "<LF>"))
        data = data[:-1]
        if data[0] == 'H' and data[2] == 'T':  # HBT
            return
        if data[0] == 'I':
            if data[1] == 'N':  # IN0 | IN1
                self._check_input(int(data[2]), "HI!" in data)
                return
            if data[1] == 'V':  # IVF
                self._parse_inventory(data)
                if self._custom_command:
                    self._add_data_to_receive_buffer(data)
                return
        if data[0] == 'S':
            if data.startswith("SRT"):
                asyncio.ensure_future(self.reset())
                return
        if len(data) > 10 and data[-7:-4] == 'IVF':
            self._parse_inventory(data)
            if self._custom_command:
                self._add_data_to_receive_buffer(data)
            return
        self._add_data_to_receive_buffer(data)

    def _check_input(self, pin: int, status: bool):
        if not self._cb_input_changed:
            return
        if self._input_debounce_time == 0.0:
            self._fire_input_changed_event(pin, status)
        else:
            if pin not in self._tasks_input or self._tasks_input[pin].done():
                self._tasks_input[pin] = asyncio.ensure_future(self._check_input_task(pin, status))

    async def _check_input_task(self, pin, status):
        check_until = time() + self._input_debounce_time
        last_status = status
        while True:
            try:
                await asyncio.sleep(0.01)
            except (TimeoutError, RfidReaderException) as err:
                self.get_logger().info("Check input task stopped - error: %s", err)
                return
            current_status = await self.get_input(pin)
            if current_status != last_status:
                check_until = time() + self._input_debounce_time
                last_status = current_status
            if check_until < time():
                break
        self._fire_input_changed_event(pin, last_status)

    async def _set_verbosity_level(self, level: int = 1) -> None:
        await self._set_command("VBL", level)

    async def _enable_additional_epc(self, enable: bool = True) -> None:
        await self._set_command("SET", "EPC", "ON" if enable else "OFF")
        self._additional_epc = enable

    async def _enable_transponder_receive_strength(self, enable: bool = True) -> None:
        await self._set_command("SET", "TRS", "ON" if enable else "OFF")
        self._additional_trs = enable

    async def _get_last_inventory(self, command: str, *parameters, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Args:
            command (str): the command with a inventory response

            timeout (float): response timeout, default to 2.0

        Raises:
            TimeoutError: if a timeout occurs

        Returns:
            List[Tag]: inventory response
        """
        await self._communication_lock.acquire()
        try:
            self._last_inventory['timestamp'] = None
            self._last_inventory['request'] = self._prepare_command(command, *parameters)
            self._send_command(command, *parameters)
            max_time = time() + timeout
            while max_time > time():
                await asyncio.sleep(0.01)
                if self._last_inventory['timestamp']:
                    break
            else:
                raise TimeoutError("no reader response for inventory command")
            return self._last_inventory
        finally:
            self._communication_lock.release()

    # @override
    def _parse_inventory(self, data: str) -> None:
        # disable 'Too many branches' warning - pylint: disable=R0912
        # disable 'Too many statements' warning - pylint: disable=R0915

        # E0040150954F02B1<CR>E200600311753E33<CR>ARP 12<CR>IVF 02
        timestamp = time()
        lines = data.split('\r')
        lines_count = len(lines) - 1
        inventory: List[UhfTag] = []
        inventory_error: List[UhfTag] = []
        i = 0
        while i < lines_count:
            line = lines[i]
            i += 1
            # check error or additional data
            new_tag = UhfTag("", timestamp)
            if 3 >= len(line) or line[3] == " ":
                if line[0] == "A":
                    if line.startswith("ARP"):  # ARP  Antenna report
                        antenna = int(line[-2:])
                        for tag in inventory:
                            tag.set_antenna(antenna)
                        for tag in inventory_error:
                            tag.set_antenna(antenna)
                        continue
                    if line.startswith("ACE"):  # Access Error
                        new_tag.set_error_message("Access Error")
                        inventory_error.append(new_tag)
                        continue
                elif line[0] == "C":
                    if line.startswith("CER"):
                        new_tag.set_error_message("CRC error")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                elif line[0] == "F":
                    if line.startswith("FLE"):
                        new_tag.set_error_message("FIFO Length Error")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                elif line[0] == "H":
                    if line.startswith("HBE"):
                        new_tag.set_error_message(f"{line} - Header Bit Error")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                # if line[0] == "I": # IVF  - not needed...the last line is skipped
                elif line[0] == "O":
                    if line.startswith("OK!"):
                        # was a write data command...and this tag was ok...replace the OK! with a string
                        # greater than three and rerun
                        i -= 1
                        lines[i] = self._last_write_data
                        continue
                    raise RfidReaderException(f"Inventory error - {line}")
                elif line[0] == "P":
                    if line.startswith("PDE"):
                        new_tag.set_error_message("Preamble Detect Error")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                elif line[0] == "R":
                    if line.startswith("RXE") or line.startswith("RDL"):
                        new_tag.set_error_message("Response Length not as Expected")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                elif line[0] == "T":
                    if line.startswith("TOE"):
                        new_tag.set_error_message("TimeOut Error")
                    elif line.startswith("TCE"):
                        new_tag.set_error_message("Tag Communication Error")
                    elif line.startswith("TOR"):
                        new_tag.set_error_message("Tag Out of Range")
                    else:
                        raise RfidReaderException(f"Inventory error - {line}")
                else:
                    raise RfidReaderException(f"Inventory error - {line}")
                inventory_error.append(new_tag)
            else:
                inventory.append(new_tag)
                if not self._inv_called:
                    index = 4
                    if self._last_inventory['request'][index] == "S":  # Call with SSL (WDT SSL USR)
                        index = 7
                    if self._last_inventory['request'][index] == "T":  # TID request
                        new_tag.set_tid(line)
                    if self._last_inventory['request'][index] != "\r":  # USR, RES, EPC, ACP, KLP
                        new_tag.set_data(line)

            if self._additional_epc:
                new_tag.set_epc(lines[i])
                i += 1
            if self._additional_trs:
                new_tag.set_rssi(int(lines[i]))
                i += 1
        self._last_inventory['transponders'] = inventory
        self._last_inventory['errors'] = inventory_error
        self._last_inventory['timestamp'] = timestamp
        if self._inv_called:
            self._fire_inventory_event(inventory)  # type: ignore
