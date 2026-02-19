"""LD Linkage Mapper — LD proxy discovery and participant mapping."""

__version__ = "2.0.0"

from .proxy import LDProxyClient, ProxyResult
from .filter import ProxyFilter, FilteredResult
from .mapper import ParticipantMapper, MappingResult

__all__ = [
    "LDProxyClient",
    "ProxyResult",
    "ProxyFilter",
    "FilteredResult",
    "ParticipantMapper",
    "MappingResult",
]
