"""Proxy variant filtering module.

Filters LD proxy results to retain only perfect proxies ($R^2 = 1.0$),
excluding blocklisted variants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

from .proxy import ProxyResult, ProxyVariant


@dataclass
class FilteredResult:
    """Filtered proxy variants for a target."""

    target_rsid: str
    filtered_proxies: List[ProxyVariant] = field(default_factory=list)
    excluded_count: int = 0

    @property
    def count(self) -> int:
        return len(self.filtered_proxies)


class ProxyFilter:
    """Filter proxy variants by R² threshold and blocklist.

    Parameters
    ----------
    min_r2 : float
        Minimum R² to retain a proxy. Default 1.0 (perfect LD).
    blocklist : set of str, optional
        rsIDs to exclude from results.
    """

    def __init__(
        self,
        min_r2: float = 1.0,
        blocklist: Set[str] | None = None,
    ) -> None:
        self.min_r2 = min_r2
        self.blocklist = blocklist or set()

    @classmethod
    def from_blocklist_file(
        cls,
        path: str | Path,
        min_r2: float = 1.0,
    ) -> "ProxyFilter":
        """Create a filter loading the blocklist from a file."""
        with open(path) as fh:
            blocklist = {line.strip() for line in fh if line.strip()}
        return cls(min_r2=min_r2, blocklist=blocklist)

    def filter(self, result: ProxyResult) -> FilteredResult:
        """Filter a single proxy result."""
        filtered = FilteredResult(target_rsid=result.target_rsid)
        for proxy in result.proxies:
            if proxy.r2 < self.min_r2:
                continue
            if proxy.rsid in self.blocklist:
                filtered.excluded_count += 1
                continue
            filtered.filtered_proxies.append(proxy)
        return filtered

    def filter_batch(self, results: List[ProxyResult]) -> List[FilteredResult]:
        """Filter multiple proxy results."""
        return [self.filter(r) for r in results]
