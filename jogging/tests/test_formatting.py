"""格式化层测试（第 4 层）：数值 → 展示字符串。

这一层全是纯函数、无 IO，是整个脚本里最值得测的部分：
差异显示的阈值、精度、正负号规则都在这里。
"""

import pytest

from analyze_jogging import (
    CORE_METRIC_DEFS,
    _better_class,
    _extract_format_precision,
    _signed_format,
    format_duration,
    format_km_cumtime_diff,
    format_km_hr_diff,
    format_km_pace_diff,
    format_metric_diff,
    format_metric_value,
    format_pace,
    short_date,
)


def metric_def(key):
    """按 key 取出 CORE_METRIC_DEFS 里的定义。"""
    return next(m for m in CORE_METRIC_DEFS if m['key'] == key)


# ---------------------------------------------------------------- format_pace

@pytest.mark.parametrize('pace, expected', [
    (6.0,   "6'00\""),
    (5.5,   "5'30\""),
    (6.3,   "6'18\""),   # 6.3 分 = 378 秒
    (6.1,   "6'06\""),   # 6.1 分 = 366 秒（浮点 366.00000000000006）
    (6.999, "7'00\""),   # 四舍五入到整秒
    (0,     "0'00\""),   # 非法值兜底
    (-1,    "0'00\""),
])
def test_format_pace(pace, expected):
    """配速按“分'秒\"”显示。秒数必须先乘 60 再取整，否则浮点误差会让它少 1 秒。"""
    assert format_pace(pace) == expected


# ------------------------------------------------------------ format_duration

@pytest.mark.parametrize('seconds, expected', [
    (0,    '0s'),        # 非法值兜底
    (-5,   '0s'),
    (30,   '30s'),       # < 1 分钟
    (59,   '59s'),
    (60,   '1:00'),      # < 1 小时
    (92,   '1:32'),
    (3600, '1:00:00'),   # ≥ 1 小时
    (3712, '1:01:52'),
    (6080, '1:41:20'),
])
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


# -------------------------------------------------------- format_metric_value

def test_format_metric_value_missing_or_zero_shows_dash():
    assert format_metric_value(None, metric_def('avg_hr')) == '-'
    assert format_metric_value(0, metric_def('avg_hr')) == '-'


def test_format_metric_value_applies_scale():
    """avg_stride_length 的 scale=0.1：原始 950 → 95.00 cm。"""
    assert format_metric_value(950, metric_def('avg_stride_length')) == '95.00 cm'


def test_format_metric_value_special_formats():
    assert format_metric_value(6080, metric_def('duration_seconds')) == '1:41:20'
    assert format_metric_value(6.3, metric_def('avg_pace')) == "6'18\""


# --------------------------------------------------------- format_metric_diff

def test_format_metric_diff_missing_values():
    assert format_metric_diff(None, 100, metric_def('avg_hr')) == ''
    assert format_metric_diff(100, None, metric_def('avg_hr')) == ''
    assert format_metric_diff(0, 0, metric_def('avg_hr')) == ''


def test_format_metric_diff_duration_threshold_is_5_seconds():
    """时长差异低于 5 秒就隐藏，避免噪声。"""
    assert format_metric_diff(6080, 6005, metric_def('duration_seconds')) == '-75s'
    assert format_metric_diff(6080, 6077, metric_def('duration_seconds')) == ''


def test_format_metric_diff_pace_shown_in_seconds():
    """配速差异换算成秒：6.30 → 6.15 min/km = -9 秒。"""
    assert format_metric_diff(6.30, 6.15, metric_def('avg_pace')) == '-9s'


def test_format_metric_diff_keeps_sub_display_precision():
    """显示值相同但真实有微小差异的指标，仍要显示高精度差值。"""
    assert format_metric_diff(130.50, 130.61, metric_def('avg_hr')) == '+0.11 bpm'
    assert format_metric_diff(130.50, 130.50, metric_def('avg_hr')) == ''
    assert format_metric_diff(245.00, 245.10, metric_def('avg_gct')) == '+0.1 ms'


def test_format_metric_diff_respects_per_key_threshold():
    """avg_gct 的阈值是 0.05，比通用精度更粗（避免显示 +0.0 ms）。"""
    assert format_metric_diff(245.00, 245.02, metric_def('avg_gct')) == ''


def test_format_metric_diff_generic_uses_fmt_precision():
    """通用指标按格式串推断阈值：'{:.2f}' → 0.01。"""
    assert format_metric_diff(16000, 16200, metric_def('total_distance')) == '+0.20 km'
    assert format_metric_diff(16000, 16005, metric_def('total_distance')) == ''


# ------------------------------------------------------- 每公里专用差异格式化

@pytest.mark.parametrize('old, new, expected', [
    (125.4, 126.2, "<span class='diff'>+1</span>"),
    (126.2, 125.4, "<span class='diff'>-1</span>"),
    (125.2, 125.4, ''),   # 四舍五入后相同 → 不显示，保证与显示的整数一致
])
def test_format_km_hr_diff_rounds_before_subtracting(old, new, expected):
    assert format_km_hr_diff(old, new) == expected


@pytest.mark.parametrize('old, new, expected', [
    (6.30, 6.15, "<span class='diff'>-9s</span>"),
    (6.15, 6.30, "<span class='diff'>+9s</span>"),
    (6.300, 6.305, ''),   # 差 0.005 min < 0.01 阈值
])
def test_format_km_pace_diff(old, new, expected):
    assert format_km_pace_diff(old, new) == expected


@pytest.mark.parametrize('old, new, expected', [
    (380, 370, "<span class='diff'>-10s</span>"),
    (380, 380, ''),
])
def test_format_km_cumtime_diff(old, new, expected):
    assert format_km_cumtime_diff(old, new) == expected


# ------------------------------------------------------ 格式化层辅助函数

@pytest.mark.parametrize('fmt, expected', [
    ('{:.2f} km', 0.01),
    ('{:.1f} %', 0.1),
    ('{:.0f} bpm', 1.0),
    ('duration', 1e-6),   # 非数值格式串 → 用最小阈值
    ('pace', 1e-6),
])
def test_extract_format_precision(fmt, expected):
    assert _extract_format_precision(fmt) == pytest.approx(expected)


@pytest.mark.parametrize('value, fmt, expected', [
    (0.5,  '{:.2f}', '+0.50'),
    (-0.5, '{:.2f}', '-0.50'),
    (5,    '{:.0f}', '+5'),
])
def test_signed_format_always_shows_sign(value, fmt, expected):
    assert _signed_format(value, fmt) == expected


# ---------------------------------------------------------------- short_date

@pytest.mark.parametrize('date_str, expected', [
    ('20260404', '0404'),       # 8 位纯数字 → 去掉年份
    ('0404', '0404'),           # 已是短格式 → 原样返回
    ('2026040', '2026040'),     # 长度不足 → 原样返回
    ('abcdefgh', 'abcdefgh'),   # 非数字 → 原样返回
])
def test_short_date(date_str, expected):
    assert short_date(date_str) == expected


# -------------------------------------------------------------- _better_class

@pytest.mark.parametrize('val_a, val_b, lower_is_better, expected', [
    (1, 2, True,  'better'),   # 越小越好，1 < 2
    (2, 1, True,  ''),
    (2, 1, False, 'better'),   # 越大越好，2 > 1
    (1, 2, False, ''),
    (5, 5, True,  ''),         # 相等不算更好
    (None, 1, True, ''),       # 缺失值不参与比较
    (1, None, True, ''),
    (1, 2, None, ''),          # lower_is_better 为 None → 按“越大越好”处理
])
def test_better_class(val_a, val_b, lower_is_better, expected):
    assert _better_class(val_a, val_b, lower_is_better) == expected
