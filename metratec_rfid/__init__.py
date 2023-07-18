"""
rfid module
"""
# from .uhf_tag import UhfTag
# from .hf_tag import HfTag

# from .connection import Connection
# from .connection.serial_connection import SerialConnection
# from .connection.socket_connection import SocketConnection

from .connection import Connection  # noqa: F401
# from .connection import Connection, SerialConnection, SocketConnection  # noqa: F401
from .reader_exception import RfidReaderException  # noqa: F401

from .uhf_reader_gen1 import UhfReaderGen1  # noqa: F401
try:
    from .deskid_uhf import DeskIdUhf  # noqa: F401
except ModuleNotFoundError:
    pass
from .pulsar_mx import PulsarMX  # noqa: F401

from .hf_reader_gen1 import HfReaderGen1  # noqa: F401
try:
    from .deskid_iso import DeskIdIso  # noqa: F401
except ModuleNotFoundError:
    pass
from .quasar_mx import QuasarMX  # noqa: F401
from .quasar_lr import QuasarLR  # noqa: F401

from .uhf_reader_gen2 import UhfReaderGen2  # noqa: F401
from .pulsar_lr import PulsarLR  # noqa: F401

from .hf_tag import HfTag  # noqa: F401
from .uhf_tag import UhfTag  # noqa: F401

__version_info__ = (1, 0, 0)
__version__ = ".".join(str(x) for x in __version_info__)
__author__ = 'neumann@metratec.com'
