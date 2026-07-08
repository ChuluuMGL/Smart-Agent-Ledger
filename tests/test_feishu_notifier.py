"""测试 feishu_notifier.py 中的纯逻辑函数 (此前 0 测试)。"""
import pytest

from feishu_notifier import (
    DEFAULT_RENEWAL_WARNING_DAYS,
    _clamped_int,
    _money,
    _reminder_start_date,
    _short_time,
    _status_label,
    effective_warning_days,
    missing_send_fields,
)


class TestStatusLabel:
    def test_known_statuses(self):
        assert _status_label("ok") == "正常"
        assert _status_label("renewal_due") == "需续费"
        assert _status_label("renewal_soon") == "临近续费"
        assert _status_label("quota_low") == "额度偏低"
        assert _status_label("quota_unknown") == "额度未知"

    def test_unknown_status(self):
        assert _status_label("weird") == "weird"

    def test_none_status(self):
        assert _status_label(None) == "未知"

    def test_empty_status(self):
        assert _status_label("") == "未知"


class TestMoney:
    def test_integer_amount(self):
        plan = {"billing_amount": 100, "billing_currency": "¥", "billing_period": "month"}
        assert _money(plan) == "¥ 100/月"

    def test_float_amount(self):
        plan = {"billing_amount": 9.99, "billing_currency": "$", "billing_period": "year"}
        assert _money(plan) == "$ 9.99/年"

    def test_integer_valued_float(self):
        """100.0 应显示为 '100' 而非 '100.00'。"""
        plan = {"billing_amount": 100.0, "billing_currency": "¥", "billing_period": "month"}
        assert _money(plan) == "¥ 100/月"

    def test_missing_amount(self):
        assert _money({"billing_currency": "¥"}) == "费用不可用"

    def test_missing_currency(self):
        assert _money({"billing_amount": 100}) == "费用不可用"

    def test_usage_period(self):
        plan = {"billing_amount": 50, "billing_currency": "¥", "billing_period": "usage"}
        assert _money(plan) == "¥ 50/按量"

    def test_no_period(self):
        plan = {"billing_amount": 50, "billing_currency": "¥"}
        assert _money(plan) == "¥ 50"

    def test_all_periods(self):
        for period, label in [("month", "月"), ("quarter", "季"), ("year", "年"),
                              ("month_reference", "月参考"), ("usage", "按量")]:
            plan = {"billing_amount": 10, "billing_currency": "¥", "billing_period": period}
            assert _money(plan) == f"¥ 10/{label}"


class TestShortTime:
    def test_iso_datetime(self):
        assert _short_time("2026-06-12T15:30:45") == "2026-06-12 15:30"

    def test_none(self):
        assert _short_time(None) == "不可用"

    def test_empty(self):
        assert _short_time("") == "不可用"

    def test_truncates_to_16_chars(self):
        assert len(_short_time("2026-06-12T15:30:45.123456")) == 16


class TestClampedInt:
    def test_normal_value(self):
        assert _clamped_int(5, default=7) == 5

    def test_string_value(self):
        assert _clamped_int("10", default=7) == 10

    def test_invalid_returns_default(self):
        assert _clamped_int("abc", default=7) == 7

    def test_none_returns_default(self):
        assert _clamped_int(None, default=7) == 7

    def test_below_minimum(self):
        assert _clamped_int(-5, default=7, minimum=0) == 0

    def test_above_maximum(self):
        assert _clamped_int(1000, default=7, maximum=365) == 365

    def test_custom_bounds(self):
        assert _clamped_int(50, default=10, minimum=0, maximum=100) == 50
        assert _clamped_int(150, default=10, minimum=0, maximum=100) == 100


class TestEffectiveWarningDays:
    def test_plan_specific_override(self):
        config = {"default_renewal_warning_days": 7, "plan_warning_days": {"plan_a": 14}}
        plan = {"id": "plan_a"}
        assert effective_warning_days(config, plan) == 14

    def test_default_fallback(self):
        config = {"default_renewal_warning_days": 7}
        plan = {"id": "plan_b"}
        assert effective_warning_days(config, plan) == 7

    def test_missing_default_uses_module_constant(self):
        config = {}
        plan = {"id": "plan_c"}
        assert effective_warning_days(config, plan) == DEFAULT_RENEWAL_WARNING_DAYS

    def test_plan_specific_clamped(self):
        config = {"plan_warning_days": {"plan_a": 999}}
        plan = {"id": "plan_a"}
        assert effective_warning_days(config, plan) <= 365


class TestReminderStartDate:
    def test_normal_calculation(self):
        result = _reminder_start_date("2026-06-30", 7)
        assert result == "2026-06-23"

    def test_zero_warning_days(self):
        result = _reminder_start_date("2026-06-30", 0)
        assert result == "2026-06-30"

    def test_none_renewal(self):
        assert _reminder_start_date(None, 7) is None

    def test_empty_renewal(self):
        assert _reminder_start_date("", 7) is None

    def test_invalid_date(self):
        assert _reminder_start_date("not-a-date", 7) is None

    def test_crosses_month_boundary(self):
        result = _reminder_start_date("2026-06-05", 10)
        assert result == "2026-05-26"

    def test_z_suffix_handled(self):
        result = _reminder_start_date("2026-06-30T00:00:00Z", 7)
        assert result == "2026-06-23"


class TestMissingSendFields:
    def test_all_present(self):
        config = {"app_id": "x", "app_secret": "y", "receive_id_type": "z", "receive_id": "w"}
        result = missing_send_fields(config)
        assert result == {"app_id": False, "app_secret": False,
                          "receive_id_type": False, "receive_id": False}

    def test_all_missing(self):
        result = missing_send_fields({})
        assert result == {"app_id": True, "app_secret": True,
                          "receive_id_type": True, "receive_id": True}

    def test_partial(self):
        config = {"app_id": "x"}
        result = missing_send_fields(config)
        assert result["app_id"] is False
        assert result["app_secret"] is True

    def test_empty_string_counts_as_missing(self):
        config = {"app_id": "", "app_secret": "y", "receive_id_type": "z", "receive_id": "w"}
        result = missing_send_fields(config)
        assert result["app_id"] is True
