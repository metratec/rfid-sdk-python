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
        if rssi:
            self.set_rssi(rssi)
        if antenna:
            self.set_antenna(antenna)
        if seen_count:
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

    def get_rssi(self) -> int:
        """Return the rssi

        Returns:
            int: the rssi
        """
        return self.get('rssi', 0)

    def set_rssi(self, rssi: int) -> None:
        """Set the rssi

        Args:
            rssi (int): the rssi to set
        """
        self.set_value('rssi', rssi)

    def get_phase(self) -> list[int]:
        """Return the phase

        Returns:
            list[int]: the phase
        """
        return self.get('phase', [])

    def set_phase(self, phase: list[int]) -> None:
        """Set the phase1

        Args:
            phase1 (int): the phase1 to set
        """
        self.set_value('phase', phase)
