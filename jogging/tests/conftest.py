"""pytest 公共配置：导入路径、依赖兜底、共享 fixture。"""

import os
import sys
import types

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
JOGGING_DIR = os.path.dirname(TESTS_DIR)

# 让测试模块能 import 上级目录的 analyze_jogging，以及同目录的 helpers
for path in (JOGGING_DIR, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

# --- fitparse 兜底 ---
# 仓库不含 .fit 文件，parse_fit_file 从不被测试调用；这里注入最小桩，
# 只是为了让 analyze_jogging 能被导入（它在模块顶层 import fitparse）。
# 装了真实依赖时不会走到这里。
try:
    import fitparse  # noqa: F401
except ImportError:  # pragma: no cover
    _stub = types.ModuleType('fitparse')
    _stub.FitFile = object
    sys.modules['fitparse'] = _stub

import analyze_jogging  # noqa: E402  必须在桩注入之后
from helpers import make_records  # noqa: E402


@pytest.fixture
def run_a():
    """较慢的一次跑步：配速 6'20"/km，心率起点 122。"""
    return {'records': make_records(hr_base=122, pace_s=380)}


@pytest.fixture
def run_b():
    """较快的一次跑步：配速 6'06"/km，心率起点 126。"""
    return {'records': make_records(hr_base=126, pace_s=366)}


@pytest.fixture
def stats_a(run_a):
    return analyze_jogging.compute_run_stats(run_a['records'])


@pytest.fixture
def stats_b(run_b):
    return analyze_jogging.compute_run_stats(run_b['records'])
