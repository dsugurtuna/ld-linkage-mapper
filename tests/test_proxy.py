"""Tests for LDProxyClient."""

from ld_mapper.proxy import LDProxyClient, ProxyResult, ProxyVariant


SAMPLE_RESPONSE = """RS Number\tCoord\tAlleles\tMAF\tDistance\tDprime\tR2
rs123\tchr6:12345\tA/G\t0.15\t0\t1.0\t1.0
rs456\tchr6:12400\tT/C\t0.20\t55\t0.95\t0.85
rs789\tchr6:12500\tG/A\t0.10\t155\t1.0\t1.0
"""


class TestLDProxyClient:
    def test_parse_response(self):
        client = LDProxyClient()
        result = client._parse_response(SAMPLE_RESPONSE, "rs999")
        assert result.target_rsid == "rs999"
        assert result.has_proxies
        assert len(result.proxies) == 3

    def test_parse_r2_values(self):
        client = LDProxyClient()
        result = client._parse_response(SAMPLE_RESPONSE, "rs999")
        assert result.proxies[0].r2 == 1.0
        assert result.proxies[1].r2 == 0.85
        assert result.proxies[2].r2 == 1.0

    def test_perfect_proxies(self):
        client = LDProxyClient()
        result = client._parse_response(SAMPLE_RESPONSE, "rs999")
        perfect = result.perfect_proxies
        assert len(perfect) == 2
        assert perfect[0].rsid == "rs123"
        assert perfect[1].rsid == "rs789"

    def test_parse_empty_response(self):
        client = LDProxyClient()
        result = client._parse_response("", "rs000")
        assert not result.has_proxies
        assert result.error == "No data returned"

    def test_query_without_token(self):
        client = LDProxyClient(token="")
        result = client.query("rs123")
        assert result.error == "No API token configured"
        assert not result.has_proxies

    def test_query_batch(self):
        client = LDProxyClient(token="")
        results = client.query_batch(["rs1", "rs2", "rs3"])
        assert len(results) == 3
        assert all(r.error == "No API token configured" for r in results)

    def test_proxy_variant_fields(self):
        pv = ProxyVariant(rsid="rs100", coord="chr6:5000", r2=0.95, d_prime=0.99)
        assert pv.rsid == "rs100"
        assert pv.r2 == 0.95


class TestProxyResult:
    def test_empty_result(self):
        r = ProxyResult(target_rsid="rs1")
        assert not r.has_proxies
        assert r.perfect_proxies == []

    def test_result_with_proxies(self):
        r = ProxyResult(
            target_rsid="rs1",
            proxies=[
                ProxyVariant(rsid="rs2", r2=1.0),
                ProxyVariant(rsid="rs3", r2=0.8),
            ],
        )
        assert r.has_proxies
        assert len(r.perfect_proxies) == 1
