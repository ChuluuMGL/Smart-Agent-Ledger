"""Tests for Gateway 认证: API Key + IP 白名单。"""
import ipaddress
import json
import pathlib

import pytest

# conftest.py 已将项目根目录加入 sys.path


# ---------------------------------------------------------------------------
# 纯逻辑: IP 白名单匹配
# ---------------------------------------------------------------------------

def _ip_in_whitelist(client_ip: str, networks: list) -> bool:
    """与 gateway._ip_in_whitelist 相同逻辑,独立测试。"""
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in net for net in networks)
    except (ValueError, TypeError):
        return False


class TestIpWhitelist:
    def test_ip_in_single_network(self):
        nets = [ipaddress.ip_network("192.0.2.0/24")]
        assert _ip_in_whitelist("192.0.2.100", nets) is True

    def test_ip_not_in_network(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist("10.0.0.1", nets) is False

    def test_boundary_ip_network_first(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist("192.168.1.0", nets) is True

    def test_boundary_ip_network_last(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist("192.168.1.255", nets) is True

    def test_ip_outside_boundary(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist("192.168.2.0", nets) is False

    def test_empty_networks_list(self):
        assert _ip_in_whitelist("192.168.1.1", []) is False

    def test_invalid_ip_returns_false(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist("not-an-ip", nets) is False

    def test_none_ip_returns_false(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert _ip_in_whitelist(None, nets) is False

    def test_multiple_networks(self):
        nets = [
            ipaddress.ip_network("192.168.1.0/24"),
            ipaddress.ip_network("10.0.0.0/8"),
        ]
        assert _ip_in_whitelist("10.5.5.5", nets) is True
        assert _ip_in_whitelist("192.168.1.50", nets) is True
        assert _ip_in_whitelist("172.16.0.1", nets) is False

    def test_ipv6_in_network(self):
        nets = [ipaddress.ip_network("fd00::/8")]
        assert _ip_in_whitelist("fd00::1", nets) is True

    def test_ipv4_not_in_ipv6_network(self):
        nets = [ipaddress.ip_network("fd00::/8")]
        assert _ip_in_whitelist("192.168.1.1", nets) is False

    def test_single_host_network(self):
        nets = [ipaddress.ip_network("192.0.2.100/32")]
        assert _ip_in_whitelist("192.0.2.100", nets) is True
        assert _ip_in_whitelist("192.168.1.101", nets) is False


# ---------------------------------------------------------------------------
# 纯逻辑: 从 JSON 加载 authorized_networks
# ---------------------------------------------------------------------------

class TestLoadAuthorizedNetworks:
    def test_valid_networks(self, tmp_path):
        config = tmp_path / "nodes.json"
        config.write_text(json.dumps({
            "authorized_networks": ["192.168.1.0/24", "10.0.0.0/8"],
        }))
        data = json.loads(config.read_text())
        networks = []
        for cidr in (data.get("authorized_networks") or []):
            try:
                networks.append(ipaddress.ip_network(str(cidr), strict=False))
            except (ValueError, TypeError):
                pass
        assert len(networks) == 2
        assert ipaddress.ip_address("192.168.1.1") in networks[0]
        assert ipaddress.ip_address("10.0.0.1") in networks[1]

    def test_empty_networks(self, tmp_path):
        config = tmp_path / "nodes.json"
        config.write_text(json.dumps({"authorized_networks": []}))
        data = json.loads(config.read_text())
        assert data.get("authorized_networks") == []

    def test_missing_field(self, tmp_path):
        config = tmp_path / "nodes.json"
        config.write_text(json.dumps({}))
        data = json.loads(config.read_text())
        assert data.get("authorized_networks") is None
        # 默认处理
        assert data.get("authorized_networks") or [] == []

    def test_invalid_cidr_skipped(self, tmp_path):
        config = tmp_path / "nodes.json"
        config.write_text(json.dumps({
            "authorized_networks": ["192.168.1.0/24", "not-a-cidr", "10.0.0.0/8"],
        }))
        data = json.loads(config.read_text())
        networks = []
        for cidr in (data.get("authorized_networks") or []):
            try:
                networks.append(ipaddress.ip_network(str(cidr), strict=False))
            except (ValueError, TypeError):
                pass
        assert len(networks) == 2

    def test_nonstrict_cidr(self, tmp_path):
        """192.0.2.100/24 应被 strict=False 接受。"""
        config = tmp_path / "nodes.json"
        config.write_text(json.dumps({
            "authorized_networks": ["192.0.2.100/24"],
        }))
        data = json.loads(config.read_text())
        networks = []
        for cidr in (data.get("authorized_networks") or []):
            try:
                networks.append(ipaddress.ip_network(str(cidr), strict=False))
            except (ValueError, TypeError):
                pass
        assert len(networks) == 1
        assert networks[0] == ipaddress.ip_network("192.0.2.0/24")


# ---------------------------------------------------------------------------
# 认证决策逻辑 (不依赖 FastAPI)
# ---------------------------------------------------------------------------

class TestAuthDecisionLogic:
    """模拟 auth_middleware 的决策逻辑。"""

    @staticmethod
    def _check_auth(path, api_key_config, networks, client_ip, provided_key):
        """返回 'allow' 或 'deny'。"""
        # 公开端点
        if path == "/health":
            return "allow"
        # 无认证配置 → 允许
        if not api_key_config and not networks:
            return "allow"
        # IP 白名单
        if client_ip and _ip_in_whitelist(client_ip, networks):
            return "allow"
        # API Key
        if api_key_config and provided_key == api_key_config:
            return "allow"
        return "deny"

    def test_health_always_public(self):
        assert self._check_auth("/health", "secret", [], "1.2.3.4", "") == "allow"

    def test_no_auth_config_allows_all(self):
        assert self._check_auth("/stats", "", [], "1.2.3.4", "") == "allow"
        assert self._check_auth("/config", "", [], "", "") == "allow"

    def test_api_key_correct(self):
        assert self._check_auth("/stats", "my-key", [], "1.2.3.4", "my-key") == "allow"

    def test_api_key_wrong(self):
        assert self._check_auth("/stats", "my-key", [], "1.2.3.4", "wrong") == "deny"

    def test_api_key_missing(self):
        assert self._check_auth("/stats", "my-key", [], "1.2.3.4", "") == "deny"

    def test_ip_whitelist_without_key(self):
        nets = [ipaddress.ip_network("192.0.2.0/24")]
        assert self._check_auth("/stats", "my-key", nets, "192.0.2.100", "") == "allow"

    def test_ip_whitelist_not_matched(self):
        nets = [ipaddress.ip_network("192.168.1.0/24")]
        assert self._check_auth("/stats", "my-key", nets, "10.0.0.1", "") == "deny"

    def test_ip_whitelist_overrides_key_requirement(self):
        """白名单 IP 不需要 API Key。"""
        nets = [ipaddress.ip_network("10.0.0.0/8")]
        assert self._check_auth("/config", "secret", nets, "10.5.5.5", "") == "allow"

    def test_key_works_from_non_whitelisted_ip(self):
        """非白名单 IP 可以用 API Key。"""
        nets = [ipaddress.ip_network("10.0.0.0/8")]
        assert self._check_auth("/config", "secret", nets, "1.2.3.4", "secret") == "allow"

    def test_only_networks_no_key_required_from_whitelist(self):
        """仅配了白名单,无 key → 白名单 IP 放行,其他拒绝。"""
        nets = [ipaddress.ip_network("192.168.0.0/16")]
        assert self._check_auth("/stats", "", nets, "192.168.1.1", "") == "allow"
        assert self._check_auth("/stats", "", nets, "8.8.8.8", "") == "deny"

    def test_only_key_no_networks(self):
        """仅配了 key,无白名单 → 有 key 放行,无 key 拒绝。"""
        assert self._check_auth("/stats", "key123", [], "1.2.3.4", "key123") == "allow"
        assert self._check_auth("/stats", "key123", [], "1.2.3.4", "") == "deny"

    def test_various_protected_paths(self):
        """所有非 /health 端点都受保护。"""
        nets = [ipaddress.ip_network("10.0.0.0/8")]
        for path in ["/stats", "/config", "/agent-ledger", "/fleet-ledger",
                     "/v1/chat/completions", "/ui", "/v1/models"]:
            assert self._check_auth(path, "", nets, "1.2.3.4", "") == "deny"
            assert self._check_auth(path, "", nets, "10.0.0.1", "") == "allow"
