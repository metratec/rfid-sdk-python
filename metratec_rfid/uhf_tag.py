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

        # disable 'Too many (positional) arguments' warning - pylint: disable=R0913,R0917

        super().__init__(tid, timestamp)
        self.set_epc(epc)
        if rssi:
            self.set_rssi(rssi)
        if antenna:
            self.set_antenna(antenna)
        if seen_count:
            self.set_seen_count(seen_count)

    def get_id(self) -> str:
        """Return the identifier of this tag.

        Returns:
            str: The EPC value or "unknown" if not available.
        """
        identifier: Optional[str] = self.get_epc()
        return identifier if identifier else "unknown"

    def get_epc(self) -> Optional[str]:
        """Return the EPC value of this tag.

        Returns:
            str: The EPC value.
        """
        return self.get('epc')

    def set_epc(self, epc: str) -> None:
        """Set the EPC value of this tag.

        Args:
            epc (str): The EPC value to set.
        """
        self.set_value('epc', epc)

    def get_rssi(self) -> int:
        """Return the RSSI value of the transaction.

        Returns:
            int: The RSSI value in dBm or 0 if not available.
        """
        return self.get('rssi', 0)

    def set_rssi(self, rssi: int) -> None:
        """Set the RSSI value of this tag.

        Args:
            rssi (int): The RSSI value to set.
        """
        self.set_value('rssi', rssi)

    def get_phase(self) -> list[int]:
        """Return the phase measurement of the singulation.

        Returns:
            list[int]: The phase values or [] if not available.
        """
        return self.get('phase', [])

    def set_phase(self, phase: list[int]) -> None:
        """Set the phase value of this tag.

        Args:
            phase (List[int]): The phase value to set.
        """
        self.set_value('phase', phase)
