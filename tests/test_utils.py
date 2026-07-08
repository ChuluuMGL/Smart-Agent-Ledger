"""测试 utils.py 中的公共工具函数。"""
import datetime as dt
import pathlib
import tempfile

import pytest

from utils import (
    dedupe_session_rows,
    epoch_from_iso,
    iso_from_epoch,
    iso_from_ms,
    load_env_file,
    mtime_cached,
    parse_iso,
    safe_float,
    safe_int,
    safe_read_json,
    utc_now,
)


# ── safe_int ────────────────────────────────────────────────────────────────


class TestDedupeSessionRows:
    def test_keeps_highest_cumulative_snapshot(self):
        rows = [
            {"agent": "Codex", "session_id": "s1", "total_tokens": 100, "ended_at": "2026-06-10T00:00:00+00:00"},
            {"agent": "Codex", "session_id": "s1", "total_tokens": 250, "ended_at": "2026-06-11T00:00:00+00:00"},
            {"agent": "Claude Code", "session_id": "s1", "total_tokens": 80, "ended_at": "2026-06-12T00:00:00+00:00"},
        ]

        result = dedupe_session_rows(rows)

        assert len(result) == 2
        codex = next(row for row in result if row["agent"] == "Codex")
        assert codex["total_tokens"] == 250

    def test_keeps_request_level_rows(self):
        rows = [
            {"agent": "n8n", "session_id": "workflow-run", "total_tokens": 100, "token_status": "n8n_reported"},
            {"agent": "n8n", "session_id": "workflow-run", "total_tokens": 120, "token_status": "n8n_reported"},
        ]

        assert len(dedupe_session_rows(rows)) == 2


class TestSafeInt:
    def test_normal_integer(self):
        assert safe_int(42) == 42

    def test_string_integer(self):
        assert safe_int("123") == 123

    def test_none_returns_default(self):
        assert safe_int(None) == 0
        assert safe_int(None, default=-1) == -1

    def test_empty_string_returns_default(self):
        assert safe_int("") == 0

    def test_float_truncates(self):
        assert safe_int(3.7) == 3

    def test_invalid_string_returns_default(self):
        assert safe_int("abc") == 0

    def test_custom_default(self):
        assert safe_int("bad", default=99) == 99


# ── safe_float ──────────────────────────────────────────────────────────────


class TestSafeFloat:
    def test_normal_float(self):
        assert safe_float(3.14) == pytest.approx(3.14)

    def test_string_float(self):
        assert safe_float("2.5") == pytest.approx(2.5)

    def test_integer_value(self):
        assert safe_float(10) == 10.0

    def test_none_returns_none(self):
        assert safe_float(None) is None

    def test_empty_string_returns_none(self):
        assert safe_float("") is None

    def test_invalid_string_returns_none(self):
        assert safe_float("xyz") is None


# ── utc_now ─────────────────────────────────────────────────────────────────


class TestUtcNow:
    def test_returns_aware_datetime(self):
        result = utc_now()
        assert result.tzinfo is not None

    def test_is_utc(self):
        result = utc_now()
        assert result.utcoffset() == dt.timedelta(0)


# ── parse_iso ───────────────────────────────────────────────────────────────


class TestParseIso:
    def test_standard_iso(self):
        result = parse_iso("2026-06-08T12:00:00+08:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 6
        assert result.day == 8

    def test_utc_z_suffix(self):
        result = parse_iso("2026-06-08T12:00:00Z")
        assert result is not None
        assert result.utcoffset() == dt.timedelta(0)

    def test_none_returns_none(self):
        assert parse_iso(None) is None

    def test_empty_string_returns_none(self):
        assert parse_iso("") is None

    def test_invalid_returns_none(self):
        assert parse_iso("not-a-date") is None


# ── iso_from_epoch ──────────────────────────────────────────────────────────


class TestIsoFromEpoch:
    def test_known_epoch(self):
        # 2026-01-01T00:00:00+00:00 → epoch 1767225600
        result = iso_from_epoch(1767225600)
        assert result is not None
        assert "2026-01-01" in result

    def test_none_returns_none(self):
        assert iso_from_epoch(None) is None

    def test_invalid_returns_none(self):
        assert iso_from_epoch("bad") is None


# ── iso_from_ms ─────────────────────────────────────────────────────────────


class TestIsoFromMs:
    def test_millisecond_epoch(self):
        # 毫秒级 epoch（> 10_000_000_000 自动除以 1000）
        ms = 1767225600_000
        result = iso_from_ms(ms)
        assert result is not None
        assert "2026-01-01" in result

    def test_second_epoch(self):
        result = iso_from_ms(1767225600)
        assert result is not None
        assert "2026-01-01" in result

    def test_none_returns_none(self):
        assert iso_from_ms(None) is None


# ── epoch_from_iso ──────────────────────────────────────────────────────────


class TestEpochFromIso:
    def test_roundtrip(self):
        original = 1767225600.0
        iso = iso_from_epoch(original)
        assert iso is not None
        result = epoch_from_iso(iso)
        assert result is not None
        assert abs(result - original) < 1.0

    def test_none_returns_none(self):
        assert epoch_from_iso(None) is None

    def test_invalid_returns_none(self):
        assert epoch_from_iso("garbage") is None


# ── load_env_file ───────────────────────────────────────────────────────────


class TestLoadEnvFile:
    def test_basic_key_value(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("API_KEY=abc123\n")
            f.write("PORT=8080\n")
            f.flush()
            result = load_env_file(pathlib.Path(f.name))
        assert result["API_KEY"] == "abc123"
        assert result["PORT"] == "8080"

    def test_comments_stripped(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("KEY=value # inline comment\n")
            f.write("# full line comment\n")
            f.flush()
            result = load_env_file(pathlib.Path(f.name))
        assert result["KEY"] == "value"
        assert "# full line comment" not in result

    def test_quoted_values(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write('KEY="double quoted"\n')
            f.write("KEY2='single quoted'\n")
            f.flush()
            result = load_env_file(pathlib.Path(f.name))
        assert result["KEY"] == "double quoted"
        assert result["KEY2"] == "single quoted"

    def test_missing_file_returns_empty(self):
        result = load_env_file(pathlib.Path("/nonexistent/file.env"))
        assert result == {}


# ── safe_read_json ──────────────────────────────────────────────────────────


class TestSafeReadJson:
    def test_valid_json_file(self, tmp_path):
        p = tmp_path / "test.json"
        p.write_text('{"key": "value", "num": 42}')
        result = safe_read_json(p)
        assert result == {"key": "value", "num": 42}

    def test_missing_file_returns_default(self, tmp_path):
        result = safe_read_json(tmp_path / "gone.json", default={"fallback": True})
        assert result == {"fallback": True}

    def test_missing_file_default_none(self, tmp_path):
        result = safe_read_json(tmp_path / "gone.json")
        assert result is None

    def test_invalid_json_returns_default(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{{")
        result = safe_read_json(p, default={})
        assert result == {}

    def test_empty_file_returns_default(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text("")
        result = safe_read_json(p, default="empty")
        assert result == "empty"

    def test_accepts_string_path(self, tmp_path):
        p = tmp_path / "strpath.json"
        p.write_text('{"ok": true}')
        result = safe_read_json(str(p))
        assert result == {"ok": True}


# ── mtime_cached ────────────────────────────────────────────────────────────


class TestMtimeCached:
    def test_first_call_loads(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"v": 1}')
        cache = {"_mtime": 0, "data": None}
        result = mtime_cached(p, cache, lambda: safe_read_json(p, default={}))
        assert result == {"v": 1}
        assert cache["data"] == {"v": 1}
        assert cache["_mtime"] > 0

    def test_returns_cache_when_unchanged(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"v": 1}')
        cache = {"_mtime": 0, "data": None}
        call_count = 0

        def loader():
            nonlocal call_count
            call_count += 1
            return safe_read_json(p, default={})

        r1 = mtime_cached(p, cache, loader)
        assert call_count == 1
        r2 = mtime_cached(p, cache, loader)
        assert call_count == 1  # 没有再次调用 loader
        assert r1 == r2

    def test_reloads_when_file_changes(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"v": 1}')
        cache = {"_mtime": 0, "data": None}
        r1 = mtime_cached(p, cache, lambda: safe_read_json(p, default={}))
        assert r1 == {"v": 1}

        # 修改文件
        p.write_text('{"v": 2}')
        r2 = mtime_cached(p, cache, lambda: safe_read_json(p, default={}))
        assert r2 == {"v": 2}

    def test_missing_file_mtime_zero(self, tmp_path):
        p = tmp_path / "gone.json"
        cache = {"_mtime": 0, "data": None}
        result = mtime_cached(p, cache, lambda: {"empty": True})
        assert result == {"empty": True}

    def test_prepopulated_cache_used(self, tmp_path):
        """如果 cache 有 data 且 mtime 匹配, loader 不被调用。"""
        p = tmp_path / "config.json"
        p.write_text('{"v": 1}')
        mtime = p.stat().st_mtime
        cache = {"_mtime": mtime, "data": {"cached": True}}
        result = mtime_cached(p, cache, lambda: {"should_not": "be_called"})
        assert result == {"cached": True}

    def test_empty_lines_ignored(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("\n\nKEY=val\n\n")
            f.flush()
            result = load_env_file(pathlib.Path(f.name))
        assert result == {"KEY": "val"}
