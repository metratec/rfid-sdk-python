""" base class with status """

import logging
from time import time
from typing import Any, Callable, Dict, Optional


class BaseClass:
    """Base Class with status and logger
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        super().__init__()
        self._logger: logging.Logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self._name: str = name if name else self.__class__.__name__
        self._status: Dict[str, Any] = {'type': 'status', 'instance': name,
                                        'status': 0, 'message': 'initialised', 'timestamp': time()}
        self._cb_status: Optional[Callable] = None

    def get_logger(self) -> logging.Logger:
        """Return the logger.

        Returns:
            logging.Logger: The logger for this instance.
        """
        return self._logger

    def get_name(self) -> str:
        """Get the reader name.

        Returns:
            str: The reader name.
        """
        return self._name

    def _update_status(self, status: int, message: str, timestamp=None) -> None:
        """
        update the instance status

        Parameter:
        * status    -- status, integer
        * message   -- status message
        * timestamp -- timestamp
        """
        if self._status['status'] == status and self._status['message'] == message:
            return
        self._status['status'] = status
        self._status['message'] = message
        self._status['timestamp'] = timestamp if timestamp else time()
        self.get_logger().debug("Status updated to \"%s\" (%d)", message, status)
        if self._cb_status and status != 0:
            self._cb_status(self._status.copy())

    def set_cb_status(self, callback: Optional[Callable]) -> Optional[Callable]:
        """Set the callback for status changes.

        Define a callback which will be triggered whenever the status of
        the reader changes. The callback has the following arguments:

        * status (Dict[str, Any]) - The new reader status dictionary, which
          contains at least the 'status', 'message' and 'timestamp' keys.

        Args:
            callback (Callable): Reference to the callback function to use.

        Returns:
            Optional[Callable]: The old callback.
        """
        old = self._cb_status
        self._cb_status = callback
        return old
