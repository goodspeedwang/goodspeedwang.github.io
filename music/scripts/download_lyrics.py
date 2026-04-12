#!/usr/bin/env python3
"""
歌词下载脚本
使用 lrclib.net API 自动下载歌词并保存为 .lrc 文件
歌词文件保存在对应的 MP3 同目录下

使用方法:
    python3 download_lyrics.py [--dry-run]
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# 配置
SCRIPT_DIR = Path(__file__).parent
MUSIC_DIR = SCRIPT_DIR.parent
SONGS_DIR = MUSIC_DIR / "songs"
ALBUM_JS_PATH = MUSIC_DIR / "album.js"

# lrclib API
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
LRCLIB_GET_URL = "https://lrclib.net/api/get"

# 请求间隔（秒），避免请求过快
REQUEST_DELAY = 0.5


def parse_album_js(file_path):
    """解析 album.js 文件，提取专辑和歌曲信息"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则提取每个专辑对象
    # 匹配 { name: "...", artist: "...", cover: "...", songs: [...] }
    pattern = r'\{\s*name:\s*"([^"]+)",\s*artist:\s*"([^"]+)",\s*cover:\s*"([^"]+)",\s*songs:\s*\[([^\]]*)\]\s*\}'

    albums = []
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        artist = match.group(2)
        cover = match.group(3)
        songs_str = match.group(4)

        # 解析歌曲列表
        songs = re.findall(r'"([^"]+)"', songs_str)

        albums.append({
            'name': name,
            'artist': artist,
            'cover': cover,
            'songs': songs
        })

    return albums


def sanitize_filename(name):
    """清理文件名中的特殊字符"""
    return name.replace('/', '_').replace('\\', '_')


def clean_song_name(name):
    """清理歌曲名，去掉常见的后缀"""
    # 去掉 " - Live"、" - ..." 等后缀
    import re
    # 匹配 " - Live"、" - 电影..."、" - 电视剧..." 等
    cleaned = re.sub(r'\s*-\s*(Live|電影|电影|電視劇|电视剧|主題曲|插曲|國語|国语).*$', '', name, flags=re.IGNORECASE)
    return cleaned.strip()


def search_lyrics(song_name, artist, album_name=None):
    """搜索歌词"""
    # 清理歌曲名
    clean_name = clean_song_name(song_name)
    
    # 尝试多种搜索方式
    search_queries = [
        f"{clean_name} {artist}",  # 歌曲名 + 歌手
        f"{song_name} {artist}",   # 原始歌曲名 + 歌手
        clean_name,                 # 只用歌曲名
    ]
    
    for query in search_queries:
        url = f"{LRCLIB_SEARCH_URL}?q={urllib.parse.quote(query)}"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))

                if not data:
                    continue

                # 优先选择有同步歌词的结果
                for result in data:
                    if result.get('syncedLyrics'):
                        # 检查歌曲名和歌手是否匹配
                        if artist.lower() in result.get('artistName', '').lower():
                            return result

                # 如果没有同步歌词，选择普通歌词
                for result in data:
                    if result.get('plainLyrics'):
                        if artist.lower() in result.get('artistName', '').lower():
                            return result

                # 返回第一个结果
                return data[0]

        except urllib.error.URLError:
            continue
        except Exception:
            continue
    
    return None


def get_lyrics_direct(artist, album, title):
    """直接获取歌词"""
    url = f"{LRCLIB_GET_URL}/{urllib.parse.quote(artist)}/{urllib.parse.quote(album)}/{urllib.parse.quote(title)}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data if data.get('syncedLyrics') or data.get('plainLyrics') else None
    except:
        return None


def lrc_to_js_content(lrc_text):
    """将 LRC 文本转为 JS 赋值内容（不含外层引号）"""
    return lrc_text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')


def save_lyrics(lrc_file, lyrics):
    """保存歌词为 .lrc 和 .js 文件"""
    # 保存 .lrc
    with open(lrc_file, 'w', encoding='utf-8') as f:
        f.write(lyrics)

    # 保存同名 .js（包含解析后的数据）
    js_file = lrc_file.with_suffix('.js')
    js_content = f"window.LYRICS = '{lrc_to_js_content(lyrics)}';\n"
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    """下载所有歌词"""
    total = 0
    success = 0
    skipped = 0
    failed = 0

    for album in albums:
        album_name = album['name']
        artist = album['artist']
        album_dir = SONGS_DIR / sanitize_filename(album_name)

        print(f"\n专辑: {album_name} - {artist}")

        for song_name in album['songs']:
            total += 1
            song_file = album_dir / f"{sanitize_filename(song_name)}.mp3"
            lrc_file = album_dir / f"{sanitize_filename(song_name)}.lrc"

            # 检查歌词文件是否已存在
            if lrc_file.exists():
                print(f"  [跳过] {song_name} (歌词已存在)")
                skipped += 1
                continue

            # 检查歌曲文件是否存在
            if not song_file.exists():
                print(f"  [跳过] {song_name} (MP3 文件不存在)")
                skipped += 1
                continue

            if dry_run:
                print(f"  [将下载] {song_name}")
                continue

            print(f"  [下载] {song_name}...", end=" ")

            # 搜索歌词
            result = search_lyrics(song_name, artist, album_name)

            if not result:
                # 尝试直接获取
                result = get_lyrics_direct(artist, album_name, song_name)

            if result:
                # 优先使用同步歌词，否则使用普通歌词
                lyrics = result.get('syncedLyrics') or result.get('plainLyrics')

                if lyrics:
                    # 保存歌词文件 (.lrc + .js)
                    save_lyrics(lrc_file, lyrics)
                    print(f"✓")
                    success += 1
                else:
                    print(f"✗ (无歌词内容)")
                    failed += 1
            else:
                print(f"✗ (未找到)")
                failed += 1

            # 请求间隔
            time.sleep(REQUEST_DELAY)

    return total, success, skipped, failed



def main():
    import argparse

    parser = argparse.ArgumentParser(description='下载歌词')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要下载的歌词，不实际下载')
    args = parser.parse_args()

    print("=" * 50)
    print("歌词下载脚本")
    print("=" * 50)

    # 检查目录
    if not SONGS_DIR.exists():
        print(f"错误: 歌曲目录不存在 {SONGS_DIR}")
        return

    if not ALBUM_JS_PATH.exists():
        print(f"错误: album.js 文件不存在 {ALBUM_JS_PATH}")
        return

    # 解析专辑信息
    print(f"\n正在解析专辑信息...")
    albums = parse_album_js(ALBUM_JS_PATH)

    if not albums:
        print("错误: 未找到任何专辑信息")
        return

    print(f"找到 {len(albums)} 张专辑")

    # 下载歌词
    print(f"\n开始{'扫描' if args.dry_run else '下载'}歌词...")
    total, success, skipped, failed = download_lyrics(albums, args.dry_run)

    # 统计
    print("\n" + "=" * 50)
    print("下载完成!")
    print(f"总计: {total} 首")
    print(f"成功: {success} 首")
    print(f"跳过: {skipped} 首")
    print(f"失败: {failed} 首")
    print("=" * 50)


if __name__ == '__main__':
    main()