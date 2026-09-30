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


# Header and row layout as documented for LDproxy (query variant first).
LDPROXY_RESPONSE = (
    "RS_Number\tCoord\tAlleles\tMAF\tDistance\tDprime\tR2\tCorrelated_Alleles\tRegulomeDB\tFunction\n"
    "rs100\tchr1:1000\t(A/G)\t0.2\t0\t1.0\t1.0\tA=A,G=G\t4\tNA\n"
    "rs101\tchr1:1500\t(C/T)\t0.2\t500\t1.0\t1.0\tA=C,G=T\t5\tNA\n"
    ".\tchr1:1600\t(G/A)\t0.2\t600\t1.0\t1.0\tA=G,G=A\t7\tNA\n"
    "rs102\tchr1:-\t(T/C)\t0.3\t-800\t0.9\t0.64\tA=T,G=C\t7\tNA\n"
)


class TestLDproxyParsing:
    def test_query_variant_row_is_not_a_proxy(self):
        result = LDProxyClient()._parse_response(LDPROXY_RESPONSE, "rs100")
        assert [p.rsid for p in result.proxies] == ["rs101", "rs102"]

    def test_columns_located_by_header(self):
        result = LDProxyClient()._parse_response(LDPROXY_RESPONSE, "rs100")
        p = result.proxies[0]
        assert p.distance == 500
        assert p.maf == 0.2
        assert p.correlated_alleles == "A=C,G=T"
        assert result.proxies[1].distance == -800

    def test_json_error_body(self):
        result = LDProxyClient()._parse_response('{"error": "rs1 is not in 1000G."}', "rs1")
        assert result.error == "rs1 is not in 1000G."
        assert not result.has_proxies

    def test_unexpected_header(self):
        result = LDProxyClient()._parse_response("error: bad token\nmore", "rs1")
        assert result.error is not None
        assert result.error.startswith("Unexpected response")


class TestQueryWithFakeTransport:
    def test_query_uses_fetch_and_parses(self, monkeypatch):
        client = LDProxyClient(token="t", rate_limit=0)
        seen = []

        def fake_fetch(url: str) -> str:
            seen.append(url)
            return LDPROXY_RESPONSE

        monkeypatch.setattr(client, "_fetch", fake_fetch)
        result = client.query("rs100")
        assert result.error is None
        assert len(result.proxies) == 2
        assert "var=rs100" in seen[0] and "pop=GBR" in seen[0]

    def test_network_error_is_returned_not_raised(self, monkeypatch):
        import urllib.error

        client = LDProxyClient(token="t", rate_limit=0)

        def failing_fetch(url: str) -> str:
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(client, "_fetch", failing_fetch)
        result = client.query("rs100")
        assert result.error is not None
        assert "connection refused" in result.error

    def test_rate_limit_spaces_requests(self, monkeypatch):
        import ld_mapper.proxy as proxy_module

        sleeps: list[float] = []
        monkeypatch.setattr(proxy_module.time, "sleep", sleeps.append)
        client = LDProxyClient(token="t", rate_limit=5.0)
        monkeypatch.setattr(client, "_fetch", lambda url: LDPROXY_RESPONSE)
        client.query_batch(["rs100", "rs100"])
        # No wait before the first request; roughly rate_limit before the second.
        assert len(sleeps) == 1
        assert 4.0 < sleeps[0] <= 5.0
