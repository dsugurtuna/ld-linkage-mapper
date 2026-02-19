"""LDlink API client for proxy variant discovery.

Queries the NCI LDlink REST API for proxy variants in linkage disequilibrium
with a set of target SNPs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProxyVariant:
    """A single proxy variant from an LD query."""

    rsid: str
    coord: str = ""
    r2: float = 0.0
    d_prime: float = 0.0
    alleles: str = ""
    distance: int = 0


@dataclass
class ProxyResult:
    """Results of an LD proxy query for one target variant."""

    target_rsid: str
    proxies: List[ProxyVariant] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_proxies(self) -> bool:
        return len(self.proxies) > 0

    @property
    def perfect_proxies(self) -> List[ProxyVariant]:
        """Return proxies with R² = 1.0."""
        return [p for p in self.proxies if p.r2 == 1.0]


class LDProxyClient:
    """Query the NCI LDlink API for proxy variants.

    Parameters
    ----------
    token : str
        LDlink API token.
    population : str
        Reference population (default: GBR for British).
    genome_build : str
        Genome build (grch37 or grch38).
    window : int
        Search window in base pairs.
    rate_limit : float
        Minimum seconds between API calls.
    """

    BASE_URL = "https://ldlink.nih.gov/LDlinkRest/ldproxy"

    def __init__(
        self,
        token: str = "",
        population: str = "GBR",
        genome_build: str = "grch38",
        window: int = 500_000,
        rate_limit: float = 1.0,
    ) -> None:
        self.token = token
        self.population = population
        self.genome_build = genome_build
        self.window = window
        self.rate_limit = rate_limit

    def _parse_response(self, text: str, target: str) -> ProxyResult:
        """Parse the tab-delimited LDproxy API response."""
        result = ProxyResult(target_rsid=target)
        lines = text.strip().split("\n")
        if len(lines) < 2:
            result.error = "No data returned"
            return result

        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            try:
                proxy = ProxyVariant(
                    rsid=parts[0].strip(),
                    coord=parts[1].strip() if len(parts) > 1 else "",
                    alleles=parts[2].strip() if len(parts) > 2 else "",
                    r2=float(parts[6]) if len(parts) > 6 else 0.0,
                    d_prime=float(parts[5]) if len(parts) > 5 else 0.0,
                )
                result.proxies.append(proxy)
            except (ValueError, IndexError):
                continue
        return result

    def query(self, rsid: str) -> ProxyResult:
        """Query LD proxies for a single variant.

        In portfolio mode (no token), returns an empty result.
        With a valid token, makes a live API call.
        """
        if not self.token:
            return ProxyResult(target_rsid=rsid, error="No API token configured")

        try:
            import urllib.request
            import urllib.parse

            params = urllib.parse.urlencode({
                "var": rsid,
                "pop": self.population,
                "r2_d": "r2",
                "window": self.window,
                "genome_build": self.genome_build,
                "token": self.token,
            })
            url = f"{self.BASE_URL}?{params}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8")
            time.sleep(self.rate_limit)
            return self._parse_response(text, rsid)
        except Exception as exc:
            return ProxyResult(target_rsid=rsid, error=str(exc))

    def query_batch(self, rsids: List[str]) -> List[ProxyResult]:
        """Query proxies for multiple variants with rate limiting."""
        return [self.query(r) for r in rsids]
