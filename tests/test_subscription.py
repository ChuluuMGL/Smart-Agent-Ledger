"""测试 subscription_ledger.py 中的续费日期和重置时间计算。"""
import datetime as dt

import pytest

from subscription_ledger import _next_renewal, _next_reset


def _make_plan(
    renewal_date: str = "2026-01-15",
    interval_months: int = 1,
    interval_days: int = 0,
    reset_type: str = "",
    reset_time: str = "00:00",
    reset_weekday: int = None,
    reset_day_of_month: int = None,
    timezone: str = "Asia/Shanghai",
) -> dict:
    """构建测试用的 plan 字典。"""
    plan: dict = {
        "renewal_date": renewal_date,
        "timezone": timezone,
        "billing": {
            "renewal_date": renewal_date,
            "renewal_interval_months": interval_months or None,
            "renewal_interval_days": interval_days or None,
        },
    }
    if reset_type:
        plan["reset"] = {
            "type": reset_type,
            "time": reset_time,
            "timezone": timezone,
        }
        if reset_weekday is not None:
            plan["reset"]["weekday"] = reset_weekday
        if reset_day_of_month is not None:
            plan["reset"]["day_of_month"] = reset_day_of_month
    return plan


# ── _next_renewal ───────────────────────────────────────────────────────────


class TestNextRenewal:
    def test_monthly_renewal_in_future(self):
        """续费日期在未来 → 直接返回该日期。"""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-02-15", interval_months=1)
        result = _next_renewal(plan, now)
        assert result is not None
        assert result.month == 2
        assert result.day == 15

    def test_monthly_renewal_in_past_advances(self):
        """续费日期在过去 → 按月推进到未来。"""
        now = dt.datetime(2026, 3, 1, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-01-15", interval_months=1)
        result = _next_renewal(plan, now)
        assert result is not None
        assert result >= now
        assert result.month == 3
        assert result.day == 15

    def test_monthly_cross_year(self):
        """月度续费跨年。"""
        now = dt.datetime(2026, 12, 20, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-01-15", interval_months=1)
        result = _next_renewal(plan, now)
        assert result is not None
        assert result.year == 2027
        assert result.month == 1
        assert result.day == 15

    def test_monthly_end_of_month_overflow(self):
        """31 号续费日在小月自动缩减到 28/29/30。"""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-01-31", interval_months=1)
        result = _next_renewal(plan, now)
        assert result is not None
        # 1月31日 → 2月无31日，应降到28日
        assert result.month == 1
        assert result.day == 31
        # 验证下一个月
        result2 = _next_renewal(plan, dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc))
        assert result2 is not None
        assert result2.day <= 28

    def test_daily_interval(self):
        """按天数间隔续费。"""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-01-10", interval_months=0, interval_days=7)
        result = _next_renewal(plan, now)
        assert result is not None
        assert result.day == 10

    def test_daily_interval_advances(self):
        now = dt.datetime(2026, 1, 12, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2026-01-10", interval_months=0, interval_days=7)
        result = _next_renewal(plan, now)
        assert result is not None
        assert result.day == 17

    def test_no_renewal_date_returns_none(self):
        plan = {"billing": {}, "timezone": "UTC"}
        result = _next_renewal(plan, dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
        assert result is None

    def test_interval_months_multi(self):
        """多月间隔续费。"""
        now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        plan = _make_plan(renewal_date="2025-11-15", interval_months=3)
        result = _next_renewal(plan, now)
        assert result is not None
        # 11月 + 3月 = 次年2月
        assert result.month == 2
        assert result.day == 15


# ── _next_reset ─────────────────────────────────────────────────────────────


class TestNextReset:
    def test_daily_reset_future_today(self):
        """当天重置时间还未到 → 返回今天。"""
        # now = 10:00, reset = 18:00 → 今天 18:00
        now = dt.datetime(2026, 6, 8, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="daily", reset_time="18:00")
        result = _next_reset(plan, now)
        assert result is not None
        assert result.day == 8
        assert result.hour == 18

    def test_daily_reset_already_passed(self):
        """当天重置时间已过 → 返回明天。"""
        now = dt.datetime(2026, 6, 8, 20, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="daily", reset_time="18:00")
        result = _next_reset(plan, now)
        assert result is not None
        assert result.day == 9
        assert result.hour == 18

    def test_weekly_reset(self):
        """每周重置。"""
        # 2026-06-08 是周一
        now = dt.datetime(2026, 6, 8, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="weekly", reset_time="00:00", reset_weekday=0)  # 周一
        result = _next_reset(plan, now)
        assert result is not None
        # 当前周一10点 > 周一0点 → 下周一
        assert result.weekday() == 0
        assert result.day == 15

    def test_weekly_reset_this_week(self):
        """本周重置日还没到 → 本周。"""
        # 2026-06-08 是周一，重置日是周三
        now = dt.datetime(2026, 6, 8, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="weekly", reset_time="00:00", reset_weekday=2)  # 周三
        result = _next_reset(plan, now)
        assert result is not None
        assert result.weekday() == 2
        assert result.day == 10

    def test_monthly_reset(self):
        """每月重置。"""
        now = dt.datetime(2026, 6, 5, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="monthly", reset_time="00:00", reset_day_of_month=15)
        result = _next_reset(plan, now)
        assert result is not None
        assert result.day == 15
        assert result.month == 6

    def test_monthly_reset_day_passed(self):
        """当月重置日已过 → 下月。"""
        now = dt.datetime(2026, 6, 20, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="monthly", reset_time="00:00", reset_day_of_month=15)
        result = _next_reset(plan, now)
        assert result is not None
        assert result.month == 7
        assert result.day == 15

    def test_monthly_reset_31_cross_month(self):
        """31号重置日在小月 → 跳过无31号的月份。"""
        now = dt.datetime(2026, 1, 1, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        plan = _make_plan(reset_type="monthly", reset_time="00:00", reset_day_of_month=31)
        result = _next_reset(plan, now)
        assert result is not None
        assert result.day == 31
        assert result.month == 1

    def test_no_reset_type_returns_none(self):
        plan = {"reset": {}, "timezone": "UTC"}
        result = _next_reset(plan, dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
        assert result is None

    def test_weekly_no_weekday_returns_none(self):
        plan = _make_plan(reset_type="weekly", reset_time="00:00")
        # reset_weekday 未设置
        now = dt.datetime(2026, 6, 8, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        result = _next_reset(plan, now)
        assert result is None

    def test_monthly_zero_day_returns_none(self):
        plan = _make_plan(reset_type="monthly", reset_time="00:00", reset_day_of_month=0)
        now = dt.datetime(2026, 6, 8, tzinfo=dt.timezone(dt.timedelta(hours=8)))
        result = _next_reset(plan, now)
        assert result is None
