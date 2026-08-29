"""测试数据构造工具。

仓库里没有 .fit 文件（data/ 被 gitignore，且含 GPS 隐私数据），
所以所有测试都用这里合成的记录，不依赖真实数据。
"""

from datetime import datetime, timedelta

# 合成数据的出发时间（UTC；报表里的开始时间会再 +8h 转北京时间）
T0 = datetime(2026, 5, 11, 6, 0, 0)


def make_records(hr_base=125, pace_s=380, step_m=50, n=320):
    """
    合成 FIT record 列表（键名与 RECORD_FIELD_MAP 一致）。

    参数：
        hr_base: 起始心率，之后每条 +0.09 线性上升
        pace_s:  每公里秒数（380 → 6'20"/km）
        step_m:  每条记录的距离间隔（米）
        n:       记录条数

    默认 n=320 & step_m=50 → 全程 16.0 km，正好是脚本的截断上限。
    """
    records = []
    for i in range(n):
        dist_m = (i + 1) * step_m
        records.append({
            'distance': dist_m,
            'enhanced_speed': 1000 / pace_s,          # m/s，恒定配速
            'heart_rate': hr_base + i * 0.09,
            'enhanced_altitude': 50 + (i % 40),       # 锯齿状，制造爬升
            'cadence': 90 + (i % 5),                  # 半步，脚本内部会 ×2
            'temperature': 24.5,
            'stance_time': 245 + (i % 10),
            'power': 210 + (i % 15),
            'step_length': 950 + (i % 20),
            'vertical_ratio': 8.1,
            'timestamp': T0 + timedelta(seconds=dist_m / 1000 * pace_s),
        })
    return records
