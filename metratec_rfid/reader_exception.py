""" reader exception  """


class RfidReaderException(Exception):
    """
    Exception class for the metratec rfid reader
    """

    def __init__(self, message) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        super().__init__(message)
