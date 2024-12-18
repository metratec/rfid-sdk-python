"""Reader exception classes"""


class RfidReaderException(Exception):
    """
    Exception class for the Metratec RFID reader
    """

    def __init__(self, message) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        super().__init__(message)


class RfidTransponderException(RfidReaderException):
    """
    Exception class for a transponder error
    """

    def __init__(self, message) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        super().__init__(message)
