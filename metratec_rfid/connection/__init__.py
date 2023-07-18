""" connection module

"""
__version_info__ = (1, 0, 0)
__version__ = ".".join(str(x) for x in __version_info__)
__author__ = 'neumann@metratec.com'

from .connection import Connection  # noqa: F401
# from .serial_connection import SerialConnection  # noqa: F401
# from .socket_connection import SocketConnection  # noqa: F401
