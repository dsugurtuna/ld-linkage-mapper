"""Offline demo of the LD proxy workflow on synthetic data.

Everything in examples/data is made up: the rsIDs are placeholders, the LD
values are invented, and the participants (SYN001...) do not exist. The
LDproxy files use the same column layout as the real LDlink output, so the
same code runs on a real download or API response.

Run from the repository root:  python examples/demo.py
"""

from __future__ import annotations

from pathlib import Path

from ld_mapper import ParticipantMapper, ProxyFilter, parse_ldproxy

DATA = Path(__file__).parent / "data"
TARGETS = ["rs9000001", "rs9000002"]


def main() -> None:
    # 1. Parse LDproxy tables (here from files; LDProxyClient.query does the same live).
    results = [parse_ldproxy((DATA / f"ldproxy_{t}.txt").read_text(), t) for t in TARGETS]
    for r in results:
        print(f"{r.target_rsid}: {len(r.proxies)} candidate proxy row(s) from LDproxy")

    # 2. Keep perfect proxies (R2 = 1.0) that are not on the blocklist.
    proxy_filter = ProxyFilter.from_blocklist_file(DATA / "blocklist.txt", min_r2=1.0)
    filtered = proxy_filter.filter_batch(results)
    for f in filtered:
        kept = ", ".join(p.rsid for p in f.filtered_proxies) or "none"
        print(f"{f.target_rsid}: kept {f.count} ({kept}); blocklisted {f.excluded_count}")

    # 3. Map to participants: which variant gives each participant data for each target?
    mapping = ParticipantMapper(DATA / "participant_variants.csv").map(filtered)
    print()
    print("participant  " + "  ".join(f"{t:>10}" for t in TARGETS))
    for pid in sorted(mapping.source):
        cells = "  ".join(f"{mapping.source[pid][t] or '-':>10}" for t in TARGETS)
        print(f"{pid:<11}  {cells}")
    print()
    for t in TARGETS:
        print(f"{t}: {mapping.available_count(t)} of {mapping.participant_count} participants")


if __name__ == "__main__":
    main()
