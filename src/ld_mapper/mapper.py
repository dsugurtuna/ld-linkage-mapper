"""Participant mapping module.

Maps filtered proxy variants to participant-level availability, generating
a per-participant x per-target availability table.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from .filter import FilteredResult


@dataclass
class MappingResult:
    """Result of mapping proxy variants to participants."""

    target_rsids: List[str]
    participant_count: int = 0
    availability: Dict[str, Dict[str, bool]] = field(default_factory=dict)

    def get_participant_availability(self, participant_id: str) -> Dict[str, bool]:
        """Return {target_rsid: available} for one participant."""
        return self.availability.get(participant_id, {})


class ParticipantMapper:
    """Map proxy variants to participant-level data.

    Checks whether participants carry any of the filtered proxy variants
    based on a participant variant file.

    Parameters
    ----------
    participant_file : str or Path
        CSV/TSV file with participants and their available variants.
    participant_col : str
        Column name for participant IDs.
    variant_col : str
        Column name for variant IDs.
    """

    def __init__(
        self,
        participant_file: str | Path,
        participant_col: str = "participant_id",
        variant_col: str = "variant_id",
    ) -> None:
        self._participant_variants: Dict[str, Set[str]] = {}
        self._load(participant_file, participant_col, variant_col)

    def _load(self, path: str | Path, pid_col: str, var_col: str) -> None:
        """Load participant-variant data from a CSV/TSV file."""
        with open(path, newline="") as fh:
            dialect = csv.Sniffer().sniff(fh.read(2048))
            fh.seek(0)
            reader = csv.DictReader(fh, dialect=dialect)
            for row in reader:
                pid = row.get(pid_col, "").strip()
                vid = row.get(var_col, "").strip()
                if pid and vid:
                    self._participant_variants.setdefault(pid, set()).add(vid)

    @property
    def participants(self) -> List[str]:
        return sorted(self._participant_variants.keys())

    def map(self, filtered_results: List[FilteredResult]) -> MappingResult:
        """Map filtered proxy results to participant availability.

        For each participant, checks if they carry any proxy variant
        (or the target variant itself) for each target.
        """
        target_rsids = [r.target_rsid for r in filtered_results]
        result = MappingResult(
            target_rsids=target_rsids,
            participant_count=len(self._participant_variants),
        )

        target_proxy_sets: Dict[str, Set[str]] = {}
        for fr in filtered_results:
            proxy_ids = {p.rsid for p in fr.filtered_proxies}
            proxy_ids.add(fr.target_rsid)
            target_proxy_sets[fr.target_rsid] = proxy_ids

        for pid, variants in self._participant_variants.items():
            avail: Dict[str, bool] = {}
            for target, proxies in target_proxy_sets.items():
                avail[target] = bool(variants & proxies)
            result.availability[pid] = avail

        return result

    @staticmethod
    def export_csv(
        result: MappingResult,
        output_path: str | Path,
    ) -> None:
        """Export the availability matrix to CSV."""
        with open(output_path, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["participant_id"] + result.target_rsids)
            for pid in sorted(result.availability.keys()):
                row = [pid] + [
                    "Yes" if result.availability[pid].get(t) else "No"
                    for t in result.target_rsids
                ]
                writer.writerow(row)
