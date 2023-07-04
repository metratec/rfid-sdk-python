""" metraTec HF Reader Gen1"""
import asyncio
from time import time
from typing import Any, Callable, Dict, List, Optional
from .reader_exception import RfidReaderException

from .hf_tag import HfTag
from .reader_gen1 import ReaderGen1
from .reader_gen1 import Connection


class HfReaderGen1(ReaderGen1):
    """The implementation of the uhf gen2 reader with the **AT-protocol.**
    """

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(instance, connection)
        self._last_inventory: Dict[str, Any] = {'timestamp': None}
        self._last_request: Dict[str, Any] = {'timestamp': None}
        self._cb_request: Optional[Callable[[str], None]] = None
        self._rfi_enabled: bool = False

    async def _prepare_reader(self) -> None:
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
                return
        if data[0] == 'I':
            if data[1] == 'V':  # IVF
                self._parse_inventory(data)
                return
        if data[0] == 'R' and data[2] == 'W':  # RNW Registers Not Written
            self._rfi_enabled = False
            return
        if data[0] == 'S':
            if data.startswith("SRT"):
                # TODO Reader reset
                return
        if len(data) >= 10 and data[-6:-3] == 'IVF':
            self._parse_inventory(data)
            return
        self._add_data_to_receive_buffer(data)

    # @override
    def set_cb_inventory(self, callback: Optional[Callable[[List[HfTag]], None]]
                         ) -> Optional[Callable[[List[HfTag]], None]]:
        """
        Set the callback for a new inventory. The callback has the following arguments:
        * tags (List[HfTag]) - the tags

        Returns:
            Optional[Callable]: the old callback
        """
        return super().set_cb_inventory(callback)

    # @override
    async def fetch_inventory(self, wait_for_tags: bool = True) -> List[HfTag]:  # type: ignore
        """
        Can be called when an inventory has been started. Waits until at least one tag is found
        and returns all currently scanned transponders from a continuous scan

        Args:
            wait_for_tags (bool): Set to true, to wait until transponders are available

        Returns:
            List[HfTag]: a list with the founded transponder
        """
        return await super().fetch_inventory(wait_for_tags)  # type: ignore

    def set_cb_request(self, callback: Optional[Callable[[str], None]]
                       ) -> Optional[Callable[[str], None]]:
        """
        Set the callback for a new inventory. The callback has the following arguments:
        * tags (List[HfTag]) - the tags

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_request
        self._cb_request = callback
        return old

    async def enable_rf_interface(self, is_single_sub_carrier: bool = True, modulation_depth: int = 100) -> None:
        """enable the reader rf interface

        Args:
            is_single_sub_carrier (bool): if True, the single sub carrier otherwise the double sub carrier mode is used.
            Default is True

            modulation_depth: modulation depth, 10% or 100%. Default is 100

        Raises:
            RfidReaderException: if an reader error occurs
        """
        if modulation_depth not in (10, 100):
            raise RfidReaderException("Modulation depth must be 100 or 10")
        await self._set_command("SRI", "SS" if is_single_sub_carrier else "DS", modulation_depth)
        self._config['single_sub_carrier'] = True
        self._config['modulation_depth'] = modulation_depth
        self._rfi_enabled = True

    async def disable_rf_interface(self) -> None:
        """disable the reader rf interface

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await self._set_command("SRI", "OFF")
        self._rfi_enabled = False

    async def set_mode(self, mode: str = "156"):
        """Sets the reader mode

        Args:
            mode (str): the ISO anti-collision and transmission protocol to be used for tag communication.
                        Available: "156", "14A", "14B". Defaults to "156"

        Raises:
            RfidReaderException: if an reader error occurs
        """
        await self._set_command("MOD", mode)

    async def set_power(self, power: int):
        """
        The reader allows different output power levels to match antenna size, tag size or tag position.
        The power level is given in milliwatt (mW). The minimum value is 500, the maximum is 4000 with steps of 250.

        The second generation ISO 15693 devices with hardware revision >= 02.00 (DeskID ISO, UM15,
        Dwarf15, QR15 and QuasarMX) allow setting power values of 100 or 200 (mW).

        Args:
            power (str): power in mW

        Raises:
            RfidReaderException: if an reader error occurs
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
        """get the current inventory from the current antenna (see set_antenna)

        Args:
            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

            afi (int): Set the application family identifier . Transponder with other api will not answer.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[Tag]: An array with the founded transponder
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
        """get the current inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.

            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

            afi (int): Set the application family identifier . Transponder with other api will not answer.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            List[Tag]: An array with the founded transponder
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
        """Starts the continuos inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

            afi (int): Set the application family identifier . Transponder with other api will not answer.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        # Method from ReaderGen1 overridden
        if self._config['antenna_mode'][0] != "S":
            # Not in single antenna mode ... switch mode
            await self.set_antenna(await self.get_antenna())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None,
                           "AFI {afi:02X}" if afi else None)

    async def start_inventory_multi(self, ignore_error: bool = False, single_slot: bool = False,
                                    only_new_tags: bool = False, afi: Optional[int] = None) -> None:
        """Starts the continuos inventory. Multiple antennas are used (see set_antenna_multiplex)

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.

            single_slot (bool): If activated the reader only searches for one transponder. this is faster.
            If more than one transponder is found, an error is thrown. Defaults to False.

            only_new_tags (bool): the reader finds each transponder only once as long as the transponder is
            powered within the RF field of the reader. Defaults to False.

            afi (int): Set the application family identifier . Transponder with other api will not answer.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        # Method from ReaderGen1 overridden
        if self._config['antenna_mode'][0] != "M":
            # Not in multiplex antenna mode ... switch mode
            await self.set_antenna_multiplex(await self.get_antenna_multiplex())
        self._send_command("CNR INV", "SSL" if single_slot else None, "ONT" if only_new_tags else None,
                           "AFI {afi:02X}" if afi else None)

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
                if self._rfi_enabled:
                    raise TimeoutError("no reader response for inventory command")
                raise RfidReaderException("RF interface not enabled")
            return self._last_inventory
        finally:
            self._communication_lock.release()

    async def read_tag_data(self, block_number: int, tag_id: Optional[str] = None,
                            option_flag: bool = False) -> Dict[str, Any]:
        """read the memory of the transponder

        Args:
            block_number (int): block to read

            tag_id (str, optional): transponder to be read, if not set, the currently available transponder is read

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The transponder data

            Dict['error', str: The transponder error if data is empty

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("REQ", "20", f"{block_number:02X}", tag_id, option_flag)

    async def _send_request(self, command: str, tag_command: str, data: Optional[str],
                            tag_id: Optional[str] = None, option_flag: bool = False) -> Dict[str, Any]:
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
        if tag_id:
            flags = f"{'6' if option_flag else '2'}{'2' if self._config.get('single_sub_carrier', True) else '3'}"\
                f"{tag_command}{tag_id}{data if data else ''}"
        else:
            flags = f"{'4' if option_flag else '0'}{'2' if self._config.get('single_sub_carrier', True) else '3'}"\
                f"{tag_command}{data if data else ''}"
        response: Dict[str, Any] = await self._get_last_request(command, flags, "CRC")
        return response

    async def read_tag_information(self, tag_id: Optional[str] = None,
                                   option_flag: bool = False) -> Dict[str, Any]:
        """read the transponder information

        Args:
            tag_id (str, optional): transponder to be read, if not set, the currently available transponder is read

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The transponder data

            Dict['error', str: The transponder error if data is empty

            Dict['timestamp', float]: the timestamp
        """
        response: Dict[str, Any] = await self._send_request("REQ", "2B", None, tag_id, option_flag)
        data = response['data']
        if data:
            info_flag = int(data[0:2], 16)
            response['is_dsfid'] = (bool)(info_flag & 0x01)
            if response['is_dsfid']:
                response['dsfid'] = int(data[16:18], 16)
            response['is_afi'] = (bool)(info_flag & 0x02)
            if response['is_afi']:
                response['afi'] = int(data[18:20], 16)
            response['is_vicc'] = (bool)(info_flag & 0x04)
            if response['is_vicc']:
                response['vicc_number_of_block'] = int(data[20:22], 16) + 1
                response['vicc_block_size'] = (int(data[22:24], 16) & 0x3F) + 1
            response['is_icr'] = (bool)(info_flag & 0x08)
            if response['is_icr']:
                response['icr'] = int(data[24:26], 16)
        return response

    async def write_tag_data(self, block_number: int, data: str, tag_id: Optional[str] = None,
                             option_flag: bool = False) -> Dict[str, Any]:
        """write the usr memory of the found transponder

        Args:
            block_number (int): block to write

            data (str): data to write

            tag_id (str, optional): transponder to be write, if not set, the currently available transponder is write

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The read transponders

            Dict['error', str]: the error message if data

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("WRQ", "21", f"{block_number:02X}{data}", tag_id, option_flag)

    async def write_tag_afi(self, afi: int, tag_id: Optional[str] = None,
                            option_flag: bool = False) -> Dict[str, Any]:
        """write the transponder application family identifier value

        Args:
            afi (int): the application family identifier to set

            tag_id (str, optional): transponder to be write, if not set, the currently available transponder is write

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The read transponders

            Dict['error', str]: the error message if data

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("WRQ", "27", f"{afi:02X}", tag_id, option_flag)

    async def lock_tag_afi(self, tag_id: Optional[str] = None, option_flag: bool = False) -> Dict[str, Any]:
        """Lock the transponder application family identifier

        Args:
            tag_id (str, optional): transponder to be write, if not set, the currently available transponder is write

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The read transponders

            Dict['error', str]: the error message if data

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("WRQ", "28", None, tag_id, option_flag)

    async def write_tag_dsfid(self, dsfid: int, tag_id: Optional[str] = None,
                              option_flag: bool = False) -> Dict[str, Any]:
        """write the transponder data storage format identifier

        Args:
            dsfid (int): the data storage format identifier to set

            tag_id (str, optional): transponder to be write, if not set, the currently available transponder is write

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The read transponders

            Dict['error', str]: the error message if data

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("WRQ", "29", f"{dsfid:02X}", tag_id, option_flag)

    async def lock_tag_dsfid(self, tag_id: Optional[str] = None, option_flag: bool = False) -> Dict[str, Any]:
        """Lock the transponder data storage format identifier

        Args:
            tag_id (str, optional): transponder to be write, if not set, the currently available transponder is write

            option_flag (bool, optional): Meaning is defined by the tag command description.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Dict['data', str]: The read transponders

            Dict['error', str]: the error message if data

            Dict['timestamp', float]: the timestamp
        """
        return await self._send_request("WRQ", "2A", None, tag_id, option_flag)

    def _parse_request(self, data: str) -> None:
        # TDT<CR>0011112222B7DD<CR>COK<CR>NCL<CR>
        # TNR<CR>
        timestamp = time()
        tag_data = ""
        error = ""
        split = data.split('\r')
        last_element = len(split) - 1
        if "ARP" in split[last_element]:
            # Antenna report added
            self._last_request['antenna'] = int(split[last_element][4])
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
        self._last_request['data'] = tag_data
        self._last_request['error'] = error
        self._last_request['timestamp'] = timestamp
        if self._cb_request and tag_data:
            self._cb_request(tag_data)

    async def _get_last_request(self, command: str, *parameters, timeout: float = 2.0) -> Dict[str, Any]:
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
            self._last_request['request'] = self._prepare_command(command, *parameters)
            self._send_command(command, *parameters)
            max_time = time() + timeout
            while max_time > time():
                await asyncio.sleep(0.01)
                if self._last_request['timestamp']:
                    break
            else:
                if self._rfi_enabled:
                    raise TimeoutError("no reader response for inventory command")
                raise RfidReaderException("RF interface not enabled")
            return self._last_request
        finally:
            self._communication_lock.release()
