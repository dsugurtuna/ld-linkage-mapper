"""Participant mapping module.

Maps filtered proxy variants to participant-level availability, generating
a per-participant x per-target availability table.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .filter import FilteredResult


@dataclass
class MappingResult:
    """Result of mapping proxy variants to participants.

    ``availability[pid][target]`` is True when the participant has genotype
    data for the target or for at least one retained proxy.
    ``source[pid][target]`` names the variant that provides it: the target
    itself when typed, otherwise the best proxy (highest R², then nearest),
    or None when nothing is available.
    """

    target_rsids: list[str]
    participant_count: int = 0
    availability: dict[str, dict[str, bool]] = field(default_factory=dict)
    source: dict[str, dict[str, str | None]] = field(default_factory=dict)

    def get_participant_availability(self, participant_id: str) -> dict[str, bool]:
        """Return {target_rsid: available} for one participant."""
        return self.availability.get(participant_id, {})

    def available_count(self, target_rsid: str) -> int:
        """Number of participants with the target or a proxy available."""
        return sum(1 for avail in self.availability.values() if avail.get(target_rsid))


class ParticipantMapper:
    """Map proxy variants to participant-level genotype availability.

    Reads a long-format file with one row per (participant, typed variant),
    for example exported from each participant's array manifest, and checks
    whether each participant has data for a target variant or one of its
    proxies. This is availability of genotype data, not carrier status.

    Parameters
    ----------
    participant_file : str or Path
        CSV or TSV file with a participant column and a variant column.
    participant_col : str
        Column name for participant IDs.
    variant_col : str
        Column name for variant IDs (rsIDs).
    delimiter : str, optional
        Field delimiter. If omitted, tab is used when the header line
        contains a tab, otherwise comma.
    """

    def __init__(
        self,
        participant_file: str | Path,
        participant_col: str = "participant_id",
        variant_col: str = "variant_id",
        delimiter: str | None = None,
    ) -> None:
        self._participant_variants: dict[str, set[str]] = {}
        self._load(participant_file, participant_col, variant_col, delimiter)

    def _load(self, path: str | Path, pid_col: str, var_col: str, delimiter: str | None) -> None:
        """Load participant-variant data from a CSV/TSV file."""
        with open(path, newline="") as fh:
            header = fh.readline()
            if delimiter is None:
                delimiter = "\t" if "\t" in header else ","
            fh.seek(0)
            reader = csv.DictReader(fh, delimiter=delimiter)
            missing = {pid_col, var_col} - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path}: missing column(s) {sorted(missing)}")
            for row in reader:
                pid = (row.get(pid_col) or "").strip()
                vid = (row.get(var_col) or "").strip()
                if pid and vid:
                    self._participant_variants.setdefault(pid, set()).add(vid)

    @property
    def participants(self) -> list[str]:
        return sorted(self._participant_variants.keys())

    def map(self, filtered_results: list[FilteredResult]) -> MappingResult:
        """Map filtered proxy results to participant availability.

        For each participant and target, the target is available if the
        participant has the target itself or any retained proxy typed.
        """
        target_rsids = [r.target_rsid for r in filtered_results]
        result = MappingResult(
            target_rsids=target_rsids,
            participant_count=len(self._participant_variants),
        )

        # Candidate variants per target, in order of preference: the target
        # itself, then proxies by descending R² and ascending distance.
        preference: dict[str, list[str]] = {}
        for fr in filtered_results:
            ranked = sorted(fr.filtered_proxies, key=lambda p: (-p.r2, abs(p.distance), p.rsid))
            preference[fr.target_rsid] = [fr.target_rsid] + [p.rsid for p in ranked]

        for pid, variants in self._participant_variants.items():
            avail: dict[str, bool] = {}
            source: dict[str, str | None] = {}
            for target, candidates in preference.items():
                chosen = next((v for v in candidates if v in variants), None)
                avail[target] = chosen is not None
                source[target] = chosen
            result.availability[pid] = avail
            result.source[pid] = source

        return result

    @staticmethod
    def export_csv(
        result: MappingResult,
        output_path: str | Path,
        show_source: bool = False,
    ) -> None:
        """Export the participant x target matrix to CSV.

        Cells are ``Yes``/``No`` by default. With ``show_source=True`` each
        cell holds the rsID that provides the data (``NA`` when none).
        """
        with open(output_path, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["participant_id", *result.target_rsids])
            for pid in sorted(result.availability.keys()):
                if show_source:
                    cells = [result.source[pid].get(t) or "NA" for t in result.target_rsids]
                else:
                    cells = ["Yes" if result.availability[pid].get(t) else "No" for t in result.target_rsids]
                writer.writerow([pid, *cells])
