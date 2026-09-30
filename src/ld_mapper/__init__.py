"""LD Linkage Mapper — LD proxy discovery and participant mapping."""

__version__ = "2.0.0"

from .filter import FilteredResult, ProxyFilter
from .mapper import MappingResult, ParticipantMapper
from .proxy import LDProxyClient, ProxyResult

__all__ = [
    "FilteredResult",
    "LDProxyClient",
    "MappingResult",
    "ParticipantMapper",
    "ProxyFilter",
    "ProxyResult",
]
