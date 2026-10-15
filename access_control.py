"""Network access helpers shared by gateway.py and agent_ledger_server.py.

Pure Python (no FastAPI import) so the decision logic can be unit tested
without a running server.

Default policy
--------------
* Services bind to 127.0.0.1 unless told otherwise.
* When no authentication is configured, only loopback clients
  (127.0.0.0/8, ::1) are served, and the HTTP Host header must name a
  loopback host (blocks DNS-rebinding from a web page).
* Inside Docker, requests that arrive through a published loopback port come
  from the container's default gateway (the Docker bridge). Setting
  ``SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE=1`` treats that single gateway IP
  as local. It may also be a comma-separated list of explicit IPs.
* Cross-origin browser access is off unless origins are listed in
  ``SMART_AGENT_LEDGER_CORS_ORIGINS``.
"""
from __future__ import annotations

import ipaddress
import os
import pathlib
from typing import Dict, FrozenSet, Iterable, List, Optional, Union
from urllib.parse import urlsplit

IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]

LOOPBACK_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
)
LOCAL_HOSTNAMES = frozenset({"localhost"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "auto"})
_FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})


def env_list(name: str) -> List[str]:
    """Read a comma-separated environment variable into a list of stripped values."""
    return [part.strip() for part in os.getenv(name, "").split(",") if part.strip()]


def parse_ip(value: object) -> Optional[IPAddress]:
    """Parse an IP address; IPv4-mapped IPv6 (::ffff:a.b.c.d) is unwrapped."""
    if value is None:
        return None
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    text = text.split("%", 1)[0]  # drop IPv6 zone id
    try:
        addr = ipaddress.ip_address(text)
    except ValueError:
        return None
    mapped = getattr(addr, "ipv4_mapped", None)
    return mapped if mapped is not None else addr


def parse_networks(values: Iterable[object]) -> List[IPNetwork]:
    networks: List[IPNetwork] = []
    for value in values:
        try:
            networks.append(ipaddress.ip_network(str(value).strip(), strict=False))
        except (ValueError, TypeError):
            continue
    return networks


def ip_in_networks(client_ip: object, networks: Iterable[IPNetwork]) -> bool:
    addr = parse_ip(client_ip)
    if addr is None:
        return False
    return any(addr.version == net.version and addr in net for net in networks)


def is_loopback_ip(client_ip: object) -> bool:
    return ip_in_networks(client_ip, LOOPBACK_NETWORKS)


def docker_default_gateway(route_path: Union[str, pathlib.Path] = "/proc/net/route") -> Optional[str]:
    """Return the IPv4 default gateway from /proc/net/route (Linux/containers)."""
    try:
        lines = pathlib.Path(route_path).read_text(encoding="ascii", errors="ignore").splitlines()
    except OSError:
        return None
    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 3 or fields[1] != "00000000":
            continue
        try:
            raw = int(fields[2], 16)
            if raw == 0:
                continue
            return str(ipaddress.IPv4Address(raw.to_bytes(4, "little")))
        except (ValueError, OverflowError):
            return None
    return None


_BRIDGE_CACHE: Dict[str, FrozenSet[str]] = {}


def trusted_docker_bridge_ips(
    setting: Optional[str] = None,
    route_path: Union[str, pathlib.Path] = "/proc/net/route",
) -> FrozenSet[str]:
    """IPs treated as local because they are the Docker bridge gateway.

    ``setting`` defaults to ``SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE``:
    empty/0/false -> nothing; 1/true/auto -> the container's default gateway;
    otherwise a comma-separated list of explicit IPs.
    """
    raw = (os.getenv("SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE", "") if setting is None else setting).strip()
    if raw.lower() in _FALSE_VALUES:
        return frozenset()
    cache_key = f"{raw}|{route_path}"
    cached = _BRIDGE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if raw.lower() in _TRUE_VALUES:
        gateway_ip = docker_default_gateway(route_path)
        result = frozenset({gateway_ip} if gateway_ip else ())
    else:
        result = frozenset(str(addr) for addr in (parse_ip(p) for p in raw.split(",")) if addr is not None)
    _BRIDGE_CACHE[cache_key] = result
    return result


def is_local_client(
    client_host: object,
    extra_local_names: Iterable[str] = (),
    bridge_ips: Optional[Iterable[str]] = None,
) -> bool:
    """True for loopback clients (and the trusted Docker bridge gateway, if enabled)."""
    if client_host is None:
        return False
    if str(client_host) in set(extra_local_names):
        return True
    addr = parse_ip(client_host)
    if addr is None:
        return False
    if is_loopback_ip(addr):
        return True
    trusted = trusted_docker_bridge_ips() if bridge_ips is None else frozenset(bridge_ips)
    return str(addr) in trusted


def host_header_hostname(host_header: Optional[str]) -> str:
    if not host_header:
        return ""
    try:
        return (urlsplit("//" + host_header.strip()).hostname or "").lower()
    except ValueError:
        return ""


def host_header_is_local(host_header: Optional[str], extra_allowed_hosts: Iterable[str] = ()) -> bool:
    """True when the Host header names a loopback host (DNS-rebinding guard).

    A missing Host header (HTTP/1.0 clients) is accepted: browsers always send one.
    """
    if not host_header:
        return True
    hostname = host_header_hostname(host_header)
    if not hostname:
        return False
    allowed = {h.strip().lower() for h in extra_allowed_hosts if h and h.strip()}
    if hostname in LOCAL_HOSTNAMES or hostname.endswith(".localhost") or hostname in allowed:
        return True
    return is_loopback_ip(hostname)


def normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/").lower()


def origin_allowed(origin: Optional[str], host_header: Optional[str], allowed_origins: Iterable[str] = ()) -> bool:
    """CSRF guard for state-changing requests.

    Requests without an Origin header (curl, SDKs, agents) are allowed.
    Browser requests are allowed when same-origin or explicitly configured.
    """
    if origin is None:
        return True
    normalized = normalize_origin(origin)
    allowed = {normalize_origin(o) for o in allowed_origins if o}
    if "*" in allowed or normalized in allowed:
        return True
    if normalized == "null" or not host_header:
        return False
    try:
        netloc = urlsplit(normalized).netloc
    except ValueError:
        return False
    return bool(netloc) and netloc == host_header.strip().lower()
