"""测试模型单价加载和费用估算功能。"""
import json
import pathlib
import pytest

# 项目根目录
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

from utils import load_model_pricing, estimate_cost_usd, safe_int


class TestLoadModelPricing:
    """测试 load_model_pricing 加载和缓存。"""

    def test_load_from_real_file(self):
        pricing = load_model_pricing(DATA_DIR)
        assert "models" in pricing
        assert "alias_map" in pricing
        assert "cny_to_usd" in pricing
        assert len(pricing["models"]) > 0
        assert len(pricing["alias_map"]) > 0

    def test_load_missing_dir_returns_empty(self, tmp_path):
        # 直接验证函数对缺失路径的容错（不依赖缓存状态）
        import utils as _u
        old_cache = dict(_u._PRICING_MTIME_CACHE)
        try:
            _u._PRICING_MTIME_CACHE["data"] = None
            _u._PRICING_MTIME_CACHE["_mtime"] = 0
            pricing = load_model_pricing(tmp_path / "nonexistent")
            assert pricing["models"] == {}
            assert pricing["alias_map"] == {}
        finally:
            _u._PRICING_MTIME_CACHE.update(old_cache)

    def test_cny_to_usd_is_float(self):
        pricing = load_model_pricing(DATA_DIR)
        assert isinstance(pricing["cny_to_usd"], float)
        assert pricing["cny_to_usd"] > 0

    def test_all_models_have_required_fields(self):
        pricing = load_model_pricing(DATA_DIR)
        for name, entry in pricing["models"].items():
            assert "input_per_million" in entry, f"{name} missing input_per_million"
            assert "output_per_million" in entry, f"{name} missing output_per_million"
            assert "currency" in entry, f"{name} missing currency"

    def test_alias_map_covers_all_aliases(self):
        pricing = load_model_pricing(DATA_DIR)
        for name, entry in pricing["models"].items():
            # canonical normalized should be in alias_map
            for alias in entry.get("aliases", []):
                norm = alias.strip().lower().replace("_", "-")
                assert norm in pricing["alias_map"], f"alias '{alias}' (norm '{norm}') not in alias_map"


class TestEstimateCostUsd:
    """测试 estimate_cost_usd 费用计算。"""

    @pytest.fixture
    def pricing(self):
        return load_model_pricing(DATA_DIR)

    def test_known_model_1m_tokens(self, pricing):
        """deepseek-chat: 1M input + 1M output = CNY 1.37 × 0.14 = $0.1918"""
        cost = estimate_cost_usd("deepseek-chat", 1_000_000, 1_000_000, pricing)
        assert cost is not None
        assert abs(cost - 0.1918) < 0.001

    def test_alias_resolution(self, pricing):
        """下划线 alias 也能匹配。"""
        cost = estimate_cost_usd("deepseek_chat", 100_000, 50_000, pricing)
        assert cost is not None
        assert cost > 0

    def test_case_insensitive(self, pricing):
        """大小写不敏感。"""
        cost = estimate_cost_usd("DeepSeek-Chat", 1_000_000, 1_000_000, pricing)
        assert cost is not None
        cost2 = estimate_cost_usd("deepseek-chat", 1_000_000, 1_000_000, pricing)
        assert cost == cost2

    def test_free_model_returns_zero(self, pricing):
        """免费模型返回 0.0。"""
        cost = estimate_cost_usd("codeqwen:7b", 1_000_000, 1_000_000, pricing)
        assert cost == 0.0

    def test_unknown_model_returns_none(self, pricing):
        cost = estimate_cost_usd("nonexistent-model-xyz", 1_000_000, 1_000_000, pricing)
        assert cost is None

    def test_none_model_returns_none(self, pricing):
        cost = estimate_cost_usd(None, 1_000_000, 1_000_000, pricing)
        assert cost is None

    def test_empty_model_returns_none(self, pricing):
        cost = estimate_cost_usd("", 1_000_000, 1_000_000, pricing)
        assert cost is None

    def test_zero_tokens_returns_zero(self, pricing):
        cost = estimate_cost_usd("deepseek-chat", 0, 0, pricing)
        assert cost == 0.0

    def test_cny_model_converted_to_usd(self, pricing):
        """CNY 模型应该按汇率转换。"""
        # deepseek-chat: input CNY 0.27/M, output CNY 1.10/M
        cost = estimate_cost_usd("deepseek-chat", 1_000_000, 0, pricing)
        expected = 0.27 * pricing["cny_to_usd"]
        assert abs(cost - expected) < 0.001

    def test_usd_model_not_converted(self, pricing):
        """USD 模型不应被汇率影响。"""
        # claude-sonnet-4: input $3/M
        cost = estimate_cost_usd("claude-sonnet-4-20250514", 1_000_000, 0, pricing)
        assert abs(cost - 3.0) < 0.01

    def test_glm5_alias(self, pricing):
        """glm-5.1 应该匹配到 glm-5。"""
        cost = estimate_cost_usd("glm-5.1", 1_000_000, 0, pricing)
        assert cost is not None
        assert cost > 0

    def test_minimax_case(self, pricing):
        """MiniMax-M2.7 大小写 alias。"""
        cost = estimate_cost_usd("MiniMax-M2.7", 1_000_000, 1_000_000, pricing)
        assert cost is not None
        assert cost > 0

    def test_small_token_count(self, pricing):
        """极少 token 也应返回合理的极小值。"""
        cost = estimate_cost_usd("deepseek-chat", 100, 100, pricing)
        assert cost is not None
        assert cost > 0
        assert cost < 0.01


class TestEstimateMissingCosts:
    """测试 agent_ledger._estimate_missing_costs 后处理。"""

    def test_fills_missing_cost(self):
        from agent_ledger import _estimate_missing_costs
        pricing = load_model_pricing(DATA_DIR)
        rows = [{
            "agent": "Test",
            "model": "deepseek-chat",
            "input_tokens": 100_000,
            "output_tokens": 50_000,
            "total_tokens": 150_000,
            "estimated_cost_usd": None,
            "actual_cost_usd": None,
            "cost_status": "local_token_estimate_only",
        }]
        _estimate_missing_costs(rows, pricing)
        assert rows[0]["estimated_cost_usd"] is not None
        assert rows[0]["estimated_cost_usd"] > 0
        assert rows[0]["cost_status"] == "pricing_table_estimate"

    def test_does_not_overwrite_known_cost(self):
        from agent_ledger import _estimate_missing_costs
        pricing = load_model_pricing(DATA_DIR)
        rows = [{
            "agent": "Hermes",
            "model": "minimax-m3",
            "input_tokens": 100_000,
            "output_tokens": 50_000,
            "total_tokens": 150_000,
            "estimated_cost_usd": 0.05,
            "actual_cost_usd": None,
            "cost_status": "hermes_state_db",
        }]
        _estimate_missing_costs(rows, pricing)
        # 应保持原值不被覆盖
        assert rows[0]["estimated_cost_usd"] == 0.05
        assert rows[0]["cost_status"] == "hermes_state_db"

    def test_skips_no_model(self):
        from agent_ledger import _estimate_missing_costs
        pricing = load_model_pricing(DATA_DIR)
        rows = [{
            "agent": "Cursor",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 100_000,
            "estimated_cost_usd": None,
            "cost_status": "not_available",
        }]
        _estimate_missing_costs(rows, pricing)
        assert rows[0]["estimated_cost_usd"] is None

    def test_skips_zero_tokens(self):
        from agent_ledger import _estimate_missing_costs
        pricing = load_model_pricing(DATA_DIR)
        rows = [{
            "agent": "Test",
            "model": "deepseek-chat",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": None,
            "cost_status": "unknown",
        }]
        _estimate_missing_costs(rows, pricing)
        assert rows[0]["estimated_cost_usd"] is None

    def test_handles_empty_pricing(self):
        from agent_ledger import _estimate_missing_costs
        rows = [{
            "agent": "Test",
            "model": "deepseek-chat",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "estimated_cost_usd": None,
            "cost_status": "unknown",
        }]
        # 空 pricing 不应报错
        _estimate_missing_costs(rows, {"models": {}})
        assert rows[0]["estimated_cost_usd"] is None
