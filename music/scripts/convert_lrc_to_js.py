#!/usr/bin/env python3
"""批量将 Wonderful World(Live) 目录下的 .lrc 转换为对应 .js 文件。

转换规则（与仓库已有的转换一致）：
    window.LYRICS = '<转义后的歌词内容>';

其中开头的 JSON 元数据行（{"t":... 作词/作曲信息）属于下载时混入的冗余内容，
并非歌词，故只保留真正的 [mm:ss.xx] 歌词行。
"""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SONGS_DIR = SCRIPT_DIR.parent / "songs"
ALBUM_DIR = SONGS_DIR / "Wonderful World(Live)"

# 匹配 LRC 时间戳行： [mm:ss.xx] 文本
LRC_LINE_RE = re.compile(r'^\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]\s*.*$')
# 匹配开头的 JSON 元数据行（下载混入的作词/作曲信息）
JSON_META_RE = re.compile(r'^\{\s*"t"\s*:')


def lrc_to_js_content(lrc_text):
    """将 LRC 文本转为 JS 赋值内容（不含外层引号）"""
    return lrc_text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')


def convert_one(lrc_file):
    text = lrc_file.read_text(encoding='utf-8')

    kept = []
    for line in text.split('\n'):
        if JSON_META_RE.match(line):
            continue  # 跳过 JSON 元数据行
        kept.append(line)

    # 去掉首尾的空行，但保留歌词内部必要的换行
    while kept and kept[0] == '':
        kept.pop(0)
    while kept and kept[-1] == '':
        kept.pop()

    lrc_only = '\n'.join(kept)
    js_content = f"window.LYRICS = '{lrc_to_js_content(lrc_only)}';\n"

    js_file = lrc_file.with_suffix('.js')
    js_file.write_text(js_content, encoding='utf-8')
    return js_file


def main():
    if not ALBUM_DIR.exists():
        print(f"错误: 目录不存在 {ALBUM_DIR}")
        return

    lrc_files = sorted(ALBUM_DIR.glob('*.lrc'))
    print(f"找到 {len(lrc_files)} 个 .lrc 文件")

    skipped = 0
    for lrc_file in lrc_files:
        js_file = lrc_file.with_suffix('.js')
        if js_file.exists():
            print(f"  [跳过] {lrc_file.name} (已有同名 .js)")
            skipped += 1
            continue
        convert_one(lrc_file)
        print(f"  [生成] {js_file.name}")

    print("完成。")


if __name__ == '__main__':
    main()
