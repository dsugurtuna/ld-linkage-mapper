"""Tests for ProxyFilter."""

from ld_mapper.filter import ProxyFilter
from ld_mapper.proxy import ProxyResult, ProxyVariant


def _make_result() -> ProxyResult:
    return ProxyResult(
        target_rsid="rs100",
        proxies=[
            ProxyVariant(rsid="rs200", r2=1.0),
            ProxyVariant(rsid="rs300", r2=0.95),
            ProxyVariant(rsid="rs400", r2=1.0),
            ProxyVariant(rsid="rs500", r2=0.50),
        ],
    )


class TestProxyFilter:
    def test_perfect_ld_filter(self):
        pf = ProxyFilter(min_r2=1.0)
        result = pf.filter(_make_result())
        assert result.count == 2
        rsids = {p.rsid for p in result.filtered_proxies}
        assert rsids == {"rs200", "rs400"}

    def test_custom_threshold(self):
        pf = ProxyFilter(min_r2=0.9)
        result = pf.filter(_make_result())
        assert result.count == 3
        rsids = {p.rsid for p in result.filtered_proxies}
        assert rsids == {"rs200", "rs300", "rs400"}

    def test_blocklist(self):
        pf = ProxyFilter(min_r2=1.0, blocklist={"rs200"})
        result = pf.filter(_make_result())
        assert result.count == 1
        assert result.filtered_proxies[0].rsid == "rs400"
        assert result.excluded_count == 1

    def test_blocklist_file(self, tmp_path):
        bl = tmp_path / "blocklist.txt"
        bl.write_text("rs200\nrs400\n")
        pf = ProxyFilter.from_blocklist_file(bl, min_r2=1.0)
        result = pf.filter(_make_result())
        assert result.count == 0
        assert result.excluded_count == 2

    def test_filter_batch(self):
        r1 = ProxyResult(
            target_rsid="rs10",
            proxies=[ProxyVariant(rsid="rs11", r2=1.0)],
        )
        r2 = ProxyResult(
            target_rsid="rs20",
            proxies=[ProxyVariant(rsid="rs21", r2=0.5)],
        )
        pf = ProxyFilter(min_r2=1.0)
        results = pf.filter_batch([r1, r2])
        assert results[0].count == 1
        assert results[1].count == 0

    def test_target_rsid_preserved(self):
        pf = ProxyFilter()
        result = pf.filter(_make_result())
        assert result.target_rsid == "rs100"


def test_min_r2_out_of_range_rejected():
    import pytest

    with pytest.raises(ValueError):
        ProxyFilter(min_r2=1.5)


def test_blocklist_file_ignores_comments(tmp_path):
    bl = tmp_path / "blocklist.txt"
    bl.write_text("# known multi-allelic sites\nrs200\n")
    pf = ProxyFilter.from_blocklist_file(bl)
    assert pf.blocklist == {"rs200"}


def test_query_error_carried_through():
    result = ProxyResult(target_rsid="rs1", error="No API token configured")
    assert ProxyFilter().filter(result).error == "No API token configured"
