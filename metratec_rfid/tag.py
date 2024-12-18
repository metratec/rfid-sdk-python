"""
metratec rfid tag base class
"""
from abc import abstractmethod
from typing import Any, Optional


class Tag(dict):
    """Transponder class
    """

    def __init__(self, tid: Optional[str], timestamp: Optional[float] = None) -> None:
        dict.__init__(self)
        if tid:
            self.set_tid(tid)
        if timestamp:
            self.set_first_seen(timestamp)
            self.set_last_seen(timestamp)

    @abstractmethod
    def get_id(self) -> str:
        """ return the tag identifier"""

    def get_tid(self) -> str:
        """Return the tag ID (TID) of this transponder.

        Returns:
            str: The TID of the tag.
        """
        return self.get('tid', '')

    def set_tid(self, tid: str) -> None:
        """Set the tag ID (TID) value of this transponder.

        Args:
            tid (str): The TID value to set.
        """
        self.set_value('tid', tid)

    def get_timestamp(self) -> float:
        """Return the timestamp value of this tag.

        DEPRECATED

        Returns:
            float: Unix timestamp in seconds.
        """
        return self.get_last_seen()

    def set_timestamp(self, timestamp: float) -> None:
        """Set the timestamp value of this tag.

        DEPRECATED

        Args:
            timestamp (float): The (unix) timestamp value to set.
        """
        self.set_last_seen(timestamp)

    def get_first_seen(self) -> float:
        """Return the first seen timestamp of this tag.

        The first time this tag was encountered in the current inventory.

        Returns:
            float: Unix timestamp in seconds.
        """
        return self.get('first_seen', 0)

    def set_first_seen(self, timestamp: float) -> None:
        """Set the first seen timestamp value of this tag.

        Args:
            timestamp (float): The (unix) timestamp to set.
        """
        # Set the new value.
        self.set_value('first_seen', timestamp)

    def get_last_seen(self) -> float:
        """Return the last seen timestamp of this tag.

        During a continuous inventory operation, this value will be
        updated to the last time this tag was encountered.

        Returns:
            float: Unix timestamp in seconds.
        """
        return self.get('last_seen', 0)

    def set_last_seen(self, timestamp: float) -> None:
        """Set the last seen timestamp value of this tag.

        Args:
            timestamp (float): The (unix) timestamp to set.
        """
        # Set the new value.
        self.set_value('last_seen', timestamp)

    def get_data(self) -> str:
        """Return the user data of this tag.

        Returns:
            str: The user data.
        """
        return self.get('data', '')

    def set_data(self, data: str) -> None:
        """Set the data value of this tag.

        Args:
            data (str): The data value to set.
        """
        self.set_value('data', data)

    def get_antenna(self) -> int:
        """Return the antenna that inventoried this tag.

        Returns:
            int: The antenna index or -1 if not available.
        """
        return self.get('antenna', -1)

    def set_antenna(self, antenna: int) -> None:
        """Set the antenna value of this tag.

        Args:
            antenna (int): The antenna value to set.
        """
        self.set_value('antenna', antenna)

    def get_seen_count(self) -> int:
        """Return the seen count of this tag.

        During a continuous inventory operation, this value will be
        incremented every time the tag was encountered.

        Returns:
            int: The number of times this tag was found.
        """
        count = self.get('seen_count')
        return count if count else 0

    def set_seen_count(self, seen_count: int) -> None:
        """Set the seen count value of this tag.

        Args:
            seen_count (int): The seen count value to set.
        """
        self.set_value('seen_count', seen_count)

    def has_error(self) -> bool:
        """Return whether this tag encountered an error.

        Get the corresponding error message with `get_error_message()`.

        Returns:
            bool: True if the tag has an error message.
        """
        return self.get('has_error', False)

    def get_error_message(self) -> str:
        """Return the error message of this tag.

        Returns:
            str: The error message.
        """
        return self.get('error_message', '')

    def set_error_message(self, message: str) -> None:
        """Set the error message value of this tag.

        Args:
            message (str): The error message to set.
        """
        self.set_value('error_message', message)
        self.set_value('has_error', bool(message))

    def set_value(self, key: str, value: Any) -> None:
        """Set a dictionary value.

        Args:
            key (str): The dictionary key.
            value (Any): The value to set or None to delete the item.
        """
        if value is not None:
            self[key] = value
        elif key in self:
            del self[key]
