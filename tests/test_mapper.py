"""Tests for ParticipantMapper."""

import csv

from ld_mapper.proxy import ProxyVariant
from ld_mapper.filter import FilteredResult
from ld_mapper.mapper import ParticipantMapper, MappingResult


def _write_participant_file(path, rows):
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["participant_id", "variant_id"])
        for row in rows:
            writer.writerow(row)


def _make_filtered_results():
    return [
        FilteredResult(
            target_rsid="rs10",
            filtered_proxies=[
                ProxyVariant(rsid="rs11", r2=1.0),
                ProxyVariant(rsid="rs12", r2=1.0),
            ],
        ),
        FilteredResult(
            target_rsid="rs20",
            filtered_proxies=[ProxyVariant(rsid="rs21", r2=1.0)],
        ),
    ]


class TestParticipantMapper:
    def test_load_and_participants(self, tmp_path):
        pf = tmp_path / "part.csv"
        _write_participant_file(pf, [
            ["P001", "rs11"],
            ["P001", "rs99"],
            ["P002", "rs21"],
        ])
        mapper = ParticipantMapper(pf)
        assert sorted(mapper.participants) == ["P001", "P002"]

    def test_map_availability(self, tmp_path):
        pf = tmp_path / "part.csv"
        _write_participant_file(pf, [
            ["P001", "rs11"],
            ["P002", "rs21"],
            ["P003", "rs99"],
        ])
        mapper = ParticipantMapper(pf)
        results = _make_filtered_results()
        mapping = mapper.map(results)

        assert mapping.participant_count == 3
        assert mapping.availability["P001"]["rs10"] is True
        assert mapping.availability["P001"]["rs20"] is False
        assert mapping.availability["P002"]["rs20"] is True
        assert mapping.availability["P003"]["rs10"] is False

    def test_target_variant_direct_match(self, tmp_path):
        pf = tmp_path / "part.csv"
        _write_participant_file(pf, [["P001", "rs10"]])
        mapper = ParticipantMapper(pf)
        results = _make_filtered_results()
        mapping = mapper.map(results)
        assert mapping.availability["P001"]["rs10"] is True

    def test_export_csv(self, tmp_path):
        pf = tmp_path / "part.csv"
        _write_participant_file(pf, [
            ["P001", "rs11"],
            ["P002", "rs21"],
        ])
        mapper = ParticipantMapper(pf)
        results = _make_filtered_results()
        mapping = mapper.map(results)

        out = tmp_path / "output.csv"
        ParticipantMapper.export_csv(mapping, out)

        with open(out) as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 2
        p1 = next(r for r in rows if r["participant_id"] == "P001")
        assert p1["rs10"] == "Yes"
        assert p1["rs20"] == "No"

    def test_get_participant_availability(self, tmp_path):
        pf = tmp_path / "part.csv"
        _write_participant_file(pf, [["P001", "rs11"]])
        mapper = ParticipantMapper(pf)
        mapping = mapper.map(_make_filtered_results())
        avail = mapping.get_participant_availability("P001")
        assert avail["rs10"] is True
        missing = mapping.get_participant_availability("NOPE")
        assert missing == {}
