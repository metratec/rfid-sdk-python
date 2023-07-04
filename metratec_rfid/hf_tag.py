"""UHF Transponder defines
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
        self.set_tid(tid)
        self.set_timestamp(timestamp)
        self.set_antenna(antenna)
        self.set_seen_count(seen_count)

    def get_id(self) -> str:
        identifier: Optional[str] = self.get_tid()
        return identifier if identifier else "unknown"
