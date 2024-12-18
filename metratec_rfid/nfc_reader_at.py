""" metratec nfc reader second generation
"""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from time import time
from .connection.connection import Connection
from .hf_tag import HfTag, ISO14ATag, ISO15Tag
from .reader import RfidReader
from .reader_exception import RfidReaderException, RfidTransponderException
from .reader_at import ReaderAT

# disable 'Too many lines in module' warning - pylint: disable=C0302


class NfcMode(Enum):
    """NFC reader operation modes."""

    AUTO = 1
    """Automatically detect the necessary mode."""

    ISO15 = 2
    """ISO 15 mode."""

    ISO14A = 3
    """ISO 14A mode."""


class NTagMirrorMode(Enum):
    """NTAG mirror modes."""

    OFF = 0
    """Mirror mode disabled."""

    UID = 1
    """Mirror Unique Identifier."""

    CNT = 2
    """Mirror NFC counter."""

    BOTH = 3
    """Mirror both."""


class NdefState(Enum):
    """NDEF state of a tag."""

    NO_NDEF = 0
    """No NDEF found on tag."""

    INITIALIZED = 1
    """Tag is ready to be written."""

    RO = 2
    """NDEF data is read only."""

    RW = 3
    """NDEF data is readable and writable."""

    MISCONFIGURED = 4
    """Tag is not correctly formatted for NDEF usage."""


class NfcReaderAT(ReaderAT):
    """The implementation of the uhf gen2 reader with the **AT-protocol.**
    """

    # disable 'Too many public methods' warning - pylint: disable=R0904
    # disable 'Too many instance attributes' warning - pylint: disable=R0902

    def __init__(self, instance: str, connection: Connection) -> None:
        super().__init__(instance, connection)
        self._mode = NfcMode.AUTO
        self._selected_tag: str = ""
        self._config: dict = {}

    ###################################################################################################################
    # RFID SETTINGS                                                                                                   #
    ###################################################################################################################

    async def enable_rf_interface(self):
        """Enable the readers RF interface.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+CW", 1)

    async def disable_rf_interface(self):
        """Disable the readers RF interface.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+CW", 0)

    async def set_mode(self, mode: NfcMode):
        """Set the readers operation mode.

        Note: Must import the `NfcMode` class from metratec_rfid.

        Args:
            mode (NfcMode): NfcMode.AUTO, NfcMode.ISO15 or NfcMode.ISO14A.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+MOD", mode.name)
        self._mode = mode

    async def get_mode(self) -> NfcMode:
        """Return the current reader mode.

        Returns:
            NfcMode: The current operation mode.
        """
        responses = await self._send_command("AT+MOD?")
        #  +MOD: AUTO
        mode = NfcMode[responses[0][6:]]
        self._mode = mode
        return mode

    async def config_rf_interface(self, is_single_sub_carrier: bool = True, modulation_depth: int = 100) -> None:
        """Configure the readers RF interface.

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
        await self._send_command("AT+CRI", "SINGLE" if is_single_sub_carrier else "DOUBLE",
                                 modulation_depth)

    ###################################################################################################################
    # TAG OPERATIONS                                                                                                  #
    ###################################################################################################################

    async def set_inventory_settings(self, enable_tag_details: bool = True, only_new_tags: bool = False,
                                     single_slot: bool = False) -> None:
        """Configure the inventory response.

        Args:
            enable_tag_details (bool, optional): To add additional information
                about the tag in the inventory response.
                Only if the reader is not in AUTO mode. Defaults to True.

            only_new_tags (bool, optional): If enabled, a Stay Quiet is
                sent to each tag in the field after a successful inventory.
                This has the effect that any tag that remains in the field
                is only found once in an inventory. Defaults to False.

            single_slot (bool, optional): Has only an effect in ISO15 mode.
                If it is set to 1 ISO15 inventories will be run in single
                slotted mode, resulting in faster inventories. There will
                be no anti-collision loop performed so an inventory with
                multiple tags in the field will result in failure.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+INVS", 1 if enable_tag_details else 0, 1 if only_new_tags else 0, 1 if single_slot
                                 else 0)

        # update configuration
        config: Dict[str, Any] = self._config['inventory']
        config['enable_tag_details'] = enable_tag_details
        config['only_new_tags'] = only_new_tags
        config['single_slot'] = single_slot

    async def get_inventory_settings(self) -> Dict[str, Any]:
        """Get the current reader inventory settings.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            dict: Dictionary with keys 'enable_tag_details',
            'only_new_tags' and 'single_slot'.
        """
        responses: List[str] = await self._send_command("AT+INVS?")
        # +INVS: 1,0,0
        data: List[str] = responses[0][7:].split(',')
        try:
            config: Dict[str, bool] = {'enable_tag_details': data[0] == '1',
                                       'only_new_tags': data[1] == '1',
                                       'single_slot': data[2] == '1'}
            self._config['inventory'] = config.copy()
            return config
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+INVS? - {responses}") from exc

    async def get_inventory(self) -> List[HfTag]:
        responses = await self._send_command("AT+INV")
        inventory = self._parse_inventory(responses, time())
        current_antenna = self._config.get('antenna', 1)
        for tag in inventory:
            tag.set_antenna(current_antenna)
        self._fire_inventory_event(inventory, False)  # type: ignore
        return inventory

    async def get_inventory_multi(self, ignore_error: bool = False) -> List[HfTag]:
        """Get an inventory from multiple antennas.

        Antenna ports are chosen according to `set_antenna_multiplex()`.

        Args:
            ignore_error (bool, optional): Set to True to ignore antenna errors.
                Defaults to False.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[Tag]: An array with the transponders found.
        """
        # pylint: disable=unused-argument

        return await self.get_inventory()

    async def detect_tag_types(self) -> List[HfTag]:
        """Detect the type of tags that are in the RF field.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            List[HfTag]: List with the detected tags.
        """
        responses = await self._send_command("AT+DTT")
        timestamp = time()
        # +DTT: E002223504422958,ISO15
        tags: List[HfTag] = []
        current_antenna = self._config.get('antenna', 1)
        for response in responses:
            if response[6] == '<':
                # error messages: <NO TAGS FOUND>
                if response[7] == 'N':  # NO TAGS FOUND
                    continue
            info = response[6:].split(',')
            if info[1] == "ISO15":
                tag: HfTag = ISO15Tag(info[0], timestamp, current_antenna)
            else:
                tag = ISO14ATag(info[0], timestamp, current_antenna, tag_type=info[1])
            tags.append(tag)
        return tags

    async def select_transponder(self, tid: str) -> None:
        """Select a transponder by its tag ID.

        Args:
            tid (str): The transponder TID.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+SEL", tid)
        self._selected_tag = tid

    async def get_selected_transponder(self) -> str:
        """Get the currently selected transponder.

        Returns:
            str: The currently selected transponder TID.
            If no transponder is selected, the return value is empty.
        """
        # await self._send_command("AT+SEL?")
        return self._selected_tag

    async def deselect_transponder(self) -> None:
        """Deselect the currently selected tag.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+DEL")
        self._selected_tag = ""

    async def write_data(self, block: int, data: str, option_flag: Optional[bool] = None) -> None:
        """Write data to a block of the tags memory.

        Depending on the protocol a select and authenticate is needed
        prior to this command.

        Args:
            block (int): Number of the block to write.
            data (str): Data to write to the card.
            option_flag (bool): Set to True if needed, only in ISO15 mode.
        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+WRT", block, data, option_flag)

    async def read_data(self, block: int, number_of_blocks: int = 1) -> str:
        """Read data from the cards memory.

        Depending on the protocol a select and authenticate is needed
        prior to this command.

        Args:
            block (int): The block (start block) to read.
            number_of_blocks (int): Number of blocks to be read, defaults to 1.

        Returns:
            str: The block data as hex string.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """

        if number_of_blocks > 1:
            responses = await self._send_command("AT+READM", block, number_of_blocks)
            data = ""
            for response in responses:
                data += response[8:]
            return data
        responses = await self._send_command("AT+READ", block)
        return responses[0][7:]

    async def read_data_with_option_flag(self, block: int, number_of_blocks: int = 1) -> tuple[str, str]:
        """Read data from the cards memory with option flag.

        Only in ISO15 mode.

        Args:
            block (int): The block (start block) to read.
            number_of_blocks (int): Number of blocks to read, defaults to 1.

        Returns:
            tuple[str, str]: Data and the security block status byte as hex.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if number_of_blocks > 1:
            responses = await self._send_command("AT+READM", block, number_of_blocks, 1)
            data = ""
            flags = ""
            for response in responses:
                split = response[8:].split(",")
                data += split[0]
                flags += split[1] if len(split) > 1 else ""
            return data, flags
        responses = await self._send_command("AT+READ", block, 1)
        split = responses[0][7:].split(",")
        return split[0], split[1] if len(split) > 1 else ""

    ###################################################################################################################
    # ISO15693 Commands                                                                                               #
    ###################################################################################################################

    # async def send_read_request(self, request: str) -> HfTag:
    #     """Send an ISO15693 request with read-alike timing to a card.

    #     Args:
    #         request (str): the request

    #     Returns:
    #         HfTag: the response

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #     """
    #     if self._mode is not Mode.ISO15:
    #         raise RfidReaderException("Only available in ISO15 mode!")
    #     responses = await self._send_command("AT+RRQ", request)
    #     tag = HfTag("", time())
    #     tag.set_data(responses[0][6:])
    #     return tag

    async def send_read_request_iso15693(self, request: str) -> str:
        """Send an ISO15693 read request with read-alike timing to a card.

        Args:
            request (str): The request.

        Returns:
            str: The response.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if self._mode is not NfcMode.ISO15:
            raise RfidReaderException("Only available in ISO15 mode!")
        responses = await self._send_command("AT+RRQ", request)
        return responses[0][6:]

    async def send_write_request_iso15693(self, request: str) -> None:
        """Send an ISO15693 write request with write-alike timing to a card.

        Args:
            request (str): The request.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if self._mode is not NfcMode.ISO15:
            raise RfidReaderException("Only available in ISO15 mode!")
        await self._send_command("AT+WRQ", request)

    async def set_afi(self, afi: str) -> None:
        """Set the Application Family Identifier for IOS15693 inventories.

        An AFI of 0 is treated as no AFI set. If set to non-zero only
        transponders with the same AFI will respond in a inventory.

        Args:
            afi (str): Application Family Identifier as hex string [00..FF].

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        if isinstance(afi, int):
            afi = f"{afi:02X}"
        if len(afi) != 2:
            raise RfidReaderException("AFI must be in range from '00' to 'FF'")
        await self._send_command("AT+AFI", afi)

    async def get_afi(self) -> str:
        """Return the Application Family Identifier for IOS15693 inventories.

        Returns:
            int: The Application Family Identifier of the reader.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        responses = await self._send_command("AT+AFI?")
        # +AFI: 0A
        return responses[0][6:]

    async def write_tag_afi(self, afi: str, option_flag: bool = False) -> None:
        """Write the Application Family Identifier to an ISO15693 transponder.

        Args:
            afi (int): AFI value.
            option_flag (bool, optional): ISO15693 request option flag.
                Defaults to False.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if isinstance(afi, int):
            afi = f"{afi:02X}"
        if len(afi) != 2:
            raise RfidReaderException("AFI must be in range from '00' to 'FF'")
        await self._send_command("AT+WAFI", afi, 1 if option_flag else 0)

    async def lock_tag_afi(self, option_flag: bool = False) -> None:
        """Permanently lock the AFI of an ISO15693 transponder.

        Args:
            option_flag (bool, optional): ISO15693 request option flag.
                Defaults to False.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("ATI+LAFI", 1 if option_flag else 0)

    async def write_tag_dsfid(self, dsfid: str, option_flag: bool = False) -> None:
        """Write the Data Storage Format Identifier to an ISO15693 transponder.

        Args:
            dsfid (str): DSFID value as hex string.
            option_flag (bool, optional): ISO15693 request option flag.
                Defaults to False.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if isinstance(dsfid, int):
            dsfid = f"{dsfid:02X}"
        if len(dsfid) != 2:
            raise RfidReaderException("DSFID must be in range from '00' to 'FF'")
        await self._send_command("AT+WDSFID", dsfid, 1 if option_flag else 0)

    async def lock_tag_dsfid(self, option_flag: bool = False) -> None:
        """Permanently lock the Data Storage Format Identifier of an ISO15693 transponder.

        Args:
            option_flag (bool, optional): ISO15693 request option flag.
                Defaults to False.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+LDSFID", 1 if option_flag else 0)

    ###################################################################################################################
    # ISO14A Commands                                                                                                 #
    ###################################################################################################################

    # Generic ISO14A Commands
    ###################################################################################################################

    async def send_request_iso14a(self, request: str) -> str:
        """Send a raw ISO 14A request to a previously selected tag.

        Args:
            request (str): Request string.

        Returns:
            str: The tag response.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        responses = await self._send_command("AT+REQ14", request)
        # +REQ14: 0004040201000F03
        if len(responses) > 0:
            return responses[0][8:]
        return ""

    # Mifare Classic Commands
    ###################################################################################################################

    async def authenticate_mifare_classic_block(self, block: int, key: str | int = "", key_type: str = "") -> None:
        """Authenticate command for Mifare classic cards to access memory blocks.

        Prior to this command, the card has to be selected.

        Args:
            block (int): Block to authenticate.
            key (str): Mifare Key to authenticate with (6 bytes as Hex).
            key_type (str): Type of key. Either key 'A' or key 'B'.
            stored_key (int): Use a stored key instead of key and key type [0..16].

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()) and 0 <= int(key) <= 16:
            await self._send_command("AT+AUTN", block, key)
        else:
            await self._send_command("AT+AUT", block, str(key).upper(), key_type.upper())

    async def store_mifare_classic_authenticate_key(self, key_store: int, key: str, key_type: str):
        """Store an authenticate key in the reader.

        Args:
            key_store (int): The key store [0..16].
            key (str): Mifare Key to authenticate with (6 bytes as Hex).
            key_type (str): Type of key. Either key 'A' or key 'B'.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+SIK", key_store, key.upper(), key_type.upper())

    async def get_mifare_classic_access_bits(self, block: int) -> str:
        """Get the access bits for a given Mifare Classic block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number to read access bits of.

        Returns:
            access_bits: Access bits as string, like "001".

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        responses = await self._send_command("AT+GAB", block)
        access_bits = ""
        for response in responses:
            # +GAB: 000
            access_bits = response[6:]
        return access_bits

    async def set_mifare_classic_keys(self, block: int, key_A: str, key_B: str,
                                      access_bits: Optional[str] = None) -> None:
        # disable 'snake_case naming style' warning - pylint: disable=C0103
        """Set the keys and optionally the access bits for a given block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block to set keys and access bits for.
            key_A (str): Mifare KeyA.
            key_B (str): Mifare KeyB.
            access_bits (str): The Mifare access bits for the block.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        if access_bits:
            await self._send_command("AT+SKA", block, key_A, key_B, access_bits)
        else:
            await self._send_command("AT+SKO", block, key_A, key_B)

    async def write_mifare_classic_value_block(self, block: int, initial_value: int, backup_address: int) -> None:
        """Write/Create a mifare classic value block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number.
            initial_value (int): Initial value.
            backup_address (int): Address of the block used for backup.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+WVL", block, initial_value, backup_address)

    async def read_mifare_classic_value_block(self, block: int) -> tuple[int, int]:
        """Read a mifare classic value block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number.

        Returns:
            tuple[int, int]: The value and the address.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +RVL: 32,5
        values = (await self._send_command("AT+RVL", block))[0][6:].split(',')
        return int(values[0]), int(values[1])

    async def increment_mifare_classic_value(self, block: int, value: int) -> None:
        """Increment the value of a Mifare Classic block.

        Prior to this command, the card has to be selected and
        the block has to be authenticated.

        Args:
            block (int): Block number.
            value (int): Increment value.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+IVL", block, value)

    async def decrement_mifare_classic_value(self, block: int, value: int) -> None:
        """Decrement the value of a Mifare Classic block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number.
            value (int): Decrement value.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+DVL", block, value)

    async def restore_mifare_classic_value(self, block: int) -> None:
        """Restore the value of a Mifare Classic block.

        This will load the current value from the block.
        With the transfer method this value can be stored in a other block.
        Note that this operation only will have an effect after the
        transfer command is executed.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+RSVL", block)

    async def transfer_mifare_classic_value(self, block: int) -> None:
        """Write all pending transactions to a mifare classic block.

        Prior to this command, the card has to be selected
        and the block has to be authenticated.

        Args:
            block (int): Block number.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+TXF", block)

    # NTAG / Mifare Ultralight
    ###################################################################################################################

    # AT+NPAUTH
    # AT+NPWD
    async def authenticate_ntag(self, password: str, password_acknowledge: str = ""):
        """Authenticate command for NTAG / Mifare Ultralight cards.

        Prior to this command, the card has to be selected.
        After the authentication password protected pages can be accessed.
        Checks the password confirmation if it has been specified.

        Args:
            password (str): Password (hex).
            password_acknowledge (str): Password acknowledge (hex).

        Raises:
            RfidTransponderException: If the acknowledge is not correct
                or the transponder returns an error.
            RfidReaderException: If a reader error occurs.

        Returns:
            str: The password acknowledge.
        """
        # +NPAUTH: ABCD
        acknowledge = (await self._send_command("AT+NPAUTH", password))[0][9:]
        if password_acknowledge and password_acknowledge != acknowledge:
            raise RfidTransponderException("wrong acknowledge")
        return acknowledge

    async def set_authenticate_ntag(self, password: str, password_acknowledge: str = ""):
        """Set the password and the password acknowledge for NTAG / Mifare Ultralight cards.

        Prior to this command, the card has to be selected.

        Args:
            password (str): Password (hex).
            password_acknowledge (str): Password acknowledge (hex).

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NPWD", password, password_acknowledge)

    # AT+NACFG
    async def write_ntag_access_config(self, page_address: int, read_protect: bool, attempts: int) -> None:
        """Configure the NTAG access configuration.

        Prior to this command, the card has to be selected and authenticated.

        Args:
            page_address (int): Page address from which password
                authentication is required.
            read_protect (bool): Also protect reading.
            attempts (int): Number of authentication attempts.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NACFG", page_address, 1 if read_protect else 0, attempts)

    async def read_ntag_access_config(self) -> tuple[int, bool, int]:
        """Read the NTAG access configuration.

        Prior to this command, the card has to be selected and authenticated.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.

        Returns:
            tuple[int, bool, int]: (page_address, read_protect, attempts).
        """
        # +NACFG: 4,1,0
        values = (await self._send_command("AT+NACFG?"))[0][8:].split(',')
        return int(values[0]), values[1] != 0, int(values[2])

    # AT+NMCFG
    async def write_ntag_mirror_config(self, mirror_mode: NTagMirrorMode, mirror_page: int, mirror_byte: int) -> None:
        """Configure the NTAG mirror configuration.

        Prior to this command, the card has to be selected and authenticated.

        Args:
            mirror_mode (NTagMirrorMode): Mirror mode.
            mirror_page (int): The start page where the configured data
                is mirrored to. Range: 4 - (Last Page - 3).
            mirror_byte (int): Offset of the mirrored data in the
                Mirror Page [0..3].

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NMCFG", mirror_mode.name, mirror_page, mirror_byte)

    async def read_ntag_mirror_config(self) -> tuple[NTagMirrorMode, int, int]:
        """Read the NTAG mirror configuration.

        Prior to this command, the card has to be selected and authenticated.

        Returns:
            tuple[int, bool, int]: (mirror_mode, mirror_page, mirror_byte).

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +NMCFG: BOTH,4,0
        values = (await self._send_command("AT+NMCFG?"))[0][8:].split(',')
        return NTagMirrorMode[values[0]], int(values[1]), int(values[2])

    # AT+NCCFG
    async def write_ntag_counter_config(self, enable_counter: bool, enable_password: bool) -> None:
        """Configure the NTAG counter configuration.

        Prior to this command, the card has to be selected and authenticated.

        Args:
            enable_counter (bool): Set to True to enable the NFC counter.
            enable_password (bool): Set to True to enable password
                protection for the NFC counter.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NCCFG", 1 if enable_counter else 0, 1 if enable_password else 0)

    async def read_ntag_counter_config(self) -> tuple[bool, bool]:
        """Read the NTAG counter configuration.

        Prior to this command, the card has to be selected and authenticated.

        Returns:
            tuple[bool, bool]: (counter_enabled, password_enabled).

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +NCCFG: 1,0
        values = (await self._send_command("AT+NCCFG?"))[0][8:].split(',')
        return values[0] == "1", values[1] == "1"

    # AT+NDCFG
    async def write_ntag_modulation_config(self, use_strong_modulation: bool) -> None:
        """Configure the NTAG modulation configuration.

        Prior to this command, the card has to be selected and authenticated.

        Args:
            use_strong_modulation (bool): Set to True to use strong modulation.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NDCFG", 1 if use_strong_modulation else 0)

    async def read_ntag_modulation_config(self) -> bool:
        """Read the NTAG modulation configuration.

        Prior to this command, the card has to be selected and authenticated.

        Returns:
            strong_modulation_enabled (bool): Whether strong modulation is enabled.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +NDCFG: 1
        value: str = (await self._send_command("AT+NDCFG?"))[0][8:]
        return value == "1"

    # AT+NCLK
    async def lock_ntag_config(self) -> None:
        """Permanently lock the NTAG configuration.

        Prior to this command, the card has to be selected and authenticated.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NCLK")

    async def is_ntag_config_locked(self) -> bool:
        """Check if the NTAG configuration is locked.

        Prior to this command, the card has to be selected and authenticated.

        Returns:
            locked (bool): True if the configuration is locked.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +NCLK: 1
        value: str = (await self._send_command("AT+NCLK?"))[0][7:]
        return value == "1"

    # AT+NCNT
    async def read_ntag_counter(self) -> int:
        """Read the NTAG counter.

        Prior to this command, the card has to be selected and authenticated.

        Returns:
            value (int): The counter value.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        # +NCNT: 12
        value: str = (await self._send_command("AT+NCNT?"))[0][7:]
        return int(value)

    #  AT+NLK
    async def lock_ntag_page(self, page: int) -> None:
        """Lock a NTAG page.

        The lock is irreversible.
        Prior to this command, the card has to be selected and authenticated.

        Args:
            page (int): The page to lock [3..15].

        Returns:
            value (int): The counter value.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NLK", page)

    # AT+NBLK
    async def lock_ntag_block_lock(self, page_number: int) -> None:
        """Set the NTAG block-lock-bits.

        The block-lock bits are used to lock the lock bits.
        Refer to the NTAG data sheet for details.
        Prior to this command, the card has to be selected and authenticated.

        Args:
            page_number (int): The page number to lock the lock bits for.

        Returns:
            value (int): The counter value.

        Raises:
            RfidTransponderException: If the transponder returns an error.
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+NBLK", page_number)

    # Mifare Desfire Command
    ###################################################################################################################

    # async def desfire_list_applications(self):
    #     """List all applications on a Mifare Desfire Card. The card has to be selected first.

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #     """
    #     responses = await self._send_command("AT+DFLSA")
    #     # +DFLSA: 5f8405
    #     # +DFLSA: 5f8415
    #     # +DFLSA: 5f8425
    #     applications = []
    #     for response in responses:
    #         applications.append(response[8:])
    #     return applications

    # async def desfire_select_application(self, application_id: str):
    #     """_summary_

    #     Args:
    #         id (str): The ID of the application to select (3 byte ASCII encoded hex)

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #     """
    #     await self._send_command("AT+DFSEL", application_id)

    # async def desfire_list_files(self):
    #     """List all files of a selected Mifare Desfire application. The card has to be selected first.

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #     """
    #     responses = await self._send_command("AT+DFLSF")
    #     # +DFLSF: 0
    #     # +DFLSF: 1
    #     # +DFLSF: 2
    #     files = []
    #     for response in responses:
    #         files.append(int(response[8:]))
    #     return files

    # async def set_desfire_file_settings(self, file_id: int, is_primary: bool):
    #     """_summary_

    #     Args:
    #         id (str): The file ID of the file to get settings from
    #         is_primary (bool): Set true for primary applications, false for secondary applications.

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #             """
    #     await self._send_command("AT+DFGFS", file_id, 1 if is_primary else 0)

    # async def get_desfire_value(self, file_id: int, is_primary: bool, communication_mode: CommMode):
    #     """Read the value of a Mifare Desfire value file

    #      Args:
    #         id (str): The file ID of the file to get the value from
    #         is_primary (bool): Set true for primary applications, false for secondary applications.
    #         communication_mode (CommMode): Communication mode with the card

    #     Raises:
    #         RfidReaderException: if an reader error occurs
    #     """
    #     responses = await self._send_command("AT+DFGV", file_id, 1 if is_primary else 0, communication_mode.name)
    #     #  +DFGV: 7560
    #     return responses[0][7:]

    ###################################################################################################################
    # ADDITIONAL DEVICE FEATURES                                                                                      #
    ###################################################################################################################

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

    # @override
    async def stop_inventory(self) -> None:
        try:
            await self._send_command('AT+BINV')
        except RfidReaderException as err:
            if "is not running" in str(err):
                return
            if "Not expected response" in str(err):
                while True:
                    resp = await self._recv()
                    if resp is None:
                        break
                    if resp in {'OK', 'ERROR'}:
                        break
                return
            raise err

    # HID Mode
    ###################################################################################################################

    async def disable_hid_mode(self) -> None:
        """Disable the readers HID mode.

        Note: This function will reboot the reader.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+HID", "OFF")
        await self._reconnect(3)

    async def set_hid_mode(self, mode: str, start: int, length: int,
                           eol: Optional[str] = None, oof: int = 5000) -> None:
        """Enable and configure the readers HID mode.

        NFC readers with a native USB support a HID mode where the Tag UID
        or memory content is outputted as keyboard keystrokes.

        Use the `disable_hid_mode()` function to disable HID mode.

        Note: This function will reboot the reader.

        Args:
            mode (str): Whether to use the tags UID (`"UID"`) or memory
                data (`"MEM"`) to determine the keystrokes.

            start (int): In UID mode the start byte of the UID.
                In MEM mode the memory block to use.

            length (int): The maximum number of bytes to print from the
                UID or block.

            eol (str, optional): This character will be appended to each
                output. Must be one of `["NONE", "RETURN", "TAB"]`.

            oof (int, optional): A tag needs to be out of field for at
                least this many milliseconds before it is outputted again.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        # disable 'Too many (positional) arguments' warning - pylint: disable=R0913,R0917
        # check mode argument
        mode_arg = str(mode).upper()
        mode_allowed = ["UID", "MEM"]
        if mode_arg not in mode_allowed:
            raise RfidReaderException(f"Mode argument must be one of {mode_allowed}")

        # check eol argument
        eol_arg = str(eol).upper()
        eol_allowed = ["NONE", "RETURN", "TAB"]
        if eol_arg not in eol_allowed:
            raise RfidReaderException(f"EOL argument must be one of {eol_allowed}")

        # send command
        await self._send_command("AT+HID", mode_arg, start, length, eol_arg, oof)

        # reader will reboot so re-connect after a short delay
        await self._reconnect(3)

    async def get_hid_mode(self) -> Dict[str, Any]:
        """Get the current HID mode settings.

        See `set_hit_mode()` for parameter explanation.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            dict: Dictionary with keys 'mode', "start", "length",
            'eol' and 'oof'.
        """
        responses: List[str] = await self._send_command("AT+HID?")

        # +HID: OFF,0,0,NONE,0
        data: List[str] = responses[0][6:].split(',')
        try:
            config: Dict[str, Any] = {
                "mode": data[0],
                "start": data[1],
                "length": data[2],
                "eol": data[3],
                "oof": data[4]
            }
            return config
        except IndexError as e:
            raise RfidReaderException(
               f"Not expected response for command AT+HID? - {responses}") from e

    async def set_hid_layout(self, layout: str) -> None:
        """Configure the keyboard layout used for HID mode.

        Args:
            layout (str): The keyboard layout string, "EN" or "FR".

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+HIDKBD", layout)

    async def get_hid_layout(self) -> str:
        """Get the current HID keyboard layout setting.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            str: The keyboard layout string, e.g. "EN" or "FR".
        """
        responses: List[str] = await self._send_command("AT+HIDKBD?")
        # +HIDKBD: EN
        data: str = responses[0][9:]
        return data

    # NDEF Functions
    ###################################################################################################################

    # AT+CHKNDEF
    async def check_ndef_state(self) -> NdefState:
        """Check the NDEF data state of a transponder.

        Prior to this command, the card has to be selected.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            NdefState: The NDEF state of the tag.
        """
        # send command
        responses: List[str] = await self._send_command("AT+CHKNDEF")
        # check response
        # +CHKNDEF: NO NDEF
        try:
            data: str = responses[0][10:]
            return NdefState[data.replace(" ", "_")]
        except (IndexError, KeyError) as e:
            raise RfidReaderException("Not expected response for command"
                                      f"AT+CHKNDEF - {responses}") from e

    # AT+RDNDEF
    async def read_ndef_records(self) -> str:
        """Read all NDEF records from a transponder.

        Prior to this command, the card has to be selected.

        Raises:
            RfidReaderException: If a reader error occurs.

        Returns:
            str: The NDEF records as hex string.
        """
        responses: List[str] = await self._send_command("AT+RDNDEF")
        records = "".join(response[9:] for response in responses)
        return records

    # AT+WRTNDEF
    async def write_ndef_records(self, records: str) -> None:
        """Write NDEF records to a transponder.

        Prior to this command, the card has to be selected.

        Args:
            records (str): The NDEF records as hex string.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+WRTNDEF", records)

    # AT+FMTNDEF
    async def format_ndef_tag(self) -> None:
        """Format a tag for NDEF usage.

        Prior to this command, the card has to be selected.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+FMTNDEF")

    # AT+SRONDEF
    async def lock_ndef_tag(self) -> None:
        """Make the NDEF data on a tag read-only.

        Prior to this command, the card has to be selected.

        Raises:
            RfidReaderException: If a reader error occurs.
        """
        await self._send_command("AT+SRONDEF")

    ###############################################################################################
    # Internal methods
    ###############################################################################################

    # @override
    async def _config_reader(self) -> None:
        await super()._config_reader()
        self._mode = await self.get_mode()
        setting = await self.get_inventory_settings()
        if not setting['enable_tag_details']:
            setting['enable_tag_details'] = True
            await self.set_inventory_settings(True, setting['only_new_tags'], setting['single_slot'])

    def _handle_inventory_events(self, msg: str, timestamp: float) -> None:
        try:
            # '+CINV: '
            self._fire_inventory_event(self._parse_inventory(
                msg.split("\r"), timestamp, 7))  # type: ignore
        except RfidReaderException as err:
            if self._status['status'] == RfidReader.WARNING and "antenna error" in self.get_status()['message'].lower():
                # error is already set
                return
            self._update_status(RfidReader.WARNING, str(err))

    def _parse_inventory(self, responses: List[str], timestamp: float, split_index: int = 6) -> List[HfTag]:
        # disable 'Too many branches' warning - pylint: disable=R0912
        # disable 'Too many statements' warning - pylint: disable=R0915

        # +CINV: E002223504422958 +CINV=<ROUND FINISHED>
        # +INV: E002223504422958
        inventory: List[HfTag] = []
        antenna: Optional[int] = None
        error: Optional[str] = None
        tag_details_enabled = bool(self._config['inventory']['enable_tag_details'])
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
                    print(
                        f"error: {response[split_index+1:-1]} - {self._ignore_errors}")
                    error = response[split_index+1:-1]
                continue
            info: List[str] = response[split_index:].split(',')
            try:
                new_tag = None
                if not tag_details_enabled:
                    tag_type = self._mode
                    if tag_type == NfcMode.AUTO:
                        new_tag = HfTag(info[0], timestamp)
                    elif tag_type == NfcMode.ISO15:
                        new_tag = ISO15Tag(info[0], timestamp)
                    elif tag_type == NfcMode.ISO14A:
                        new_tag = ISO14ATag(info[0], timestamp)
                else:
                    tag_type = self._mode
                    if tag_type == NfcMode.AUTO:
                        tag_type = NfcMode[info.pop(1)]
                    if tag_type == NfcMode.ISO15:
                        new_tag = ISO15Tag(info[0], timestamp, dsfid=info[1])
                    elif tag_type == NfcMode.ISO14A:
                        new_tag = ISO14ATag(info[0], timestamp, sak=info[1], atqa=info[2])
                if new_tag is not None:  # null check
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
            raise RfidReaderException(
                f"{error}{f' - Antenna {antenna} ' if antenna else ''}")
        if antenna:
            for tag in inventory:
                tag.set_antenna(antenna)
        return inventory

    def _parse_error_response(self, response: str) -> RfidReaderException:
        """analyse the reader error and return the resulting exception

        Args:
            response (str): error response

        Returns:
            RfidReaderException: resulting exception
        """
        transponder_error = [
            "No Tag selected",  # NFC_CORE_ERROR_NOT_SELECTED:
            "Wrong Tag type",  # NFC_CORE_ERROR_TAG_TYPE:
            "Unexpected Tag response",  # NFC_CORE_ERROR_UNEXPECTED_RESPONSE:
            "Block out of range",  # NFC_CORE_ERROR_BLOCK_RANGE:
            "Not authenticated",  # NFC_CORE_ERROR_NOT_AUTHENTICATED:
            "Access prohibited",  # NFC_CORE_ERROR_ACCESS_PROHIBITED:
            "Wrong block size",  # NFC_CORE_ERROR_BLOCK_SIZE:
            "Tag timeout",  # NFC_CORE_ERROR_IO_TIMEOUT:
            "Collision error",  # NFC_CORE_ERROR_COLLISION:
            "Overflow",  # NFC_CORE_ERROR_OVERFLOW:
            "Parity error",  # NFC_CORE_ERROR_PARITY:
            "Framing error",  # NFC_CORE_ERROR_FRAMING:
            "Protocol violation",  # NFC_CORE_ERROR_PROTOCOL_VIOLATION:
            "Authentication failure",  # NFC_CORE_ERROR_AUTHENTICATION:
            "Length error",  # NFC_CORE_ERROR_LENGTH:
            "Received NAK",  # NFC_CORE_ERROR_NAK:
            "NTAG invalid argument",  # NFC_CORE_ERROR_NTAG_INVALID_ARG:
            "NTAG parity/crc error",  # NFC_CORE_ERROR_NTAG_PARITY:
            "NTAG auth limit reached",  # NFC_CORE_ERROR_NTAG_AUTH_LIMIT:
            "NTAG EEPROM failure (maybe locked?)",  # NFC_CORE_ERROR_NTAG_EEPROM:
            "Mifare NAK 0",  # NFC_CORE_ERROR_MIFARE_NAK0:
            "Mifare NAK 1",  # NFC_CORE_ERROR_MIFARE_NAK1:
            "Mifare NAK 3",  # NFC_CORE_ERROR_MIFARE_NAK3:
            "Mifare NAK 4",  # NFC_CORE_ERROR_MIFARE_NAK4:
            "Mifare NAK 5",  # NFC_CORE_ERROR_MIFARE_NAK5:
            "Mifare NAK 6",  # NFC_CORE_ERROR_MIFARE_NAK6:
            "Mifare NAK 7",  # NFC_CORE_ERROR_MIFARE_NAK7:
            "Mifare NAK 8",  # NFC_CORE_ERROR_MIFARE_NAK8:
            "Mifare NAK 9",  # NFC_CORE_ERROR_MIFARE_NAK9:
            "ISO15 custom command error",  # NFC_CORE_ERROR_ISO15_CUSTOM_CMD_ERR:
            "ISO15 command not supported",  # NFC_CORE_ERROR_ISO15_CMD_NOT_SUPPORTED:
            "ISO15 command not recognized",  # NFC_CORE_ERROR_ISO15_CMD_NOT_RECOGNIZED:
            "ISO15 option not supported",  # NFC_CORE_ERROR_ISO15_OPT_NOT_SUPPORTED:
            "ISO15 no information",  # NFC_CORE_ERROR_ISO15_NO_INFO:
            "ISO15 block not available",  # NFC_CORE_ERROR_ISO15_BLOCK_NOT_AVAIL:
            "ISO15 block locked",  # NFC_CORE_ERROR_ISO15_BLOCK_LOCKED:
            "ISO15 content change failure",  # NFC_CORE_ERROR_ISO15_CONTENT_CHANGE_FAIL:
            "ISO15 block programming failure",  # NFC_CORE_ERROR_ISO15_BLOCK_PROGRAMMING_FAIL:
            "ISO15 block protected",  # NFC_CORE_ERROR_ISO15_BLOCK_PROTECTED:
            "ISO15 cryptographic error",  # NFC_CORE_ERROR_ISO15_CRYPTO:
        ]

        # reader_error = [
        #     "No such protocol",  # NFC_CORE_ERROR_NO_SUCH_PROTO:
        #     "No frontend selected",  # NFC_CORE_ERROR_NO_FRONTEND:
        #     "Failed to initialize frontend",  # NFC_CORE_ERROR_FRONTEND_INIT:
        #     "Wrong operation mode",  # NFC_CORE_ERROR_OP_MODE:
        #     "Invalid parameter",  # NFC_CORE_ERROR_INVALID_PARAM:
        #     "Command failed",  # NFC_CORE_ERROR_COMMAND_FAILED:
        #     "IO error",  # NFC_CORE_ERROR_IO:
        #     "Timeout",  # NFC_CORE_ERROR_TIMEOUT:
        #     "Temperature error",  # NFC_CORE_ERROR_TEMPERATURE:
        #     "Resource error",  # NFC_CORE_ERROR_RESOURCE:
        #     "RF error",  # NFC_CORE_ERROR_RF:
        #     "Noise error",  # NFC_CORE_ERROR_NOISE:
        #     "Aborted",  # NFC_CORE_ERROR_ABORTED:
        #     "Authentication delay",  # NFC_CORE_ERROR_AUTH_DELAY:
        #     "Unsupported parameter",  # NFC_CORE_ERROR_UNSUPPORTED_PARAM:
        #     "Unsupported command",  # NFC_CORE_ERROR_UNSUPPORTED_CMD:
        #     "Wrong use condition",  # NFC_CORE_ERROR_USE_CONDITION:
        #     "Key error",  # NFC_CORE_ERROR_KEY:
        #     "No key at given index",  # NFC_CORE_ERROR_KEYSTORE_NO_KEY:
        #     "Could not save key",  # NFC_CORE_ERROR_KEYSTORE_SAVE_ERROR:
        #     "Feedback out of range",  # NFC_CORE_ERROR_FEEDBACK_OUT_OF_RANGE:
        #     "Invalid feedback string",  # NFC_CORE_ERROR_FEEDBACK_PARSING_ERROR:
        #     "Feedback already running",  # NFC_CORE_ERROR_FEEDBACK_ALREADY_RUNNING:
        #     "Unknown Error",  # NFC_CORE_ERROR_UNKNOWN:
        # ]
        if response in transponder_error:
            return RfidTransponderException(response)
        return RfidReaderException(response)

    async def _reconnect(self, delay_s):
        """Disconnect the reader and re-connect after specified delay.
        """
        # disconnect
        try:
            await self.disconnect()
        except RfidReaderException as e:
            self.get_logger().error(e)

        # wait for specified period of time
        await asyncio.sleep(delay_s)

        # re-connect
        await self.connect()

    # @override
    async def _prepare_reader_communication(self) -> None:
        """The method of the ReaderAT superclass uses a `stop_inventory`
        function which is not available when HID mode is active.
        This raises an error which will cause any `connect` to fail.
        Therefore we catch and ignore the error here.
        """
        try:
            await super()._prepare_reader_communication()
        except RfidReaderException as err:
            if "HID mode active" not in str(err):
                raise err
