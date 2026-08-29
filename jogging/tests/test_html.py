"""HTML 组装层测试（第 6 层）：模板渲染、表格行、配置一致性。

核心目标是守住几条“结构不变式”——它们一旦被破坏，页面会静默出错
（而不是崩溃），所以必须有测试兜住。
"""

import os
import re

import pytest

import analyze_jogging
from analyze_jogging import (
    CHART_DEFS,
    CORE_METRIC_DEFS,
    KM_COLUMN_GROUPS,
    _assemble_full_html,
    _build_chart_cards,
    _build_core_metric_rows,
    _build_km_group_headers,
    _build_per_km_data_rows,
    _build_th_date_row,
    build_all_chart_scripts,
)

CUM_GROUPS = [g for g in KM_COLUMN_GROUPS if g['cum']]
EXPECTED_TDS = 1 + len(KM_COLUMN_GROUPS) * 3   # 公里编号 + 每组 3 列


def build_report(stats_a, stats_b, date1='0407', date2='0511'):
    """拼一份完整报告 HTML，各测试共用一个构造入口。"""
    return _assemble_full_html(
        date1, date2,
        _build_core_metric_rows(stats_a, stats_b),
        _build_per_km_data_rows(stats_a, stats_b, date1, date2),
        build_all_chart_scripts(stats_a, stats_b, date1, date2),
        '2026-05-11 20:00',
    )


# ------------------------------------------------------- _build_chart_cards

def test_chart_cards_cover_every_chart_def():
    html = _build_chart_cards()
    assert html.count('<canvas') == len(CHART_DEFS)
    for cfg in CHART_DEFS:
        assert f"id='{cfg['id']}'" in html
        assert cfg['title'] in html


# --------------------------------------------- 每公里表头（由 KM_COLUMN_GROUPS 驱动）

def test_km_group_headers_match_column_groups():
    headers = _build_km_group_headers()
    assert headers.count('<th') == len(KM_COLUMN_GROUPS)
    assert headers.count("class='col-cum'") == len(CUM_GROUPS)
    assert headers.count('colspan=') == len(KM_COLUMN_GROUPS)


def test_th_date_row_has_three_cells_per_group():
    row = _build_th_date_row('0407', '0511')
    assert row.count('<th') == len(KM_COLUMN_GROUPS) * 3
    assert row.count("class='col-cum'") == len(CUM_GROUPS) * 3
    assert row.count('0407') == len(KM_COLUMN_GROUPS)
    assert row.count('0511') == len(KM_COLUMN_GROUPS)


# -------------------------------------------------- _build_per_km_data_rows

def test_per_km_rows_column_layout(stats_a, stats_b):
    rows = _build_per_km_data_rows(stats_a, stats_b, '0407', '0511')
    assert len(rows) == 16
    for i, row in enumerate(rows, start=1):
        assert row.count('<td') == EXPECTED_TDS
        assert row.count("class='col-cum'") == len(CUM_GROUPS) * 3
        assert f'>{i}km<' in row


def test_per_km_rows_even_km_highlighted(stats_a, stats_b):
    """双数公里行加 .row-even 实现隔行变色。"""
    rows = _build_per_km_data_rows(stats_a, stats_b, '0407', '0511')
    for i, row in enumerate(rows, start=1):
        assert ("class='row-even'" in row) == (i % 2 == 0)


def test_group_count_mismatch_raises(stats_a, stats_b, monkeypatch):
    """KM_COLUMN_GROUPS 与实际单元格组数不一致时应立即报错，而不是静默错位。"""
    monkeypatch.setattr(
        analyze_jogging, 'KM_COLUMN_GROUPS',
        KM_COLUMN_GROUPS + [{'label': '多出来的一组', 'cum': False}],
    )
    with pytest.raises(AssertionError):
        _build_per_km_data_rows(stats_a, stats_b, '0407', '0511')


# --------------------------------------------------- _build_core_metric_rows

def test_core_metric_rows_cover_all_defs(stats_a, stats_b):
    rows = _build_core_metric_rows(stats_a, stats_b)
    assert len(rows) == len(CORE_METRIC_DEFS)
    for row, metric in zip(rows, CORE_METRIC_DEFS):
        assert metric['label'] in row


# --------------------------------------------------------- 整页结构不变式

def test_canvas_ids_match_generated_chart_js(stats_a, stats_b):
    """防回归：页面里的 canvas 必须与生成的 Chart.js 一一对应。

    曾经 <canvas> 是硬编码在 HTML 里的，往 CHART_DEFS 加图表时 JS 会生成、
    但页面没有对应 canvas，getElementById 取到 null 会让整段 <script> 抛错，
    导致所有图表一起失效。
    """
    html = build_report(stats_a, stats_b)
    canvas_ids = set(re.findall(r"<canvas id='([^']+)'", html))
    js_ids = set(re.findall(r"getElementById\('([^']+)'\)", html))
    assert canvas_ids == js_ids
    assert canvas_ids == {cfg['id'] for cfg in CHART_DEFS}


def test_no_unsubstituted_placeholders(stats_a, stats_b):
    """模板里若有未替换的 $xxx，说明 substitute 漏传了变量。"""
    html = build_report(stats_a, stats_b)
    assert re.findall(r'\$[a-z_][a-z0-9_]*', html) == []


def test_report_links_static_assets(stats_a, stats_b):
    html = build_report(stats_a, stats_b)
    assert 'static/compare.css' in html
    assert 'static/favicon.ico' in html
    assert 'href="index.html"' in html   # 返回首页


def test_report_has_no_inline_style_block(stats_a, stats_b):
    """样式必须外链到 compare.css，不应再有内联 <style>。"""
    html = build_report(stats_a, stats_b)
    assert '<style' not in html


def test_every_chart_script_is_emitted(stats_a, stats_b):
    html = build_report(stats_a, stats_b)
    assert html.count('new Chart(') == len(CHART_DEFS)


# ---------------------------------------------------------- 配置与模板完整性

def test_chart_def_ids_are_unique():
    ids = [cfg['id'] for cfg in CHART_DEFS]
    assert len(ids) == len(set(ids))


def test_chart_def_data_keys_exist_in_stats(stats_a):
    for cfg in CHART_DEFS:
        assert cfg['data_key'] in stats_a, f"stats 里没有 {cfg['data_key']}"


def test_core_metric_defs_well_formed():
    keys = [m['key'] for m in CORE_METRIC_DEFS]
    assert len(keys) == len(set(keys))
    for metric in CORE_METRIC_DEFS:
        assert metric['label']
        assert metric['fmt'] in ('duration', 'pace') or '{' in metric['fmt']


def test_template_files_exist():
    for name in ('report_template.html', 'chart.js.tmpl'):
        path = os.path.join(analyze_jogging.TEMPLATE_DIR, name)
        assert os.path.isfile(path), f'模板缺失: {path}'
