""" metraTec HF Reader Gen1"""
import asyncio
from time import time
from typing import Any, Callable, Dict, List, Optional
from .reader_exception import RfidReaderException

from .hf_tag import HfTag, HfTagInfo
from .reader_ascii import ReaderAscii
from .reader_ascii import Connection


class HfReaderAscii(ReaderAscii):
    """The implementation of the hf gen1 reader with the **ASCII-protocol.**
    """

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(instance, connection)
        self._last_inventory: Dict[str, Any] = {'timestamp': None}
        self._last_request: Dict[str, Any] = {'timestamp': None}
        self._cb_request: Optional[Callable[[HfTag], None]] = None
        self._rfi_enabled: bool = False

    # @override
    def set_cb_inventory(self, callback: Optional[Callable[[List[HfTag]], None]]
                         ) -> Optional[Callable[[List[HfTag]], None]]:
        """Set the callback for a new inventory.

        Define a callback which will be triggered whenever a new inventory
        result is available. The callback has the following arguments:

        * tags (List[HfTag]) - List of transponders found in the inventory.

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

    def set_cb_request(self, callback: Optional[Callable[[HfTag], None]]
                       ) -> Optional[Callable[[HfTag], None]]:
        """Set the callback for a new request result.

        Define a callback which will be triggered whenever a new request
        result (for example `read_tag_data()`) is available.
        The callback has the following arguments:

        * tags (List[HfTag]) - List of transponders found.

        Returns:
            Optional[Callable]: The old callback.
        """
        old = self._cb_request
        self._cb_request = callback
        return old

    async def enable_rf_interface(self, is_single_sub_carrier: bool = True, modulation_depth: int = 100) -> None:
        """Enable the readers RF interface.

        Args:
            is_single_sub_carrier (bool): If True, the single sub carrier
                mode is used (default).
                Otherwise it will be the double sub carrier mode.

            modulation_depth: Modulation depth, 10% or 100%. Default is 100%.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        if modulation_depth not in (10, 100):
            raise RfidReaderException("Modulation depth must be 100 or 10")
        await self._set_command("SRI", "SS" if is_single_sub_carrier else "DS", modulation_depth)
        self._config['single_sub_carrier'] = True
        self._config['modulation_depth'] = modulation_depth
        self._rfi_enabled = True

    async def disable_rf_interface(self) -> None:
        """Disable the readers RF interface.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._set_command("SRI", "OFF")
        self._rfi_enabled = False

    async def set_mode(self, mode: str = "156"):
        """Set the reader mode.

        Args:
            mode (str): The ISO anti-collision and transmission protocol
                to be used for tag communication.
                Available are "156", "14A" and "14B". Defaults to "156".

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._set_command("MOD", mode)

    async def set_power(self, power: int):
        """Set the output power level of the reader.

        The reader allows different output power levels to match antenna
        size, tag size or tag position.
        The power level is given in milliwatt (mW). The minimum value
        is 500, the maximum is 4000 with steps of 250.

        The second generation ISO 15693 devices with hardware
        revision >= 02.00 (DeskID ISO, UM15, Dwarf15, QR15 and QuasarMX)
        allow setting power values of 100 or 200 (mW).

        Args:
            power (str): Power value in mW.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        try:
            await self._set_command("SET", "PWR", power)
        except RfidReaderException as err:
            if "UPA" in str(err):
                raise RfidReaderException(f"Set power not supported by {self._config['firmware']} version "
                                          f"{self._config['firmware_version']}") from err
            raise err

    # @override
    async def get_inventory(self, single_slot: bool = False, only_new_tags: bool = False,
                            afi: Optional[int] = None) -> List[HfTag]:
        """Get an inventory from the current antenna.

        Args:
            single_slot (bool): If enabled, the reader only searches for
                one transponder, which is faster.
                If more than one transponder is found, an error is raised.
                Defaults to False.

            only_new_tags (bool): The reader finds each transponder only
                once as long as the transponder is powered within the RF
                field of the reader. Defaults to False.

            afi (int): Set the Application Family Identifier. Transponders
                with other AFI will not answer.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[Tag]: An array with the transponders found.
        """
        if self._config['antenna_mode'][0] != "S":
            # Not in single antenna mode ... switch mode
            await self.set_antenna(await self.get_antenna())
        inv: Dict[str, Any] = await self._get_last_inventory("INV", "SSL" if single_slot else None,
                                                             "ONT" if only_new_tags else None,
                                                             "AFI {afi:02X}" if afi else None)
        return inv['transponders']

    # @override
    async def get_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                  only_new_tags: bool = False, afi: Optional[int] = None) -> List[HfTag]:
        """Get an inventory from multiple antennas.

        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors.
                Defaults to False.

            single_slot (bool): If enabled, the reader only searches for
                one transponder, which is faster.
                If more than one transponder is found, an error is raised.
                Defaults to False.

            only_new_tags (bool): The reader finds each transponder only
                once as long as the transponder is powered within the RF
                field of the reader. Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[HfTag]: An array with the transponders found.
        """
        if self._config['antenna_mode'][0] != "M":
            # Not in multiplex antenna mode ... switch mode
            await self.set_antenna_multiplex(await self.get_antenna_multiplex())
        inventory: List[HfTag] = []
        for _ in range(0, await self.get_antenna_multiplex()):
            inv = await self._get_last_inventory("INV", "SSL" if single_slot else None,
                                                 "ONT" if only_new_tags else None,
                                                 "AFI {afi:02X}" if afi else None)
            inventory.extend(inv['transponders'])
        return inventory

    async def start_inventory(self, single_slot: bool = False, only_new_tags: bool = False,
                              afi: Optional[int] = None) -> None:
        """Start a continuous inventory.

        This will cause the reader to perform inventories continuously
        until the `stop_inventory()` function is called.

        Args:
            single_slot (bool): If enabled, the reader only searches for
                one transponder, which is faster.
                If more than one transponder is found, an error is raised.
                Defaults to False.

            only_new_tags (bool): The reader finds each transponder only
                once as long as the transponder is powered within the RF
                field of the reader. Defaults to False.

            afi (int): Set the Application Family Identifier. Transponders
                with other AFI will not answer.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        # Method from ReaderGen1 overridden
        if self._config['antenna_mode'][0] != "S":
            # Not in single antenna mode ... switch mode
            await self.set_antenna(await self.get_antenna())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None,
                           "AFI {afi:02X}" if afi else None)

    async def start_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                    only_new_tags: bool = False, afi: Optional[int] = None) -> None:
        """Start a continuous inventory on multiple antennas.

        This will cause the reader to perform inventories continuously
        until the `stop_inventory_multi()` function is called.
        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna
                errors. Defaults to False.

            single_slot (bool): If enabled, the reader only searches for
                one transponder, which is faster.
                If more than one transponder is found, an error is raised.
                Defaults to False.

            only_new_tags (bool): The reader finds each transponder only
                once as long as the transponder is powered within the RF
                field of the reader. Defaults to False.

            afi (int): Set the Application Family Identifier. Transponders
                with other AFI will not answer.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        # Method from ReaderGen1 overridden
        if self._config['antenna_mode'][0] != "M":
            # Not in multiplex antenna mode ... switch mode
            await self.set_antenna_multiplex(await self.get_antenna_multiplex())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None,
                           "AFI {afi:02X}" if afi else None)

    async def read_tag_data(self, block_number: int, tag_id: Optional[str] = None,
                            option_flag: bool = False) -> HfTag:
        """Read the memory of a transponder.

        Args:
            block_number (int): Block number to read.

            tag_id (str, optional): Transponder to be read, defined by its
                tag ID. If not set, the currently available transponder is read.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTag: The transponder that was read.
        """
        return await self._send_request("REQ", "20", f"{block_number:02X}", tag_id, option_flag)

    async def read_tag_information(self, tag_id: Optional[str] = None,
                                   option_flag: bool = False) -> HfTagInfo:
        """Read the transponder information.

        Args:
            tag_id (str, optional): Transponder to be read, defined by its
                tag ID. If not set, the currently available transponder is read.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTagInfo: The transponder info that was read.
        """
        response = await self._send_request("REQ", "2B", None, tag_id, option_flag)

        return HfTagInfo(response.get_tid(), response.get_data(), response.get_error_message(),
                         response.get_timestamp(), response.get_antenna(), response.get_seen_count())

    async def write_tag_data(self, block_number: int, data: str, tag_id: Optional[str] = None,
                             option_flag: bool = False) -> HfTag:
        """Write the USR memory of a transponder.

        Args:
            block_number (int): Block number to write.

            data (str): Data to write.

            tag_id (str, optional): Transponder to write, defined by its
                tag ID. If not set, the currently available transponder is written.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTag: The transponder that was written.
        """
        return await self._send_request("WRQ", "21", f"{block_number:02X}{data}", tag_id, option_flag)

    async def write_tag_afi(self, afi: int, tag_id: Optional[str] = None,
                            option_flag: bool = False) -> HfTag:
        """Write the Application Family Identifier value of a transponder.

        Args:
            afi (int): The Application Family Identifier to set.

            tag_id (str, optional): Transponder to write, defined by its
                tag ID. If not set, the currently available transponder is written.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If an reader error occurs.

        Returns:
            HfTag: The transponder that was written.
        """
        return await self._send_request("WRQ", "27", f"{afi:02X}", tag_id, option_flag)

    async def lock_tag_afi(self, tag_id: Optional[str] = None, option_flag: bool = False) -> HfTag:
        """Lock the Application Family Identifier of a transponder.

        Args:
            tag_id (str, optional): Transponder to lock, defined by its
                tag ID. If not set, the currently available transponder is locked.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTag: The transponder that was locked.
        """
        return await self._send_request("WRQ", "28", None, tag_id, option_flag)

    async def write_tag_dsfid(self, dsfid: int, tag_id: Optional[str] = None,
                              option_flag: bool = False) -> HfTag:
        """Write the Data Storage Format Identifier of a transponder.

        Args:
            dsfid (int): The Data Storage Format Identifier to set.

            tag_id (str, optional): Transponder to write, defined by its
                tag ID. If not set, the currently available transponder is written.

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTag: The transponder that was written.
        """
        return await self._send_request("WRQ", "29", f"{dsfid:02X}", tag_id, option_flag)

    async def lock_tag_dsfid(self, tag_id: Optional[str] = None, option_flag: bool = False) -> HfTag:
        """Lock the Data Storage Format Identifier of a transponder.

        Args:
            tag_id (str, optional): Transponder to lock, defined by its
                tag ID. If not set, the currently available transponder is locked.

            option_flag (bool, optional): Meaning is defined by the tag
                command description.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            HfTag: The transponder that was locked.
        """
        return await self._send_request("WRQ", "2A", None, tag_id, option_flag)

    # @override
    async def fetch_inventory(self, wait_for_tags: bool = True) -> List[HfTag]:  # type: ignore
        """
        Can be called when an inventory has been started. Waits until at least one tag is found
        and returns all currently scanned transponders from a continuous scan.

        Args:
            wait_for_tags (bool): Set to true, to wait until transponders are available.

        Returns:
            List[HfTag]: A list with the transponders found.
        """
        return await super().fetch_inventory(wait_for_tags)  # type: ignore

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    # @override
    async def _config_reader(self) -> None:
        await super()._config_reader()
        await self.enable_rf_interface()

    # @override
    def _data_received(self, data: str, timestamp: float):
        # disable 'Too many return statements' warning - pylint: disable=R0911
        self.get_logger().debug("data received %s", data.replace(
            "\r", "<CR>").replace("\n", "<LF>"))
        data = data[:-1]
        if data[0] == 'H' and data[2] == 'T':  # HBT
            return
        if data[0] == 'T':
            if data[1] == 'D' or data[1] == 'N':  # TDT TND
                self._parse_request(data)
                if self._custom_command:
                    self._add_data_to_receive_buffer(data)
                return
        if data[0] == 'I':
            if data[1] == 'V':  # IVF
                self._parse_inventory(data)
                if self._custom_command:
                    self._add_data_to_receive_buffer(data)
                return
        if data[0] == 'R' and data[2] == 'W':  # RNW Registers Not Written
            self._rfi_enabled = False
            return
        if data[0] == 'S':
            if data.startswith("SRT"):
                asyncio.ensure_future(self.reset())
                return
        if len(data) >= 10 and data[-6:-3] == 'IVF':
            self._parse_inventory(data)
            if self._custom_command:
                self._add_data_to_receive_buffer(data)
            return
        self._add_data_to_receive_buffer(data)

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
            self._last_inventory['request'] = self._prepare_command(
                command, *parameters)
            self._send_command(command, *parameters)
            max_time = time() + timeout
            while max_time > time():
                await asyncio.sleep(0.01)
                if self._last_inventory['timestamp']:
                    break
            else:
                if self._rfi_enabled:
                    raise TimeoutError(
                        "no reader response for inventory command")
                raise RfidReaderException("RF interface not enabled")
            return self._last_inventory
        finally:
            self._communication_lock.release()

    # @override
    def _parse_inventory(self, data: str) -> None:
        # E0040150954F02B1<CR>E200600311753E33<CR>ARP 12<CR>IVF 02
        timestamp = time()
        split = data.split('\r')
        inventory: List[HfTag] = []
        inventory_error: List[HfTag] = []
        for line in split[0:-1]:
            if line[1] == "R" and line[2] == "P":  # ARP  Antenna report
                antenna = int(line[-2:])
                for tag in inventory:
                    tag.set_antenna(antenna)
                continue
            new_tag = HfTag(line, timestamp)
            inventory.append(new_tag)
        self._last_inventory['transponders'] = inventory
        self._last_inventory['errors'] = inventory_error
        self._last_inventory['timestamp'] = timestamp
        self._fire_inventory_event(inventory)  # type: ignore

    async def _send_request(self, command: str, tag_command: str, data: Optional[str],
                            tag_id: Optional[str] = None, option_flag: bool = False) -> HfTag:
        """_summary_

        Args:
            command (str): The request command "REQ" or "WRQ".

            tag_command (str): The tag command.

            data (Optional[str]): The additional data.

            tag_id (Optional[str], optional): The transponder id. Defaults to None.

            option_flag (bool, optional): The option flag. Defaults to False.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The transponder data

            Dict['error', str: The transponder error if data is empty

            Dict['timestamp', float]: the timestamp
        """
        # disable 'Too many arguments' warning - pylint: disable=R0913
        # disable 'Too many positional arguments' warning - pylint: disable=R0917
        if tag_id:
            self._last_request['tid'] = tag_id
            flags = f"{'6' if option_flag else '2'}{'2' if self._config.get('single_sub_carrier', True) else '3'}"\
                f"{tag_command}{tag_id}{data if data else ''}"
        else:
            self._last_request['tid'] = ""
            flags = f"{'4' if option_flag else '0'}{'2' if self._config.get('single_sub_carrier', True) else '3'}"\
                f"{tag_command}{data if data else ''}"
        response = await self._get_last_request(command, flags, "CRC")
        return response

    def _parse_request(self, data: str) -> None:
        # TDT<CR>0011112222B7DD<CR>COK<CR>NCL<CR>
        # TNR<CR>
        timestamp = time()
        tag_data = ""
        error = ""
        split = data.split('\r')
        last_element = len(split) - 1
        antenna = None
        if "ARP" in split[last_element]:
            # Antenna report added
            antenna = int(split[last_element][4])
            last_element -= 1
        if split[last_element] == "NCL":
            if split[2] == "COK":
                if split[1][0:2] == "00":
                    tag_data = split[1][2:-4]
                else:
                    error = f"TEC {split[1][2:4]}"
            else:
                error = split[2]
        else:
            # CDT - Collision detect
            # TNR - Tag not responding - no tag
            # RDL - read data too long
            error = split[last_element]
        tag = HfTag(self._last_request.get('tid', ""), timestamp, antenna)
        tag.set_error_message(error)
        tag.set_data(tag_data)
        self._last_request['response'] = tag
        self._last_request['timestamp'] = timestamp
        if self._cb_request and tag_data:
            self._cb_request(tag)

    async def _get_last_request(self, command: str, *parameters, timeout: float = 2.0) -> HfTag:
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
            self._last_request['timestamp'] = None
            self._last_request['request'] = self._prepare_command(
                command, *parameters)
            self._send_command(command, *parameters)
            max_time = time() + timeout
            while max_time > time():
                await asyncio.sleep(0.01)
                if self._last_request['timestamp']:
                    break
            else:
                if self._rfi_enabled:
                    raise TimeoutError(
                        "no reader response for inventory command")
                raise RfidReaderException("RF interface not enabled")
            return self._last_request['response']
        finally:
            self._communication_lock.release()
