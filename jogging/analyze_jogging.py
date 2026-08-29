#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跑步数据分析工具 - 生成 HTML 可视化对比报告
============================================

设计思路：
  - 分层架构：配置 → 解析 → 统计 → 格式化 → 图表 → HTML组装
  - 每个函数只做一件事，命名即文档
  - 所有展示相关逻辑（格式化、差异计算、高亮）集中在格式化层
"""

import json
import os
import re
from datetime import datetime
from string import Template

from fitparse import FitFile


# =============================================================================
# 0. 目录布局 — 所有路径统一在此定义
# =============================================================================

# 脚本所在目录（jogging/），无论从哪个 cwd 运行都能正确定位
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')          # 输入：FIT 文件（git 忽略）
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')  # 页面 / 图表模板
STATIC_DIR = os.path.join(BASE_DIR, 'static')      # CSS / favicon 等静态资源


# =============================================================================
# 1. 配置层 — 纯数据定义，无业务逻辑
# =============================================================================

# FIT 文件字段到内部变量名的映射（record 级别）
RECORD_FIELD_MAP = {
    'heart_rate':      'heart_rates',
    'enhanced_speed':  'speeds',
    'distance':        'distances',
    'timestamp':       'timestamps',
    'enhanced_altitude': 'altitudes',
    'cadence':         'cadences',
    'temperature':     'temperatures',
    'stance_time':     'ground_contact_times',
    'power':           'powers',
    'step_length':     'stride_lengths',
    'vertical_ratio':  'vertical_ratios',
}

# 左侧核心指标表格的列定义
CORE_METRIC_DEFS = [
    {'key': 'total_distance',     'label': '总距离',       'fmt': '{:.2f} km', 'scale': 0.001},
    {'key': 'duration_seconds',   'label': '时长',         'fmt': 'duration'},
    {'key': 'avg_pace',           'label': '平均配速',     'fmt': 'pace',       'lower_is_better': True},
    {'key': 'avg_hr',             'label': '平均心率',     'fmt': '{:.0f} bpm', 'lower_is_better': True},
    {'key': 'max_hr',             'label': '最高心率',     'fmt': '{:.0f} bpm'},
    {'key': 'avg_cadence',        'label': '平均步频',     'fmt': '{:.0f} spm', 'lower_is_better': False},
    {'key': 'avg_stride_length',  'label': '平均步幅',     'fmt': '{:.2f} cm',  'scale': 0.1},
    {'key': 'avg_gct',            'label': '平均触地时间', 'fmt': '{:.0f} ms',  'lower_is_better': True},
    {'key': 'avg_vertical_ratio','label': '平均垂直比例', 'fmt': '{:.1f} %',   'lower_is_better': True},
    {'key': 'elevation_gain',     'label': '累计爬升',     'fmt': '{:.1f} m'},
    {'key': 'avg_temperature',    'label': '温度',         'fmt': '{:.1f} °C'},
    {'key': 'avg_power',          'label': '平均功率',     'fmt': '{:.0f} W'},
]

# 图表区域配置：每个图表从 stats 中取哪个字段、用什么过滤/Y轴方向
CHART_DEFS = [
    {'id': 'hrChart',      'title': '心率变化对比',  'data_key': 'heart_rates',
     'y_label': '心率 (bpm)',                                          },
    {'id': 'paceChart',    'title': '配速变化对比',  'data_key': 'speeds',
     'y_label': '配速 (min/km)',
     'filter_fn': lambda x: 1000 / x / 60 if (x > 0 and 5 <= 1000 / x / 60 <= 10) else None,
     'reverse_y': True},
    {'id': 'gctChart',     'title': '触地时间对比',  'data_key': 'ground_contact_times',
     'y_label': '触地时间 (ms)',
     'filter_fn': lambda x: x if x <= 350 else None,
     'reverse_y': True},
    {'id': 'cadenceChart', 'title': '步频对比',      'data_key': 'cadences',
     'y_label': '步频 (spm)',
     'filter_fn': lambda x: x * 2 if x >= 75 else None},
]

# 底部每公里表格的列分组定义（每组 3 列：date1 / date2 / 差异）
# cum=True 表示该组为累积列，单元格加 col-cum 浅蓝底色
KM_COLUMN_GROUPS = [
    {'label': '心率',         'cum': False},
    {'label': '配速',         'cum': False},
    {'label': '累积平均心率', 'cum': True},
    {'label': '累积平均配速', 'cum': True},
    {'label': '累积用时',     'cum': False},
]

# 图表降采样步长（每 N 条记录取一条），减少前端渲染压力
DOWNSAMPLE_STEP = 10


# =============================================================================
# 2. 数据解析层 — 从 FIT 二进制文件提取原始记录
# =============================================================================

def parse_fit_file(filepath):
    """
    解析 Garmin .fit 文件，按消息类型分组返回字典。

    返回值示例：
        {
            'records': [{field: value}, ...],   # 每秒/每条记录的原始数据
            'sessions': [...],                  # 整次慢跑摘要
            'laps': [...]                      # 圈（lap）数据
        }
    """
    fitfile = FitFile(filepath)
    result = {'records': [], 'sessions': [], 'laps': []}

    for msg_type in ('record', 'session', 'lap'):
        for msg in fitfile.get_messages(msg_type):
            record = {f.name: f.value for f in msg if f.value is not None}
            if record:
                result[f'{msg_type}s'].append(record)

    return result


# =============================================================================
# 3. 统计计算层 — 原始记录 → 聚合统计 + 每公里分箱
# =============================================================================

def compute_run_stats(raw_records, max_distance_m=16000):
    """
    从原始 record 列表中计算所有聚合指标。

    设计思路：
      1) 先逐条提取字段（过滤无效值）
      2) 再批量算平均值
      3) 最后计算衍生指标（配速、爬升、时长等）

    参数：
        max_distance_m: 最大分析距离（米），超出部分截断以排除冷却步行
    """
    # ---- 第一步：字段提取 ----
    stats = {internal_name: [] for internal_name in RECORD_FIELD_MAP.values()}
    stats['distance_values'] = []  # 单位：km

    for rec in raw_records:
        dist_m = rec.get('distance', 0)
        if dist_m > max_distance_m:
            break

        for fit_key, stat_key in RECORD_FIELD_MAP.items():
            val = rec.get(fit_key)
            if val is None:
                continue
            if fit_key == 'timestamp':
                stats[stat_key].append(val)
            elif val > 0:  # 数值型字段过滤零值/负值
                stats[stat_key].append(val)

        if 'distance' in rec:
            stats['distance_values'].append(dist_m / 1000)

    if not stats['distance_values']:
        return {}

    # ---- 第二步：基础平均值 ----
    _compute_field_averages(stats)

    # ---- 第三步：衍生指标 ----
    _compute_derived_metrics(stats)

    return stats


def _compute_field_averages(stats):
    """为每个数值数组计算平均值，存入 stats 的 avg_* 键。"""
    avg_mappings = [
        ('heart_rates',           'avg_hr'),
        ('speeds',                '_raw_avg_speed'),         # 中间值，后面算配速
        ('temperatures',          'avg_temperature'),
        ('ground_contact_times',  'avg_gct'),
        ('powers',                'avg_power'),
        ('stride_lengths',        'avg_stride_length'),     # 需要缩放
        ('vertical_ratios',       'avg_vertical_ratio'),
        ('cadences',              'avg_cadence'),           # 需要翻倍（半步→整步）
    ]

    for src_key, dest_key in avg_mappings:
        values = stats.get(src_key, [])
        if not values:
            continue
        mean = sum(values) / len(values)

        if src_key == 'cadences':
            # Garmin cadence 以半步为单位，乘 2 得 spm（steps per minute）
            stats[dest_key] = mean * 2
        elif src_key == 'stride_lengths':
            # stride_length 单位由 CORE_METRIC_DEFS 的 scale 统一处理
            stats[dest_key] = mean
        else:
            stats[dest_key] = mean


def _compute_derived_metrics(stats):
    """基于已提取的字段数组，计算复合指标。"""
    hrs = stats.get('heart_rates', [])
    speeds = stats.get('speeds', [])
    distances = stats.get('distances', [])
    altitudes = stats.get('altitudes', [])
    timestamps = stats.get('timestamps', [])

    if hrs:
        stats['max_hr'] = max(hrs)
        # avg_hr 已在 _compute_field_averages 中计算

    if speeds:
        raw_avg = stats.get('_raw_avg_speed', 0)
        stats['avg_pace'] = 1000 / raw_avg / 60 if raw_avg > 0 else 0

    if distances:
        stats['total_distance'] = max(distances)

    if len(timestamps) >= 2:
        stats['duration_seconds'] = (timestamps[-1] - timestamps[0]).total_seconds()

    if len(altitudes) >= 2:
        stats['elevation_gain'] = sum(
            max(0, altitudes[i] - altitudes[i - 1])
            for i in range(1, len(altitudes))
        )

    # 累积用时序列：每条记录相对于起点的秒数，用于每公里节点插值
    if timestamps:
        t0 = timestamps[0]
        stats['_cumulative_time'] = [(t - t0).total_seconds() for t in timestamps]


def compute_per_km_split(stats, max_km=16):
    """
    将连续数据按公里分箱，计算每公里的 HR / pace / cum_avg_HR / cum_avg_pace。

    返回列表，每项一个 dict：
        {
            'km': 公里数 (int),
            'hr': 该公里平均心率 (float|None),
            'pace': 该公里平均配速 min/km (float|None),
            'cum_avg_hr': 到该公里为止的平均心率 (float|None),
            'cum_avg_pace': 到该公里为止的平均配速 (float|None),
        }

    设计要点：
      - 配速过滤范围 [5, 10] min/km，剔除 GPS 漂移导致的异常值
      - cum_avg 使用"到当前距离的所有有效数据"，而非简单移动平均
    """
    distances = stats.get('distance_values', [])
    heart_rates = stats.get('heart_rates', [])
    speeds = stats.get('speeds', [])

    results = []

    for km_num in range(1, max_km + 1):
        hr_in_km = []
        pace_in_km = []      # 当前公里内
        hr_cumulative = []   # 到目前为止累积
        pace_cumulative = []

        for idx, dist in enumerate(distances):
            if dist <= 0:
                continue

            pace_val = _speed_to_pace(speeds[idx]) if idx < len(speeds) else None
            if pace_val is None:
                continue

            # 当前公里区间 (km_num-1, km_num]
            if km_num - 1 < dist <= km_num:
                if idx < len(heart_rates):
                    hr_in_km.append(heart_rates[idx])
                pace_in_km.append(pace_val)

            # 累积区间 (0, km_num]
            if dist <= km_num:
                if idx < len(heart_rates):
                    hr_cumulative.append(heart_rates[idx])
                pace_cumulative.append(pace_val)

        entry = {
            'km': km_num,
            'hr': _mean(hr_in_km),
            'pace': _mean(pace_in_km),
            'cum_avg_hr': _mean(hr_cumulative),
            'cum_avg_pace': _mean(pace_cumulative),
        }
        results.append(entry)

    return results


def get_cumulative_time_at_kms(stats, max_km=20):
    """
    返回每个整数公里节点对应的累积用时（秒）。

    用于底部表格的「累积用时」列。
    当总距离略小于目标公里时（如 15.98km vs 16km），
    容差 50m 内使用最后一条记录的时间。
    """
    distances = stats.get('distance_values', [])
    times = stats.get('_cumulative_time', [])

    if not distances or not times:
        return []

    nodes = []
    for target_km in range(1, max_km + 1):
        found_time = _find_value_at_or_near(distances, times, target_km, tolerance_km=0.05)
        if found_time is not None:
            nodes.append({'km': target_km, 'seconds': found_time})
        else:
            break  # 后续更远的公里也不会有数据了

    return nodes


# =============================================================================
# 辅助工具函数（统计层内部使用）
# =============================================================================

def _speed_to_pace(speed_mps):
    """
    速度 (m/s) → 配速 (min/km)。无效值返回 None。

    过滤条件：只接受合理慢跑配速 [5, 10] min/km，
    排除 GPS 信号丢失或停止走动时的异常值。
    """
    if speed_mps <= 0:
        return None
    pace = 1000 / speed_mps / 60
    return pace if 5 <= pace <= 10 else None


def _mean(values):
    """安全均值：空列表返回 None。"""
    return sum(values) / len(values) if values else None


def _find_value_at_or_near(x_coords, y_values, target_x, tolerance_km=0.05):
    """
    在 x_coords 中找到第一个 >= target_x 的点，返回对应 y。
    如果没有精确匹配但最后一个坐标在容差范围内，则用最后一个 y。
    """
    for i, x in enumerate(x_coords):
        if x >= target_x:
            return y_values[i] if i < len(y_values) else None

    # 容差回退：终点距离目标很近时使用最后一点
    last_x = x_coords[-1] if x_coords else 0
    if last_x >= target_x - tolerance_km:
        last_idx = min(len(y_values) - 1, len(x_coords) - 1)
        return y_values[last_idx]
    return None


def downsample(values, step=DOWNSAMPLE_STEP):
    """等间隔降采样，减少图表数据点数量。"""
    return values[::step]


def compute_y_axis_range(values, padding_factor=1.0):
    """
    计算 Y 轴合理范围，基于 5%-95% 分位数避免极端值拉偏。

    参数：
        padding_factor: 在分位数范围两侧各扩展的比例倍数
    """
    if not values:
        return {'min': 0, 'max': 100}

    sorted_v = sorted(values)
    n = len(sorted_v)
    lo = sorted_v[int(n * 0.05)]
    hi = sorted_v[int(n * 0.95)]
    margin = (hi - lo) * padding_factor

    return {
        'min': max(0, lo - margin),
        'max': hi + margin,
    }


# =============================================================================
# 4. 格式化层 — 数值 → 展示字符串
# =============================================================================

def format_pace(min_per_km):
    """配速格式：6'18\" 表示 6 分 18 秒/公里。"""
    if min_per_km <= 0:
        return "0'00\""
    # 先乘 60 再取整。若写成 int((min_per_km - mins) * 60)，
    # 6.3 会因浮点表示误差变成 377.9999…秒而被截断成 6'17"。
    total_seconds = int(round(min_per_km * 60))
    mins, secs = divmod(total_seconds, 60)
    return f"{mins}'{secs:02d}\""


def format_duration(seconds_total):
    """
    时长格式：
      ≥ 1 小时 → H:MM:SS  （如 1:41:52）
      < 1 小时 → M:SS     （如 12:31）
      < 1 分钟 → Xs       （如 30s）
    """
    if seconds_total <= 0:
        return "0s"

    h = int(seconds_total // 3600)
    m = int((seconds_total % 3600) // 60)
    s = int(seconds_total % 60)

    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    if m > 0:
        return f"{m}:{s:02d}"
    return f"{s}s"


def format_metric_value(value, metric_def):
    """
    根据 CORE_METRIC_DEFS 中的 fmt/scale 定义，将数值转为展示字符串。
    缺失/零值统一显示 '-'。
    """
    if value is None or value == 0:
        return '-'

    v = value * metric_def.get('scale', 1) if metric_def.get('scale') else value
    fmt = metric_def['fmt']

    if fmt == 'duration':
        return format_duration(v)
    if fmt == 'pace':
        return format_pace(v)
    return fmt.format(v)


def format_metric_diff(old_val, new_val, metric_def):
    """
    计算并格式化两个值的差异（new - old）。

    规则：
      - 任一缺失 → 空字符串
      - 差异绝对值低于精度阈值 → 隐藏（避免无意义噪声）
      - 时长差异 → 显示秒数（如 +75s 或 -75s）
      - 配速差异 → 显示秒数（如 +9s 或 -9s）
      - 其他数值 → 按 fmt 精度显示符号+数值
      - 对于显示值相同但实际有微小差异的指标，显示更精确的差异：
          * 平均心率（avg_hr）: 显示两位小数（+0.11 bpm）
          * 平均触地时间（avg_gct）: 显示一位小数，阈值 0.05 ms
          * 平均垂直比例（avg_vertical_ratio）: 显示两位小数（+0.05 %）
          * 平均步频（avg_cadence）: 显示一位小数（+0.5 spm）
          * 最高心率（max_hr）: 显示两位小数（+0.11 bpm）
          * 平均功率（avg_power）: 显示一位小数（+0.5 W）
          * 温度（avg_temperature）: 显示两位小数（+0.05 °C）
          * 平均步幅（avg_stride_length）: 显示两位小数（+0.05 cm）
          * 累计爬升（elevation_gain）: 显示两位小数（+0.05 m）
    """
    if old_val is None or new_val is None or (old_val == 0 and new_val == 0):
        return ''

    scale = metric_def.get('scale', 1)
    diff = (new_val * scale) - (old_val * scale)
    fmt = metric_def['fmt']
    key = metric_def.get('key')

    # --- 各类型的差异阈值和格式化 ---
    if fmt == 'duration':
        return f"{diff:+.0f}s" if abs(diff) >= 5 else ''

    if fmt == 'pace':
        sec_diff = int(round(diff * 60))
        return f"{sec_diff:+d}s" if abs(sec_diff) > 0 else ''

    # 特殊指标：显示更精确的差异（避免因显示值相同而隐藏）
    if key == 'avg_hr':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} bpm"
    if key == 'avg_gct':
        if abs(diff) < 0.05:   # 避免显示 +0.0 ms
            return ''
        return f"{diff:+.1f} ms"
    if key == 'avg_vertical_ratio':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} %"
    if key == 'avg_cadence':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.1f} spm"
    if key == 'max_hr':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} bpm"
    if key == 'avg_power':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.1f} W"
    if key == 'avg_temperature':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} °C"
    if key == 'avg_stride_length':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} cm"
    if key == 'elevation_gain':
        if abs(diff) < 1e-6:
            return ''
        return f"{diff:+.2f} m"

    # 通用数值：从格式串推断精度阈值
    precision = _extract_format_precision(fmt)
    if abs(diff) < precision:
        return ''
    return _signed_format(diff, fmt)


def format_km_hr_diff(hr_old, hr_new):
    """
    每公里心率的差异格式化。
    对四舍五后的整数求差，确保与显示值一致。
    """
    d = round(hr_new) - round(hr_old)
    return f"<span class='diff'>{d:+.0f}</span>" if abs(d) >= 1 else ''


def format_km_pace_diff(pace_old, pace_new):
    """
    每公里配速的差异格式化（单位：秒）。
    """
    d = pace_new - pace_old
    if abs(d) < 0.01:
        return ''
    sec = int(round(d * 60))
    return f"<span class='diff'>{sec:+d}s</span>"


def format_km_cumtime_diff(seconds_old, seconds_new):
    """
    每公里节点累积用时的差异格式化。
    """
    d = int(round(seconds_new - seconds_old))
    return f"<span class='diff'>{d:+d}s</span>" if abs(d) >= 1 else ''


# =============================================================================
# 格式化层辅助函数
# =============================================================================

def _extract_format_precision(fmt_str):
    """从如 '{:.2f}' 的格式串中提取最小精度（如 0.01）。"""
    match = re.search(r'\.(\d+)f', fmt_str)
    if match:
        digits = int(match.group(1))
        return float(f'1e-{digits}')
    return 1e-6


def _signed_format(value, fmt_str):
    """带符号格式化数值，确保正数也带 + 号。"""
    try:
        formatted = fmt_str.format(value)
        if formatted.startswith('-') or formatted.startswith('+'):
            return formatted
        return f"+{formatted}"
    except (ValueError, TypeError):
        return f"{value:+}"


def short_date(date_str):
    """
    将 YYYYMMDD 格式的日期字符串转换为 MMDD 格式（去掉年份）。
    例如：'20260404' → '0404'
    """
    if len(date_str) == 8 and date_str.isdigit():
        return date_str[4:]  # 去掉前4位年份
    return date_str


# =============================================================================
# 5. 图表生成层 — 统计数据 → Chart.js JS 代码
# =============================================================================

def build_all_chart_scripts(stats1, stats2, date1, date2):
    """
    根据图表配置生成所有图表的 JavaScript 代码片段列表。

    每个 CHART_DEF 产生一段 `new Chart(...)` 代码，
    最终由 HTML 模板拼入 `<script>` 标签。
    """
    dist1 = downsample(stats1['distance_values'])
    dist2 = downsample(stats2['distance_values'])
    scripts = []

    for cfg in CHART_DEFS:
        js = _build_one_comparison_chart(cfg, stats1, stats2, dist1, dist2, date1, date2)
        if js:
            scripts.append(js)

    return scripts


def _build_one_comparison_chart(cfg, s1, s2, dist1, dist2, date1, date2):
    """
    为单个图表配置生成双线对比图 JS。

    流程：
      1) 取原始数据 → 可选 filter_fn 过滤 → 降采样
      2) 组装 {x: distance, y: value} 点集
      3) 计算联合 Y 轴范围
      4) 渲染 Chart.js 初始化代码
    """
    key = cfg['data_key']
    raw1 = downsample(s1[key])
    raw2 = downsample(s2[key])

    filter_fn = cfg.get('filter_fn')
    vals1 = [filter_fn(v) for v in raw1] if filter_fn else list(raw1)
    vals2 = [filter_fn(v) for v in raw2] if filter_fn else list(raw2)

    valid = [v for v in vals1 + vals2 if v is not None]
    if not valid:
        return ''

    y_range = compute_y_axis_range(valid)

    points1 = [{'x': d, 'y': v} for d, v in zip(dist1, vals1) if v is not None]
    points2 = [{'x': d, 'y': v} for d, v in zip(dist2, vals2) if v is not None]

    return _render_comparison_chart_js(
        chart_id=cfg['id'],
        title=cfg['title'],
        label_old=date1,
        label_new=date2,
        data_json1=json.dumps(points1),
        data_json2=json.dumps(points2),
        y_range=y_range,
        y_label=cfg['y_label'],
        reverse_y=cfg.get('reverse_y', False),
    )


def _render_comparison_chart_js(chart_id, title, label_old, label_new,
                                data_json1, data_json2, y_range, y_label, reverse_y):
    """渲染一个标准双线对比图的 Chart.js 初始化 JS 字符串（模板见 chart.js.tmpl）。"""
    return _load_template('chart.js.tmpl').substitute(
        chart_id=chart_id,
        label_old=label_old,
        label_new=label_new,
        data_json1=data_json1,
        data_json2=data_json2,
        y_min=f"{y_range['min']:.1f}",
        y_max=f"{y_range['max']:.1f}",
        y_label=y_label,
        reverse_y=str(reverse_y).lower(),
    )


# =============================================================================
# 6. HTML 构建层 — 将所有数据组装成最终 HTML 文件
# =============================================================================

def generate_report(run1_raw, run2_raw, date1, date2, output_path):
    """
    主编排函数：解析 → 统计 → 构建 → 写文件。

    这是唯一对外暴露的高层接口，main() 只调用此函数。
    """
    gen_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 短日期格式（去掉年份）
    short_date1 = short_date(date1)
    short_date2 = short_date(date2)

    # --- 统计 ---
    stats1 = compute_run_stats(run1_raw['records'])
    stats2 = compute_run_stats(run2_raw['records'])

    # --- 图表 JS ---
    chart_scripts = build_all_chart_scripts(stats1, stats2, short_date1, short_date2)

    # --- 表格行 ---
    core_metric_rows = _build_core_metric_rows(stats1, stats2)
    km_data_rows = _build_per_km_data_rows(stats1, stats2, short_date1, short_date2)

    # --- 组装完整 HTML ---
    html = _assemble_full_html(short_date1, short_date2, core_metric_rows, km_data_rows,
                               chart_scripts, gen_timestamp)

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(html)


def _build_core_metric_rows(stats1, stats2):
    """
    生成左侧核心指标对比表格的 <tr> 行 HTML 列表。

    每行包含：指标名 | 旧值 | 新值 | 差异(new - old)
    更优值自动添加 .better CSS 类（蓝色高亮）。
    """
    rows = []

    for m in CORE_METRIC_DEFS:
        v_old = stats1.get(m['key'])
        v_new = stats2.get(m['key'])

        better_cls = m.get('lower_is_better')
        cls_old = _better_class(v_old, v_new, better_cls) if better_cls is not None else ''
        cls_new = _better_class(v_new, v_old, better_cls) if better_cls is not None else ''
        diff_html = format_metric_diff(v_old, v_new, m)

        rows.append(
            f"<tr>"
            f"<td>{m['label']}</td>"
            f"<td class='{cls_old}'>{format_metric_value(v_old, m)}</td>"
            f"<td class='{cls_new}'>{format_metric_value(v_new, m)}</td>"
            f"<td class='diff'>{diff_html}</td>"
            f"</tr>"
        )

    return rows


def _build_per_km_data_rows(stats1, stats2, date1, date2):
    """
    生成底部每公里数据表格的 <tr> 行 HTML 列表。

    表格列结构（共 16 列）：公里编号 + 5 个分组 × 3 列（date1 / date2 / 差异）。
    分组定义见 KM_COLUMN_GROUPS，cum=True 的分组单元格加 col-cum 浅蓝底。

    双数公里行添加 .row-even 类实现隔行变色。
    """
    splits1 = compute_per_km_split(stats1)
    splits2 = compute_per_km_split(stats2)
    time_nodes1 = get_cumulative_time_at_kms(stats1)
    time_nodes2 = get_cumulative_time_at_kms(stats2)

    rows = []
    max_km = min(len(splits1), len(splits2))

    for i in range(max_km):
        k1 = splits1[i]
        k2 = splits2[i]

        row_class = 'row-even' if k1['km'] % 2 == 0 else ''
        tr_attr = f" class='{row_class}'" if row_class else ''

        # --- 心率 ---
        hr1 = f"{k1['hr']:.0f}" if k1['hr'] else '-'
        hr2 = f"{k2['hr']:.0f}" if k2['hr'] else '-'
        hr_diff = format_km_hr_diff(k1['hr'], k2['hr']) if k1['hr'] and k2['hr'] else ''

        # --- 配速 ---
        p1 = format_pace(k1['pace']) if k1['pace'] else '-'
        p2 = format_pace(k2['pace']) if k2['pace'] else '-'
        p_diff = format_km_pace_diff(k1['pace'], k2['pace']) if k1['pace'] and k2['pace'] else ''

        # --- 累积平均心率（col-cum 背景）---
        chr1 = f"{k1['cum_avg_hr']:.0f}" if k1['cum_avg_hr'] else '-'
        chr2 = f"{k2['cum_avg_hr']:.0f}" if k2['cum_avg_hr'] else '-'
        chr_diff = format_km_hr_diff(k1['cum_avg_hr'], k2['cum_avg_hr']) if k1['cum_avg_hr'] and k2['cum_avg_hr'] else ''

        # --- 累积平均配速（col-cum 背景）---
        cp1 = format_pace(k1['cum_avg_pace']) if k1['cum_avg_pace'] else '-'
        cp2 = format_pace(k2['cum_avg_pace']) if k2['cum_avg_pace'] else ''
        cp_diff = format_km_pace_diff(k1['cum_avg_pace'], k2['cum_avg_pace']) if k1['cum_avg_pace'] and k2['cum_avg_pace'] else ''

        # --- 累积用时 ---
        ct1 = time_nodes1[i]['seconds'] if i < len(time_nodes1) else None
        ct2 = time_nodes2[i]['seconds'] if i < len(time_nodes2) else None
        ctm1 = format_duration(int(ct1)) if ct1 is not None else '-'
        ctm2 = format_duration(int(ct2)) if ct2 is not None else ''
        ctm_diff = format_km_cumtime_diff(ct1, ct2) if (ct1 is not None and ct2 is not None) else ''

        # 每组 3 个单元格（date1 / date2 / 差异），顺序必须与 KM_COLUMN_GROUPS 一致
        group_cells = [
            [hr1, hr2, hr_diff],
            [p1, p2, p_diff],
            [chr1, chr2, chr_diff],
            [cp1, cp2, cp_diff],
            [ctm1, ctm2, ctm_diff],
        ]
        assert len(group_cells) == len(KM_COLUMN_GROUPS), '列分组数量与 KM_COLUMN_GROUPS 不一致'

        cells = [f"<td>{k1['km']}km</td>"]
        for group, vals in zip(KM_COLUMN_GROUPS, group_cells):
            cum = " class='col-cum'" if group['cum'] else ''  # 累积列背景色标记
            cells.append(''.join(f"<td{cum}>{v}</td>" for v in vals))

        rows.append(f"<tr{tr_attr}>" + ''.join(cells) + "</tr>")

    return rows


def _build_chart_cards():
    """由 CHART_DEFS 生成图表卡片 HTML，保证 canvas id 与 JS 侧一一对应。"""
    cards = []
    for cfg in CHART_DEFS:
        cards.append(
            f"<div class='chart-card'>"
            f"<div class='chart-title'>{cfg['title']}</div>"
            f"<canvas id='{cfg['id']}'></canvas></div>"
        )
    return '\n                    '.join(cards)


def _build_km_group_headers():
    """由 KM_COLUMN_GROUPS 生成每公里表头第一行的分组 <th>。"""
    cells = []
    for g in KM_COLUMN_GROUPS:
        cum = " class='col-cum'" if g['cum'] else ''
        cells.append(f"<th colspan='3'{cum}>{g['label']}</th>")
    return '\n                        '.join(cells)


def _build_th_date_row(date1, date2):
    """生成每公里表头第二行的日期子列 <th>，顺序与 KM_COLUMN_GROUPS 一致。"""
    cells = []
    for g in KM_COLUMN_GROUPS:
        cum = " class='col-cum'" if g['cum'] else ''
        cells.append(f"<th{cum}>{date1}</th><th{cum}>{date2}</th><th{cum}>差异</th>")
    return ''.join(cells)


def _load_template(filename):
    """读取 templates/ 下的模板文件，返回 string.Template 实例。"""
    with open(os.path.join(TEMPLATE_DIR, filename), encoding='utf-8') as f:
        return Template(f.read())


def _assemble_full_html(date1, date2, core_rows, km_rows,
                         chart_scripts, gen_timestamp):
    """
    将所有组件拼装为完整的 HTML 文档字符串。

    页面骨架来自 report_template.html；图表卡片与每公里表头分别由
    CHART_DEFS / KM_COLUMN_GROUPS 生成，避免与图表 JS 侧重复定义。
    """
    return _load_template('report_template.html').substitute(
        date1=date1,
        date2=date2,
        gen_timestamp=gen_timestamp,
        chart_cards=_build_chart_cards(),
        core_rows=''.join(core_rows),
        km_group_headers=_build_km_group_headers(),
        th_date_row=_build_th_date_row(date1, date2),
        km_rows=''.join(km_rows),
        chart_scripts=''.join(chart_scripts),
    )


# =============================================================================
# 7. 辅助函数（HTML 层）
# =============================================================================

def _better_class(val_a, val_b, lower_is_better):
    """
    判断 val_a 是否比 val_b 更优，返回对应的 CSS 类名。

    lower_is_b=True 时，越小越好（如心率、配速、GCT）
    lower_is_b=None 或 False 时，越大越好（如步频、功率）
    """
    if val_a is None or val_b is None:
        return ''
    return 'better' if (val_a < val_b if lower_is_better else val_a > val_b) else ''


# =============================================================================
# 8. 入口
# =============================================================================

def update_index_html(stats_newer, date_str, output_file):
    """
    将最新一次跑步的核心指标插入 jogging/index.html 表格的第一行。

    如果同名日期已存在则跳过，避免重复。
    """
    index_path = os.path.join(BASE_DIR, 'index.html')
    if not os.path.exists(index_path):
        print("警告: jogging/index.html 不存在，跳过索引更新")
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 防止重复：如果该日期已在表格中则跳过
    if f'href="{date_str}.html"' in content or f'>{date_str}<' in content:
        print(f"索引: {date_str} 已存在于 index.html，跳过")
        return

    # 开始时间：从 session 或首条 record 的 timestamp 提取 HH:MM
    start_time = _extract_start_time(stats_newer)

    # 构建新行，字段顺序与 index.html 表头一致
    cells = [f"<td class='date-cell'><a href='{output_file}'>{date_str}</a></td>", f"<td>{start_time}</td>"]
    for m in CORE_METRIC_DEFS:
        val = stats_newer.get(m['key'])
        cells.append(f"<td>{format_metric_value(val, m)}</td>")

    new_row = f"                <tr>\n                    " + ''.join(cells) + "\n                </tr>"
    # 在 <tbody> 标签后插入新行（作为第一行）
    content = content.replace('<tbody>', '<tbody>\n' + new_row)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已更新: {index_path}")


def _extract_start_time(stats):
    """从 timestamps 列表中提取开始时间 (HH:MM)，自动转为北京时间 (UTC+8)。"""
    from datetime import timedelta
    ts_list = stats.get('timestamps', [])
    if not ts_list:
        return '-'
    t0 = ts_list[0] + timedelta(hours=8)  # UTC → 北京时间
    return t0.strftime('%H:%M')


def main():
    """
    CLI 入口：

      1. 扫描 data/ 目录下的 .fit 文件（按名称排序）
      2. 取最新的两个进行对比
      3. 输出 HTML 报告（以较新日期命名）
      4. 自动将较新的数据行插入 index.html 索引表
    """
    data_dir = DATA_DIR
    fit_files = sorted(f for f in os.listdir(data_dir) if f.endswith('.fit'))

    if len(fit_files) < 2:
        print("需要至少两个 FIT 文件")
        return

    # 取最早和次早（排序后前两个），date1=旧 date2=新
    name1, path1 = fit_files[0].split('.')[0], os.path.join(data_dir, fit_files[0])
    name2, path2 = fit_files[1].split('.')[0], os.path.join(data_dir, fit_files[1])

    print(f"解析: {path1}")
    raw1 = parse_fit_file(path1)

    print(f"解析: {path2}")
    raw2 = parse_fit_file(path2)

    output_file = f"{max(name1, name2)}.html"
    output_path = os.path.join(BASE_DIR, output_file)
    print(f"生成: {output_path}")

    generate_report(raw1, raw2, name1, name2, output_path)

    # 更新 index.html：用较新那次的数据
    stats_newer = compute_run_stats(raw2['records'])
    newer_date = max(name1, name2)  # 较新日期
    update_index_html(stats_newer, newer_date, output_file)

    print("完成!")


if __name__ == '__main__':
    main()
