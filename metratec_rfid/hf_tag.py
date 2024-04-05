"""HF Transponder defines
"""
from typing import Optional

from .tag import Tag


class HfTag(Tag):
    """
    HF Transponder class
    """
    # disable 'Too many public methods' warning - pylint: disable=R0904

    def __init__(
            self, tid: str, timestamp: Optional[float] = None,
            antenna: Optional[int] = None, seen_count: int = 1) -> None:

        # disable 'Too many arguments' warning - pylint: disable=R0913

        super().__init__(tid, timestamp)
        if antenna:
            self.set_antenna(antenna)
        self.set_seen_count(seen_count)

    def get_id(self) -> str:
        identifier: Optional[str] = self.get_tid()
        return identifier if identifier else "unknown"

    def get_tid(self) -> str:
        """Return the tid

        Returns:
            str: the tid
        """
        return self.get('tid', "")

    def set_type(self, tag_type: str):
        """Sets the transponder type

        Args:
            type (str): the transponder type
        """
        self.set_value("type", tag_type)

    def get_type(self) -> str:
        """The transponder type if set

        Returns:
            str: the transponder type
        """
        return self.get('type', '')


class ISO15Tag(HfTag):
    """
    ISO15 Transponder class
    """

    def __init__(self, tid: str, timestamp: float | None = None, antenna: int | None = None,
                 seen_count: int = 1, dsfid: str | None = None) -> None:
        # disable 'Too many arguments' warning - pylint: disable=R0913
        super().__init__(tid, timestamp, antenna, seen_count)
        self.set_type("ISO15")
        if dsfid:
            self.set_dsfid(dsfid)

    def get_dsfid(self) -> str:
        """Return the dsfid byte as hex

        Returns:
            str: the dsfid byte as hex
        """
        return self.get('dsfid', '')

    def set_dsfid(self, dsfid: str) -> None:
        """Set the dsfid byte as hex

        Args:
            dsfid (str): the dsfid byte as hex
        """
        self.set_value('dsfid', dsfid)


class ISO14ATag(HfTag):
    """
    ISO14A Transponder class
    """

    def __init__(self, tid: str, timestamp: float | None = None, antenna: int | None = None,
                 seen_count: int = 1, sak: str | None = None, atqa: str | None = None,
                 tag_type: str | None = None) -> None:
        # disable 'Too many arguments' warning - pylint: disable=R0913
        super().__init__(tid, timestamp, antenna, seen_count)
        self.set_type(tag_type if tag_type else "ISO14A")
        if sak:
            self.set_sak(sak)
        if atqa:
            self.set_atqa(atqa)

    def get_sak(self) -> str:
        """Return the sak byte as hex

        Returns:
            str: the sak byte as hex
        """
        return self.get('sak', '')

    def set_sak(self, sak: str) -> None:
        """Set the sak byte as hex

        Args:
            sak (str): the dsfid byte as hex
        """
        self.set_value('sak', sak)

    def get_atqa(self) -> str:
        """Return the atqa bytes as hex

        Returns:
            str: the atqa bytes as hex
        """
        return self.get('atqa', '')

    def set_atqa(self, atqa: str) -> None:
        """Set the atqa bytes as hex

        Args:
            atqa (str): the atqa bytes as hex
        """
        self.set_value('atqa', atqa)


class HfTagInfo(HfTag):
    """
    HF Transponder Info class
    """

    def __init__(self, tid: str, tag_info: Optional[str], error_message: Optional[str],
                 timestamp: Optional[float] = None, antenna: Optional[int] = None, seen_count: int = 1) -> None:
        # disable 'Too many arguments' warning - pylint: disable=R0913
        super().__init__(tid, timestamp, antenna, seen_count)
        if error_message:
            self.set_error_message(error_message)
        if tag_info:
            info_flag = int(tag_info[0:2], 16)
            self.set_value('is_dsfid', (bool)(info_flag & 0x01))
            if self.is_dsfid():
                self.set_value('dsfid', int(tag_info[16:18], 16))
            self.set_value('is_afi', (bool)(info_flag & 0x02))
            if self.is_afi():
                self.set_value('afi', int(tag_info[18:20], 16))
            self.set_value('is_vicc', (bool)(info_flag & 0x04))
            if self.is_vicc():
                self.set_value('vicc_number_of_block', int(tag_info[20:22], 16) + 1)
                self.set_value('vicc_block_size', (int(tag_info[22:24], 16) & 0x3F) + 1)
            self.set_value('is_icr', (bool)(info_flag & 0x08))
            if self.is_icr():
                self.set_value('icr', int(tag_info[24:26], 16))

    def is_dsfid(self) -> bool:
        """Return if the DSFID field is supported by this transponder

        Returns:
            bool: if True, the DSFID field is present
        """
        return self.get('is_dsfid', False)

    def get_dsfid(self) -> int:
        """Returns the Data storage format identifier (DSFID) if present

        Returns:
            int: the DSFID of this transponder
        """
        return self.get('dsfid', None)

    def is_afi(self) -> bool:
        """Return if the AFI field is supported by this transponder

        Returns:
            bool: if True, the AFI field is present
        """
        return self.get('is_afi', False)

    def get_afi(self) -> int:
        """Returns the Application family identifier (API) if present

        Returns:
            int: the API of this transponder
        """
        return self.get('afi', None)

    def is_vicc(self) -> bool:
        """Return if the VICC memory information is supported by this transponder

        Returns:
            bool: if True, the VICC memory information is present
        """
        return self.get('is_vicc', False)

    def get_vicc_number_of_block(self) -> int:
        """Returns the number of available memory block for this transponder

        Returns:
            int: the number of memory blocks
        """
        return self.get('vicc_number_of_block', None)

    def get_vicc_block_size(self) -> int:
        """Returns the memory block size for this transponder

        Returns:
            int: the memory block size
        """
        return self.get('vicc_block_size', 0)

    def is_icr(self) -> bool:
        """Return if the IC reference is supported by this transponder

        Returns:
            bool: if True, the IC reference is present
        """
        return self.get('is_icr', False)

    def get_icr(self) -> int:
        """Returns the IC reference for this transponder

        Returns:
            int: the IC reference
        """
        return self.get('icr', None)


class HfTagMemory(dict):
    """Tag Memory information
    """

    def __init__(self, sectors: int, number_of_blocks: int, block_size: int) -> None:
        dict.__init__(self)
        self['sectors'] = sectors
        self['number_of_blocks'] = number_of_blocks
        self['block_size'] = block_size

    def get_sectors(self) -> int:
        """
        Returns:
            int: adjacent same-sized sectors
        """
        return self['sectors']

    def get_number_of_blocks(self) -> int:
        """
        Returns:
            int: the number of blocks
        """
        return self['number_of_blocks']

    def get_block_size(self) -> int:
        """
        Returns:
            int: the tag block size
        """
        return self['block_size']
