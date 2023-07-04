""" connection base class """

from abc import abstractmethod
from typing import Callable, Optional


class Connection():
    """Default connection
    """

    def __init__(self) -> None:
        self._cb_connection_made: Optional[Callable[[], None]] = None
        self._cb_connection_lost: Optional[Callable[[str], None]] = None
        self._cb_data_received: Optional[Callable[[bytes], None]] = None

    def set_cb_connection_made(self, callback: Optional[Callable]) -> Optional[Callable]:
        """
        Set the callback for connection made. The callback has no arguments.

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_connection_made
        self._cb_connection_made = callback
        return old

    def set_cb_connection_lost(self, callback: Optional[Callable]) -> Optional[Callable]:
        """
        Set the callback for connection lost. The callback has the following arguments:
        * reason - the lost reason

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_connection_lost
        self._cb_connection_lost = callback
        return old

    def set_cb_data_received(self, callback: Optional[Callable]) -> Optional[Callable]:
        """
        Set the callback if data is received. The callback has the following arguments:
        * message (bytes) - the received message

        Returns:
            Optional[Callable]: the old callback
        """
        old = self._cb_data_received
        self._cb_data_received = callback
        return old

    @abstractmethod
    def get_info(self) -> str:
        """Return the input information
        """

    @abstractmethod
    def connect(self) -> None:
        """Connects the input
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnects the input
        """

    @abstractmethod
    def is_connected(self) -> bool:
        """ return True if the connection is established """

    @abstractmethod
    def set_separator(self, separator: str) -> None:
        """ set the input separator """

    @abstractmethod
    def send(self, data: bytes) -> None:
        """Send data to the input

        Args:
            data (bytes): data to send
        """
