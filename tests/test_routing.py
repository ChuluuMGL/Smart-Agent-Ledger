"""测试 gateway.py 中的路由检测和降级链逻辑。

gateway.py 在模块级创建 FastAPI app 实例，直接 import 会触发 FastAPI 初始化。
我们通过 sys.modules 注入 mock 来跳过这一步，只导入纯函数。
"""
import sys
import types
from unittest.mock import MagicMock

import pytest


# ── 在 import gateway 前 mock FastAPI 及其依赖 ─────────────────────────────
# 创建一个假的 fastapi 模块树，让 gateway.py 的顶层代码不报错
_mock_fastapi = types.ModuleType("fastapi")
_mock_fastapi.FastAPI = MagicMock(return_value=MagicMock())
_mock_fastapi.HTTPException = Exception
_mock_fastapi.Request = MagicMock

_mock_responses = types.ModuleType("fastapi.responses")
_mock_responses.FileResponse = MagicMock
_mock_responses.HTMLResponse = MagicMock
_mock_responses.StreamingResponse = MagicMock
_mock_responses.JSONResponse = MagicMock

_mock_middleware = types.ModuleType("fastapi.middleware")
_mock_cors = types.ModuleType("fastapi.middleware.cors")
_mock_cors.CORSMiddleware = MagicMock

sys.modules.setdefault("fastapi", _mock_fastapi)
sys.modules.setdefault("fastapi.responses", _mock_responses)
sys.modules.setdefault("fastapi.middleware", _mock_middleware)
sys.modules.setdefault("fastapi.middleware.cors", _mock_cors)

from gateway import detect_route, fallback_chain


# ── detect_route — 关键词命中 ──────────────────────────────────────────────


class TestDetectRoute:
    """消息 → 路由类型的关键词匹配规则。"""

    # ── forced 参数 ──

    def test_forced_local(self):
        assert detect_route([{"role": "user", "content": "随便什么"}], forced="local") == "local"

    def test_forced_coding(self):
        assert detect_route([{"role": "user", "content": "随便什么"}], forced="coding") == "coding"

    def test_forced_reasoning(self):
        assert detect_route([{"role": "user", "content": "随便什么"}], forced="reasoning") == "reasoning"

    def test_forced_quality(self):
        assert detect_route([{"role": "user", "content": "随便什么"}], forced="quality") == "quality"

    def test_forced_invalid_falls_through(self):
        """forced 值不在白名单时走正常路由。"""
        result = detect_route([{"role": "user", "content": "帮我debug一下"}], forced="unknown")
        assert result == "coding"

    # ── quality 关键词 ──

    def test_quality_prd(self):
        assert detect_route([{"role": "user", "content": "帮我写个PRD"}]) == "quality"

    def test_quality_final_draft(self):
        assert detect_route([{"role": "user", "content": "这是终稿请检查"}]) == "quality"

    def test_quality_client_facing(self):
        assert detect_route([{"role": "user", "content": "发客户的邮件"}]) == "quality"

    # ── reasoning 关键词 ──

    def test_reasoning_analysis(self):
        msg = [{"role": "user", "content": "请做一个严谨分析"}]
        assert detect_route(msg) == "reasoning"

    def test_reasoning_tradeoff(self):
        msg = [{"role": "user", "content": "这两个方案的tradeoff是什么"}]
        assert detect_route(msg) == "reasoning"

    def test_reasoning_architecture(self):
        msg = [{"role": "user", "content": "讨论一下架构设计"}]
        assert detect_route(msg) == "reasoning"

    # ── coding 关键词 ──

    def test_coding_debug(self):
        assert detect_route([{"role": "user", "content": "debug这个bug"}]) == "coding"

    def test_coding_code_block(self):
        assert detect_route([{"role": "user", "content": "看看这段代码 ```python"}]) == "coding"

    def test_coding_import(self):
        assert detect_route([{"role": "user", "content": "import os"}]) == "coding"

    def test_coding_pytest(self):
        assert detect_route([{"role": "user", "content": "运行pytest"}]) == "coding"

    # ── local 关键词（短消息） ──

    def test_local_short_message(self):
        """短消息 + local 关键词 → local 路由。"""
        msg = [{"role": "user", "content": "快速格式化"}]
        assert detect_route(msg) == "local"

    def test_local_keyword_long_message_also_local(self):
        """P2.4: 移除长度限制后，长消息含 local 关键词也能匹配 local 路由。"""
        long_text = "快速" + "填充内容" * 100  # >400 字符
        msg = [{"role": "user", "content": long_text}]
        result = detect_route(msg)
        assert result == "local"

    def test_long_message_no_keyword_defaults_coding(self):
        """长消息不含任何关键词 → 默认 coding。"""
        long_text = "这是一段很长的话题讨论" * 50  # >400 字符
        msg = [{"role": "user", "content": long_text}]
        result = detect_route(msg)
        assert result == "coding"

    # ── 默认路由 ──

    def test_default_coding(self):
        """无关键词消息默认走 coding 路由。"""
        msg = [{"role": "user", "content": "今天天气不错"}]
        assert detect_route(msg) == "coding"

    # ── 边界情况 ──

    def test_empty_messages(self):
        """空消息列表 → 默认 coding。"""
        assert detect_route([]) == "coding"

    def test_none_content(self):
        """content 为 None 的消息 → 默认 coding。"""
        assert detect_route([{"role": "user", "content": None}]) == "coding"

    def test_list_content(self):
        """content 是列表（多模态消息）也能拼接。"""
        msg = [{"role": "user", "content": [{"type": "text", "text": "debug这个问题"}]}]
        assert detect_route(msg) == "coding"

    def test_case_insensitive(self):
        """关键词匹配不区分大小写（_messages_text 已 lower）。"""
        assert detect_route([{"role": "user", "content": "Debug"}]) == "coding"
        assert detect_route([{"role": "user", "content": "API 接口"}]) == "coding"

    def test_multiple_messages_concatenated(self):
        """多轮消息会拼接后再匹配。"""
        msgs = [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "帮我做"},
            {"role": "assistant", "content": "好的"},
            {"role": "user", "content": "一个架构分析"},
        ]
        assert detect_route(msgs) == "reasoning"


# ── fallback_chain — 降级链 ────────────────────────────────────────────────


class TestFallbackChain:
    def test_local_chain(self):
        assert fallback_chain("local") == ["local", "coding", "backup"]

    def test_coding_chain(self):
        assert fallback_chain("coding") == ["coding", "backup", "quality"]

    def test_reasoning_chain(self):
        assert fallback_chain("reasoning") == ["reasoning", "coding", "backup"]

    def test_quality_chain(self):
        assert fallback_chain("quality") == ["quality", "coding", "backup"]

    def test_unknown_route_default(self):
        assert fallback_chain("unknown") == ["coding", "backup"]

    def test_empty_route_default(self):
        assert fallback_chain("") == ["coding", "backup"]

    def test_chain_order_preserves_priority(self):
        """每条链的首元素就是路由本身（最高优先级）。"""
        for route in ["local", "coding", "reasoning", "quality"]:
            chain = fallback_chain(route)
            assert chain[0] == route
