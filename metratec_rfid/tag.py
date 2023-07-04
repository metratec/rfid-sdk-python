"""
metratec rfid tag base class
"""
from abc import abstractmethod
from typing import Any, Optional


class Tag(dict):
    """Transponder class
    """

    def __init__(self, tid: Optional[str], timestamp:  Optional[float] = None) -> None:
        dict.__init__(self)
        self.set_tid(tid)
        self.set_timestamp(timestamp)

    @abstractmethod
    def get_id(self) -> str:
        """ return the tag identifier"""

    def get_tid(self) -> Optional[str]:
        """Return the tid

        Returns:
            str: the tid
        """
        return self.get('tid')

    def set_tid(self, tid: Optional[str]) -> None:
        """Set the tid

        Args:
            tid (str): the tid to set
        """
        self.set_value('tid', tid)

    def get_timestamp(self) -> Optional[float]:
        """Return the timestamp

        Returns:
            float: the timestamp
        """
        return self.get('timestamp')

    def set_timestamp(self, timestamp: Optional[float]) -> None:
        """Set the timestamp

        Args:
            timestamp (float): the timestamp to set
        """
        self.set_value('timestamp', timestamp)

    def get_first_seen(self) -> Optional[float]:
        """Return the first seen timestamp

        Returns:
            float: the first seen timestamp
        """
        return self.get('first_seen')

    def set_first_seen(self, timestamp: Optional[float]) -> None:
        """Set the first seen timestamp

        Args:
            timestamp (float): the first seen timestamp to set
        """
        self.set_value('first_seen', timestamp)

    def get_last_seen(self) -> Optional[float]:
        """Return the last seen timestamp

        Returns:
            float: the last seen timestamp
        """
        return self.get('last_seen')

    def set_last_seen(self, timestamp: Optional[float]) -> None:
        """Set the last seen timestamp

        Args:
            timestamp (float): the last seen timestamp to set
        """
        self.set_value('last_seen', timestamp)

    def get_data(self) -> Optional[str]:
        """Return the user data

        Returns:
            str: the user data
        """
        return self.get('data')

    def set_data(self, data: Optional[str]) -> None:
        """Set the data

        Args:
            data (str): the data to set
        """
        self.set_value('data', data)

    def get_antenna(self) -> Optional[int]:
        """Return the antenna

        Returns:
            int: the antenna
        """
        return self.get('antenna')

    def set_antenna(self, antenna: Optional[int]) -> None:
        """Set the antenna

        Args:
            antenna (int): the antenna to set
        """
        self.set_value('antenna', antenna)

    def get_seen_count(self) -> int:
        """Return the seen count

        Returns:
            int: the seen count
        """
        count = self.get('seen_count')
        return count if count else 0

    def set_seen_count(self, seen_count: Optional[int]) -> None:
        """Set the seen count

        Args:
            seen_count (int): the seen count to set
        """
        self.set_value('seen_count', seen_count)

    def has_error(self) -> bool:
        """Return true if the tag has a error message

        Returns:
            bool: true if the tag has a error message
        """
        return self.get('has_error', False)

    def get_error_message(self) -> Optional[str]:
        """Return the error message

        Returns:
            str: the error message
        """
        return self.get('error_message')

    def set_error_message(self, message: Optional[str]) -> None:
        """Set the error message

        Args:
            message (str): the error message to set
        """
        self.set_value('error_message', message)
        self.set_value('has_error', bool(message))

    def set_value(self, key: str, value: Any) -> None:
        """Set a dictionary value

        Args:
            key (str): the key
            value (Any): the value to set
        """
        if value is not None:
            self[key] = value
        elif key in self:
            del self[key]
