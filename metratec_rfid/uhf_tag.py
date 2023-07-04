"""UHF Transponder defines
"""
from typing import Optional

from .tag import Tag


class UhfTag(Tag):
    """UHF Transponder class
    """
    # disable 'Too many public methods' warning - pylint: disable=R0904

    def __init__(
            self, epc: str, timestamp: Optional[float] = None,
            tid: Optional[str] = None, antenna: Optional[int] = None,
            seen_count: int = 1, rssi: Optional[int] = None) -> None:

        # disable 'Too many arguments' warning - pylint: disable=R0913

        super().__init__(tid, timestamp)
        self.set_epc(epc)
        self.set_timestamp(timestamp)
        self.set_rssi(rssi)
        self.set_tid(tid)
        self.set_antenna(antenna)
        self.set_seen_count(seen_count)

    def get_id(self) -> str:
        identifier: Optional[str] = self.get_epc()
        return identifier if identifier else "unknown"

    def get_epc(self) -> Optional[str]:
        """Return the epc

        Returns:
            str: the epc
        """
        return self.get('epc')

    def set_epc(self, epc: str) -> None:
        """Set the epc

        Args:
            epc (str): the epc to set
        """
        self.set_value('epc', epc)

    def get_rssi(self) -> Optional[int]:
        """Return the rssi

        Returns:
            int: the rssi
        """
        return self.get('rssi')

    def set_rssi(self, rssi: Optional[int]) -> None:
        """Set the rssi

        Args:
            rssi (int): the rssi to set
        """
        self.set_value('rssi', rssi)
