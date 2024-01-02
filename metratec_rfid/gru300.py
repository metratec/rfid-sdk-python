"""GRU 300 class
"""

from .pulsar_lr import PulsarLRBase
from .reader import ExpectedReaderInfo


@ExpectedReaderInfo("GRU300", "GRU300", 1.0)
class GRU300(PulsarLRBase):
    """GRU 300 class"""
