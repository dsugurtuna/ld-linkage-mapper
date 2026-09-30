"""LDlink API client for proxy variant discovery.

Queries the NCI LDlink LDproxy endpoint for variants in linkage disequilibrium
with a target SNP, and parses the tab-delimited response.

Response columns (as returned by LDproxy): RS_Number, Coord, Alleles, MAF,
Distance, Dprime, R2, Correlated_Alleles, then annotation columns. The first
data row is the query variant itself (distance 0), which is not a proxy.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ProxyVariant:
    """A single proxy variant from an LD query."""

    rsid: str
    coord: str = ""
    r2: float = 0.0
    d_prime: float = 0.0
    alleles: str = ""
    distance: int = 0
    maf: float = 0.0
    correlated_alleles: str = ""


@dataclass
class ProxyResult:
    """Results of an LD proxy query for one target variant."""

    target_rsid: str
    proxies: list[ProxyVariant] = field(default_factory=list)
    error: str | None = None

    @property
    def has_proxies(self) -> bool:
        return len(self.proxies) > 0

    @property
    def perfect_proxies(self) -> list[ProxyVariant]:
        """Return proxies with R² = 1.0 in the reference population."""
        return [p for p in self.proxies if p.r2 == 1.0]


def _normalise(name: str) -> str:
    """Normalise a header name: 'RS_Number', 'RS Number' -> 'rsnumber'."""
    return name.strip().lower().replace("_", "").replace(" ", "")


def parse_ldproxy(text: str, target: str) -> ProxyResult:
    """Parse a tab-delimited LDproxy table (API response or web download).

    Columns are located by header name, not position. The query variant
    itself and rows without an rsID (``.``) are skipped, because neither
    can act as a proxy that is matched by rsID.
    """
    result = ProxyResult(target_rsid=target)
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        result.error = str(payload.get("error", "Unrecognised JSON response"))
        return result

    lines = stripped.split("\n")
    if len(lines) < 2:
        result.error = "No data returned"
        return result

    header = [_normalise(h) for h in lines[0].split("\t")]
    if "rsnumber" not in header or "r2" not in header:
        result.error = f"Unexpected response: {lines[0][:200]}"
        return result
    col = {name: i for i, name in enumerate(header)}

    def cell(parts: list[str], name: str) -> str:
        i = col.get(name)
        return parts[i].strip() if i is not None and i < len(parts) else ""

    for line in lines[1:]:
        parts = line.split("\t")
        rsid = cell(parts, "rsnumber")
        if not rsid or rsid == "." or rsid.lower() == target.lower():
            continue
        try:
            proxy = ProxyVariant(
                rsid=rsid,
                coord=cell(parts, "coord"),
                alleles=cell(parts, "alleles"),
                r2=float(cell(parts, "r2")),
                d_prime=float(cell(parts, "dprime") or 0.0),
                distance=int(float(cell(parts, "distance") or 0)),
                maf=float(cell(parts, "maf") or 0.0),
                correlated_alleles=cell(parts, "correlatedalleles"),
            )
        except ValueError:
            continue
        result.proxies.append(proxy)
    return result


class LDProxyClient:
    """Query the NCI LDlink API for proxy variants.

    Parameters
    ----------
    token : str
        LDlink API token. Without one, ``query`` returns an error result and
        makes no network call.
    population : str
        1000 Genomes reference population code (default: GBR).
    genome_build : str
        Genome build (grch37 or grch38).
    window : int
        Search window in base pairs either side of the target.
    rate_limit : float
        Minimum seconds between the start of consecutive API calls.
    timeout : float
        Per-request timeout in seconds.
    """

    BASE_URL = "https://ldlink.nih.gov/LDlinkRest/ldproxy"

    def __init__(
        self,
        token: str = "",
        population: str = "GBR",
        genome_build: str = "grch38",
        window: int = 500_000,
        rate_limit: float = 1.0,
        timeout: float = 30.0,
    ) -> None:
        self.token = token
        self.population = population
        self.genome_build = genome_build
        self.window = window
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._last_request: float | None = None

    def _parse_response(self, text: str, target: str) -> ProxyResult:
        """Parse an LDproxy response; see :func:`parse_ldproxy`."""
        return parse_ldproxy(text, target)

    def _wait_for_rate_limit(self) -> None:
        """Sleep so that consecutive requests start at least rate_limit apart."""
        now = time.monotonic()
        if self._last_request is not None:
            remaining = self.rate_limit - (now - self._last_request)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request = time.monotonic()

    def _fetch(self, url: str) -> str:
        """Perform the HTTP GET. Separate so tests can replace it."""
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body: bytes = resp.read()
        return body.decode("utf-8")

    def query(self, rsid: str) -> ProxyResult:
        """Query LD proxies for a single variant.

        Without a token, returns an error result and makes no network call.
        Network and HTTP errors are returned in ``ProxyResult.error`` rather
        than raised, so one failed variant does not stop a batch.
        """
        if not self.token:
            return ProxyResult(target_rsid=rsid, error="No API token configured")

        params = urllib.parse.urlencode(
            {
                "var": rsid,
                "pop": self.population,
                "r2_d": "r2",
                "window": self.window,
                "genome_build": self.genome_build,
                "token": self.token,
            }
        )
        self._wait_for_rate_limit()
        try:
            text = self._fetch(f"{self.BASE_URL}?{params}")
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
            return ProxyResult(target_rsid=rsid, error=str(exc))
        return self._parse_response(text, rsid)

    def query_batch(self, rsids: list[str]) -> list[ProxyResult]:
        """Query proxies for multiple variants, one at a time, rate limited."""
        return [self.query(r) for r in rsids]
