"""
rfid module
"""
# from .uhf_tag import UhfTag
# from .hf_tag import HfTag

# from .connection import Connection
# from .connection.serial_connection import SerialConnection
# from .connection.socket_connection import SocketConnection

__author__ = "Matthias Neumann"
__license__ = "MIT License"
__version__ = "1.3.2"
__maintainer__ = "Matthias Neumann"
__email__ = "neumann@metratec.com"

from .connection import Connection  # noqa: F401
from .reader_exception import RfidReaderException  # noqa: F401
from .reader_exception import RfidTransponderException  # noqa: F401

from .uhf_reader_ascii import UhfReaderAscii  # noqa: F401
try:
    from .deskid_uhf import DeskIdUhf  # noqa: F401
    from .pulsar_mx import PulsarMX  # noqa: F401
except ModuleNotFoundError:
    pass

from .hf_reader_ascii import HfReaderAscii  # noqa: F401
try:
    from .deskid_iso import DeskIdIso  # noqa: F401
    from .quasar_lr import QuasarLR  # noqa: F401
    from .quasar_mx import QuasarMX  # noqa: F401
except ModuleNotFoundError:
    pass

from .uhf_reader_at import UhfReaderAT  # noqa: F401
try:
    from .pulsar_lr import PulsarLR  # noqa: F401
    from .plrm import Plrm  # noqa: F401
    from .deskid_uhf import DeskIdUhfv2, DeskIdUhfv2FCC  # noqa: F401
    from .qrg2 import QRG2, QRG2FCC  # noqa: F401
    from .dwarfg2_v2 import DwarfG2v2, DwarfG2Miniv2, DwarfG2XRv2  # noqa: F401
except ModuleNotFoundError:
    pass

from .nfc_reader_at import NfcReaderAT, NfcMode, NTagMirrorMode  # noqa: F401
try:
    from .deskid_nfc import DeskIdNfc  # noqa: F401
    from .qr_nfc import QrNfc  # noqa: F401
except ModuleNotFoundError:
    pass

from .hf_tag import HfTag  # noqa: F401
from .hf_tag import HfTagInfo  # noqa: F401
from .hf_tag import ISO15Tag  # noqa: F401
from .hf_tag import ISO14ATag  # noqa: F401
from .uhf_tag import UhfTag  # noqa: F401

from .utils import detect_readers  # noqa: F401

__version_info__ = (1, 3, 0)
__version__ = ".".join(str(x) for x in __version_info__)
__author__ = 'neumann@metratec.com'
