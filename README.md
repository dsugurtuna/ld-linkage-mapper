# LD Linkage Mapper

[![CI](https://github.com/dsugurtuna/ld-linkage-mapper/actions/workflows/ci.yml/badge.svg)](https://github.com/dsugurtuna/ld-linkage-mapper/actions/workflows/ci.yml)

**Expand variant coverage using Linkage Disequilibrium proxy discovery, filtering, and participant-level mapping.**

In large-scale biobanks, not every genetic variant is directly measured on the genotyping array. Variants close to each other are often co-inherited (linkage disequilibrium). When a target variant is absent, a *perfect proxy* ($R^2 = 1.0$) that **is** present on the array can serve as a surrogate. This toolkit automates the full workflow: querying the NCI LDlink API, filtering results by $R^2$ threshold and blocklist, and mapping filtered proxies to participant-level availability.

> **Portfolio project.** Built as a generalised demonstration of LD proxy workflows. No real participant data is included.

---

## Architecture

```
src/ld_mapper/
    __init__.py          # Public API exports
    proxy.py             # LDlink REST API client (LDProxyClient)
    filter.py            # R² / blocklist filtering (ProxyFilter)
    mapper.py            # Participant-variant mapping (ParticipantMapper)
tests/
    test_proxy.py        # Client + parser tests
    test_filter.py       # Filter logic + blocklist tests
    test_mapper.py       # Participant mapping + CSV export tests
legacy/
    query_ld_proxy.sh    # Original curl-based API client
    filter_high_ld_variants.sh  # Original awk-based R²=1.0 filter
    map_variants_to_participants.py  # Original Python mapper
```

---

## Quick start

```bash
pip install -e ".[dev]"
pytest -v
```

### Python API

```python
from ld_mapper import LDProxyClient, ProxyFilter, ParticipantMapper

# 1. Query LD proxies (requires NCI LDlink API token)
client = LDProxyClient(token="your_token", population="GBR", genome_build="grch38")
results = client.query_batch(["rs429358", "rs7412"])

# 2. Filter to perfect proxies, excluding blocklisted variants
filt = ProxyFilter(min_r2=1.0, blocklist={"rs12345"})
filtered = filt.filter_batch(results)

# 3. Map to participant availability
mapper = ParticipantMapper("participants.csv")
mapping = mapper.map(filtered)
ParticipantMapper.export_csv(mapping, "availability.csv")
```

---

## Key features

| Feature | Detail |
| :--- | :--- |
| **LDlink REST client** | Rate-limited queries to the NCI LDproxy endpoint with configurable population, genome build, and search window |
| **Configurable filtering** | $R^2$ threshold (default 1.0) with optional blocklist from file |
| **Participant mapping** | $O(1)$ set-based lookup mapping proxy variants to participant genotype availability |
| **CSV export** | Participant × target availability matrix |
| **Batch processing** | Process multiple target rsIDs in a single call |

## Development

```bash
make dev        # install with dev dependencies
make test       # run pytest
make lint       # run ruff
make clean      # remove build artefacts
```

## Jira provenance

| Ticket | Description |
| :--- | :--- |
| BIOIN-92 | LD proxy lookup and participant mapping for recall feasibility |

---

*Created by [dsugurtuna](https://github.com/dsugurtuna)*
