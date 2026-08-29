"""统计计算层测试（第 3 层）：原始记录 → 聚合指标 / 每公里分箱。

重点覆盖几处带“容差”“截断”“分位数”等非常规规则的函数。
"""

import pytest

from analyze_jogging import (
    _find_value_at_or_near,
    _mean,
    _speed_to_pace,
    compute_per_km_split,
    compute_run_stats,
    compute_y_axis_range,
    downsample,
    get_cumulative_time_at_kms,
)
from helpers import make_records


# ------------------------------------------------------------ _speed_to_pace

@pytest.mark.parametrize('speed_mps, expected', [
    (0, None),
    (-1, None),
    (1000 / (6.3 * 60), pytest.approx(6.3)),
    (1000 / (5 * 60), pytest.approx(5.0)),    # 下边界（含）
    (1000 / (10 * 60), pytest.approx(10.0)),  # 上边界（含）
    (1000 / (4 * 60), None),                  # 过快 → 剔除
    (1000 / (11 * 60), None),                 # 过慢 → 剔除
])
def test_speed_to_pace_filters_out_of_range(speed_mps, expected):
    """只接受 [5, 10] min/km，剔除 GPS 漂移和停止走动的异常值。"""
    result = _speed_to_pace(speed_mps)
    if expected is None:
        assert result is None
    else:
        assert result == expected


# -------------------------------------------------------------------- _mean

def test_mean():
    assert _mean([1, 2, 3]) == 2
    assert _mean([]) is None


# ---------------------------------------------------- _find_value_at_or_near

XS = [0.0, 1.0, 2.0, 3.0]
YS = [10, 20, 30, 40]


def test_find_value_exact_match():
    assert _find_value_at_or_near(XS, YS, 2.0) == 30


def test_find_value_takes_first_point_at_or_beyond_target():
    assert _find_value_at_or_near(XS, YS, 1.5) == 30


def test_find_value_out_of_range_returns_none():
    assert _find_value_at_or_near(XS, YS, 5.0) is None


def test_find_value_tolerance_fallback():
    """终点距目标在 50m 容差内时，回退到最后一点。"""
    assert _find_value_at_or_near(XS, YS, 3.02) == 40


def test_find_value_empty_input():
    assert _find_value_at_or_near([], [], 1.0) is None


# ---------------------------------------------------------------- downsample

def test_downsample_default_step():
    assert downsample(list(range(100))) == list(range(0, 100, 10))


def test_downsample_custom_step():
    assert downsample(list(range(100)), step=25) == [0, 25, 50, 75]


def test_downsample_empty():
    assert downsample([]) == []


# ------------------------------------------------------- compute_y_axis_range

def test_y_axis_range_empty_fallback():
    assert compute_y_axis_range([]) == {'min': 0, 'max': 100}


def test_y_axis_range_constant_values():
    assert compute_y_axis_range([10] * 100) == {'min': 10, 'max': 10}


def test_y_axis_range_excludes_extreme_outlier():
    """5%-95% 分位数：单个极端值不应把 Y 轴拉偏。"""
    result = compute_y_axis_range([10] * 99 + [1000])
    assert result == {'min': 10, 'max': 10}


def test_y_axis_range_never_negative_min():
    assert compute_y_axis_range([1, 2, 3])['min'] >= 0


# --------------------------------------------------------- compute_run_stats

def test_compute_run_stats_core_fields(stats_a):
    # 注意：total_distance 单位是「米」，换算成 km 由 CORE_METRIC_DEFS 的 scale=0.001 负责
    assert stats_a['total_distance'] == pytest.approx(16000, abs=1)
    # 时长 = 最后一条记录 - 第一条记录。首条记录落在 50m 处（出发后 19s），
    # 所以是 16km×380s - 19s = 6061s
    assert stats_a['duration_seconds'] == pytest.approx(6061, abs=1)
    assert stats_a['max_hr'] >= stats_a['avg_hr']
    assert stats_a['avg_hr'] == pytest.approx(136.4, abs=0.5)
    assert stats_a['avg_cadence'] == pytest.approx(184, abs=1)   # 半步 ×2
    assert stats_a['elevation_gain'] > 0


def test_compute_run_stats_truncates_cool_down_walk():
    """默认在 16000m 截断，排除结束后的步行数据。"""
    stats = compute_run_stats(make_records(n=400))   # 合成 20km
    assert stats['total_distance'] == pytest.approx(16000, abs=1)


def test_compute_run_stats_empty_input():
    assert compute_run_stats([]) == {}


def test_two_runs_are_distinguishable(stats_a, stats_b):
    """两次合成的跑步必须有差异，否则上层对比测试没有意义。"""
    assert stats_a['avg_pace'] > stats_b['avg_pace']      # a 更慢
    assert stats_a['duration_seconds'] > stats_b['duration_seconds']


# ------------------------------------------------------ compute_per_km_split

def test_per_km_split_covers_all_16_km(stats_a):
    splits = compute_per_km_split(stats_a)
    assert [s['km'] for s in splits] == list(range(1, 17))
    assert all(s['hr'] is not None for s in splits)
    assert all(s['pace'] is not None for s in splits)


def test_per_km_split_cumulative_average(stats_a):
    """累积平均 = 到该公里为止所有数据的均值。

    合成数据的心率线性上升，所以累积均值应单调不减，
    且最后一个公里点（即全程）应等于整体平均心率。
    """
    splits = compute_per_km_split(stats_a)
    cum = [s['cum_avg_hr'] for s in splits]
    assert all(b >= a for a, b in zip(cum, cum[1:]))   # 单调不减
    assert cum[-1] == pytest.approx(stats_a['avg_hr'], abs=0.01)
    assert cum[0] < cum[-1]   # 心率上升 → 首公里均值低于全程均值


# ----------------------------------------------- get_cumulative_time_at_kms

def test_cumulative_time_one_node_per_km(stats_a):
    nodes = get_cumulative_time_at_kms(stats_a)
    assert [n['km'] for n in nodes] == list(range(1, 17))
    seconds = [n['seconds'] for n in nodes]
    assert seconds == sorted(seconds)   # 单调递增


def test_cumulative_time_tolerance_fallback_near_finish():
    """终点 15.98km 而非 16.00km：容差 50m 内应回退到最后一条记录。"""
    records = make_records(step_m=15980 / 320, n=320)   # 全程 15.98km
    nodes = get_cumulative_time_at_kms(compute_run_stats(records))
    assert [n['km'] for n in nodes] == list(range(1, 17))


def test_cumulative_time_stops_at_actual_distance():
    """只跑了 3km 时不应产出 16 个节点。"""
    records = make_records(n=60)   # 3km
    nodes = get_cumulative_time_at_kms(compute_run_stats(records))
    assert [n['km'] for n in nodes] == [1, 2, 3]
