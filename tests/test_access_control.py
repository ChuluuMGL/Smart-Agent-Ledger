"""Security defaults: loopback-only without auth, no CORS by default, CSRF/Host guards.

The first half tests access_control.py directly (no FastAPI needed). The second
half drives the real gateway / collector apps through Starlette's TestClient.
"""
import inspect

import pytest

import access_control as ac


# ---------------------------------------------------------------------------
# Pure logic
# ---------------------------------------------------------------------------

class TestIsLocalClient:
    @pytest.mark.parametrize("host", ["127.0.0.1", "127.8.9.10", "::1", "::ffff:127.0.0.1"])
    def test_loopback_is_local(self, host):
        assert ac.is_local_client(host, bridge_ips=()) is True

    @pytest.mark.parametrize("host", ["192.168.1.20", "10.0.0.5", "100.64.1.2", "fd00::1", "0.0.0.0", "", None, "testclient"])
    def test_non_loopback_is_not_local(self, host):
        assert ac.is_local_client(host, bridge_ips=()) is False

    def test_extra_names(self):
        assert ac.is_local_client("testclient", extra_local_names={"testclient"}, bridge_ips=()) is True

    def test_trusted_bridge_ip(self):
        assert ac.is_local_client("172.17.0.1", bridge_ips={"172.17.0.1"}) is True
        assert ac.is_local_client("172.17.0.2", bridge_ips={"172.17.0.1"}) is False


class TestDockerBridge:
    ROUTE = (
        "Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\n"
        "eth0\t00000000\t010011AC\t0003\t0\t0\t0\t00000000\n"
        "eth0\t000011AC\t00000000\t0001\t0\t0\t0\t0000FFFF\n"
    )

    def test_default_gateway_parsed(self, tmp_path):
        route = tmp_path / "route"
        route.write_text(self.ROUTE)
        assert ac.docker_default_gateway(route) == "172.17.0.1"

    def test_missing_route_file(self, tmp_path):
        assert ac.docker_default_gateway(tmp_path / "nope") is None

    def test_flag_off_by_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv("SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE", raising=False)
        route = tmp_path / "route"
        route.write_text(self.ROUTE)
        assert ac.trusted_docker_bridge_ips(route_path=route) == frozenset()

    def test_flag_auto_uses_gateway(self, tmp_path):
        route = tmp_path / "route"
        route.write_text(self.ROUTE)
        assert ac.trusted_docker_bridge_ips("1", route_path=route) == frozenset({"172.17.0.1"})

    def test_flag_explicit_ips(self, tmp_path):
        assert ac.trusted_docker_bridge_ips("192.168.65.1, bogus", route_path=tmp_path / "x") == frozenset({"192.168.65.1"})


class TestHostHeader:
    @pytest.mark.parametrize("host", ["localhost:8001", "127.0.0.1:8001", "[::1]:8001", "app.localhost", None, ""])
    def test_local_hosts(self, host):
        assert ac.host_header_is_local(host) is True

    @pytest.mark.parametrize("host", ["evil.example", "evil.example:8001", "192.168.1.20:8001"])
    def test_rebinding_hosts_rejected(self, host):
        assert ac.host_header_is_local(host) is False

    def test_extra_allowed(self):
        assert ac.host_header_is_local("ledger.lan:8001", ["ledger.lan"]) is True


class TestOrigin:
    def test_no_origin_allowed(self):
        assert ac.origin_allowed(None, "localhost:8001") is True

    def test_same_origin_allowed(self):
        assert ac.origin_allowed("http://localhost:8001", "localhost:8001") is True

    def test_foreign_origin_rejected(self):
        assert ac.origin_allowed("https://evil.example", "localhost:8001") is False
        assert ac.origin_allowed("null", "localhost:8001") is False

    def test_configured_origin_allowed(self):
        assert ac.origin_allowed("https://tools.example/", "localhost:8001", ["https://tools.example"]) is True


def test_networks_and_ipv4_mapped():
    nets = ac.parse_networks(["192.168.1.0/24", "not-a-cidr", "fd00::/8"])
    assert len(nets) == 2
    assert ac.ip_in_networks("::ffff:192.168.1.7", nets) is True
    assert ac.ip_in_networks("fd00::5", nets) is True
    assert ac.ip_in_networks("10.0.0.1", nets) is False


# ---------------------------------------------------------------------------
# App integration (needs fastapi + httpx)
# ---------------------------------------------------------------------------

def _client(app, client_host=None, base_url="http://127.0.0.1:8001"):
    from fastapi.testclient import TestClient

    if client_host is None:
        return TestClient(app, base_url=base_url)
    if "client" not in inspect.signature(TestClient.__init__).parameters:
        pytest.skip("this Starlette TestClient cannot set the client address")
    return TestClient(app, base_url=base_url, client=(client_host, 50000))


@pytest.fixture
def gw_no_auth(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    import gateway

    monkeypatch.setattr(gateway, "_GW_API_KEY", "")
    monkeypatch.setattr(gateway, "_get_authorized_networks", lambda: [])
    monkeypatch.delenv("SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE", raising=False)
    monkeypatch.delenv("SMART_AGENT_LEDGER_ALLOWED_HOSTS", raising=False)
    return gateway


def test_no_auth_non_loopback_client_gets_403(gw_no_auth, monkeypatch):
    # "testclient" is not an IP, so with no extra names it is a non-loopback peer.
    monkeypatch.setattr(gw_no_auth, "_EXTRA_LOCAL_NAMES", frozenset())
    for method, path in [("get", "/config"), ("post", "/v1/chat/completions"), ("get", "/admin/nodes")]:
        response = getattr(_client(gw_no_auth.app), method)(path)
        assert response.status_code == 403, path
        assert "GATEWAY_API_KEY" in response.json()["detail"]
        assert "authorized_networks" in response.json()["detail"]


def test_no_auth_lan_ip_gets_403(gw_no_auth, monkeypatch):
    monkeypatch.setattr(gw_no_auth, "_EXTRA_LOCAL_NAMES", frozenset())
    response = _client(gw_no_auth.app, "192.168.1.20").get("/config")
    assert response.status_code == 403
    assert response.json()["client_ip"] == "192.168.1.20"


def test_no_auth_loopback_client_allowed(gw_no_auth, monkeypatch):
    monkeypatch.setattr(gw_no_auth, "_EXTRA_LOCAL_NAMES", frozenset())
    assert _client(gw_no_auth.app, "127.0.0.1").get("/config").status_code == 200


def test_no_auth_testclient_alias_allowed(gw_no_auth):
    # conftest registers TestClient's placeholder names as local.
    assert _client(gw_no_auth.app).get("/config").status_code == 200


def test_no_auth_trusted_docker_bridge_allowed(gw_no_auth, monkeypatch):
    monkeypatch.setattr(gw_no_auth, "_EXTRA_LOCAL_NAMES", frozenset())
    monkeypatch.setenv("SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE", "172.17.0.1")
    assert _client(gw_no_auth.app, "172.17.0.1").get("/config").status_code == 200
    assert _client(gw_no_auth.app, "172.17.0.9").get("/config").status_code == 403


def test_health_always_open(gw_no_auth, monkeypatch):
    monkeypatch.setattr(gw_no_auth, "_EXTRA_LOCAL_NAMES", frozenset())
    assert _client(gw_no_auth.app).get("/health").status_code == 200
    monkeypatch.setattr(gw_no_auth, "_GW_API_KEY", "secret")
    assert _client(gw_no_auth.app).get("/health").status_code == 200


def test_dns_rebinding_host_rejected(gw_no_auth):
    response = _client(gw_no_auth.app).get("/config", headers={"host": "evil.example:8001"})
    assert response.status_code == 403
    assert "Host" in response.json()["detail"]


def test_cors_header_absent_for_random_origin(gw_no_auth):
    client = _client(gw_no_auth.app)
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}
    preflight = client.options(
        "/config",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in {k.lower() for k in preflight.headers}


def test_cross_origin_post_rejected(gw_no_auth):
    response = _client(gw_no_auth.app).post(
        "/config/routing", json={}, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403
    assert "cross-origin" in response.json()["detail"]


def test_api_key_required_when_configured(gw_no_auth, monkeypatch):
    monkeypatch.setattr(gw_no_auth, "_GW_API_KEY", "s3cret")
    client = _client(gw_no_auth.app)
    assert client.get("/config").status_code == 401
    assert client.get("/config", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/config", headers={"X-API-Key": "s3cret"}).status_code == 200


def test_gateway_uses_constant_time_compare():
    source = open("gateway.py", encoding="utf-8").read()
    assert "hmac.compare_digest" in source
    assert 'allow_origins=["*"]' not in source


# ---------------------------------------------------------------------------
# Collector (agent_ledger_server.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def collector(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    import agent_ledger_server

    monkeypatch.delenv("SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS", raising=False)
    monkeypatch.delenv("SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE", raising=False)
    monkeypatch.setattr(agent_ledger_server, "READONLY_LEDGER_DISK_CACHE_DIR", tmp_path)
    monkeypatch.setattr(agent_ledger_server, "build_agent_ledger", lambda days, limit: {"totals": {}, "recent_sessions": []})
    agent_ledger_server.READONLY_LEDGER_CACHE.clear()
    agent_ledger_server.READONLY_LEDGER_TASKS.clear()
    yield agent_ledger_server
    agent_ledger_server.READONLY_LEDGER_CACHE.clear()
    agent_ledger_server.READONLY_LEDGER_TASKS.clear()


def test_collector_rejects_remote_by_default(collector, monkeypatch):
    monkeypatch.setattr(collector, "_EXTRA_LOCAL_NAMES", frozenset())
    client = _client(collector.app, base_url="http://127.0.0.1:8002")
    assert client.get("/health").status_code == 200
    response = client.get("/agent-ledger?days=1&limit=1")
    assert response.status_code == 403
    assert "SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS" in response.json()["detail"]


def test_collector_allows_loopback(collector):
    assert _client(collector.app, base_url="http://127.0.0.1:8002").get("/agent-ledger?days=1&limit=1").status_code == 200


def test_collector_allows_configured_network(collector, monkeypatch):
    monkeypatch.setattr(collector, "_EXTRA_LOCAL_NAMES", frozenset())
    monkeypatch.setenv("SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS", "100.64.0.0/10")
    ok = _client(collector.app, "100.101.102.103", base_url="http://100.90.1.1:8002")
    assert ok.get("/agent-ledger?days=1&limit=1").status_code == 200
    denied = _client(collector.app, "192.168.1.9", base_url="http://100.90.1.1:8002")
    assert denied.get("/agent-ledger?days=1&limit=1").status_code == 403


def test_collector_unit_logic(monkeypatch):
    pytest.importorskip("fastapi")
    import agent_ledger_server

    monkeypatch.setattr(agent_ledger_server, "_EXTRA_LOCAL_NAMES", frozenset())
    monkeypatch.delenv("SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS", raising=False)
    assert agent_ledger_server._client_allowed("127.0.0.1", "127.0.0.1:8002") is True
    assert agent_ledger_server._client_allowed("127.0.0.1", "evil.example:8002") is False
    assert agent_ledger_server._client_allowed("10.1.2.3", "10.0.0.2:8002") is False
    monkeypatch.setenv("SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS", "10.0.0.0/8")
    assert agent_ledger_server._client_allowed("10.1.2.3", "10.0.0.2:8002") is True


def test_default_bind_is_loopback():
    run_sh = open("run.sh", encoding="utf-8").read()
    compose = open("docker-compose.yml", encoding="utf-8").read()
    plist = open("deploy/com.smart-agent-ledger.agent-ledger.plist.example", encoding="utf-8").read()
    install = open("deploy/install-agent-ledger-readonly-launchd.sh", encoding="utf-8").read()
    assert 'GATEWAY_HOST="${GATEWAY_HOST:-127.0.0.1}"' in run_sh
    assert "--host 0.0.0.0" not in run_sh
    assert "${SMART_AGENT_LEDGER_BIND:-127.0.0.1}:" in compose
    assert "--host 0.0.0.0" not in plist
    assert 'BIND_HOST="127.0.0.1"' in install
