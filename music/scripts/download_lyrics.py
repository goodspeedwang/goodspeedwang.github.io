 #!/usr/bin/env python3
"""
歌词下载脚本
使用多个 API 源自动下载歌词并保存为 .lrc 文件
支持源: lrclib.net, 网易云音乐, QQ音乐, 歌词.ovh

使用方法:
    python3 download_lyrics.py [--dry-run] [--album "专辑名"]
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

# 各歌词源 API
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
LRCLIB_GET_URL = "https://lrclib.net/api/get"
NETEASE_API = "https://music.163.com/api/search/get?s_type=1&limit=5&offset=0="
LYRICS_OVH_API = "https://api.lyrics.ovh/v1/"
# QQ音乐歌词API（通过 c.y.qq.com 接口）
QQ_SEARCH_URL = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w="

# 请求间隔（秒），避免请求过快
REQUEST_DELAY = 0.8


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


# 繁体转简体映射表（常用字）
T2S_MAP = {
    '愛': '爱', '國': '国', '際': '际', '語': '语', '詞': '词',
    '長': '长', '開': '开', '間': '间', '東': '东', '車': '车',
    '專': '专', '業': '业', '為': '为', '學': '学', '習': '习',
    '樂': '乐', '應': '应', '點': '点', '頭': '头', '體': '体',
    '書': '书', '畫': '画', '電': '电', '腦': '脑', '機': '机',
    '門': '门', '關': '关', '鄉': '乡', '場': '场', '動': '动',
    '對': '对', '時': '时', '條': '条', '幾': '几', '並': '并',
    '來': '来', '見': '见', '現': '现', '義': '义', '認': '认',
    '說': '说', '語': '语', '讀': '读', '詩': '诗', '誰': '谁',
    '讓': '让', '這': '这', '進': '进', '遠': '远', '還': '还',
    '邊': '边', '過': '过', '運': '运', '會': '会', '傷': '伤',
    '備': '备', '樂': '乐', '夢': '梦', '與': '与', '雖': '虽',
    '風': '风', '飛': '飞', '馬': '马', '魚': '鱼', '鳥': '鸟',
    '麵': '面', '館': '馆', '園': '园', '圓': '圆', '圖': '图',
    '聲': '声', '聽': '听', '臉': '脸', '舊': '旧', '萬': '万',
    '葉': '叶', '號': '号', '歲': '岁', '歡': '欢', '氣': '气',
    '無': '无', '燈': '灯', '煙': '烟', '愛': '爱', '當': '当',
    '憂': '忧', '懷': '怀', '戀': '恋', '擁': '拥', '斷': '断',
    '親': '亲', '記': '记', '設': '设', '許': '许', '評': '评',
    '詞': '词', '論': '论', '責': '责', '費': '费', '貸': '贷',
    '貿': '贸', '資': '资', '賣': '卖', '質': '质', '輕': '轻',
    '過': '过', '達': '达', '違': '违', '遺': '遗', '鄰': '邻',
    '醉': '醉', '鍾': '钟', '閃': '闪', '陽': '阳', '隨': '随',
    '難': '难', '願': '愿', '類': '类', '離': '离', '韓': '韩',
    '音': '音', '響': '响', '順': '顺', '預': '预', '領': '领',
    '頻': '频', '顆': '颗', '題': '题', '額': '额', '風': '风',
    '飯': '饭', '飾': '饰', '餘': '余', '養': '养', '駕': '驾',
    '髮': '发', '鬧': '闹', '龜': '龟', '戲': '戏', '獨': '独',
    '獎': '奖', '環': '环', '癡': '痴', '確': '确', '禪': '禅',
    '窮': '穷', '競': '竞', '築': '筑', '範': '范', '練': '练',
    '網': '网', '緣': '缘', '總': '总', '縮': '缩', '縱': '纵',
    '繁': '繁', '繼': '继', '續': '续', '羅': '罗', '習': '习',
    '臺': '台', '艷': '艳', '藝': '艺', '處': '处', '複': '复',
    '視': '视', '規': '规', '觀': '观', '調': '调', '講': '讲',
    '購': '购', '費': '费', '質': '质', '變': '变', '讓': '让',
    '豐': '丰', '貝': '贝', '負': '负', '財': '财', '貢': '贡',
    '貴': '贵', '買': '买', '費': '费', '貯': '贮', '貿': '贸',
    '賀': '贺', '賓': '宾', '賒': '赊', '贅': '赘', '贏': '赢',
    '贈': '赠', '贶': '贶', '贇': '贇', '贈': '赠', '贳': '贳',
}


def to_simplified(text):
    """繁体中文转简体中文"""
    for t, s in T2S_MAP.items():
        text = text.replace(t, s)
    return text


def clean_song_name(name):
    """清理歌曲名，去掉常见的后缀"""
    import re
    cleaned = re.sub(r'\s*-\s*(Live|電影|电影|電視劇|电视剧|主題曲|插曲|國語|国语|Encore|Talking).*$', '', name, flags=re.IGNORECASE)
    return cleaned.strip()


def search_lyrics(song_name, artist, album_name=None):
    """搜索歌词，依次尝试多个来源"""
    # 清理歌曲名
    clean_name = clean_song_name(song_name)
    
    # 来源1: lrclib.net（同步/普通歌词）
    result = _search_lrclib(song_name, clean_name, artist)
    if result:
        lyrics = result.get('syncedLyrics') or result.get('plainLyrics')
        if lyrics:
            return lyrics
    
    # 来源2: 网易云音乐 API
    lyrics = _search_netease(clean_name, artist, album_name)
    if lyrics:
        return lyrics
    
    # 来源3: QQ音乐
    lyrics = _search_qq_music(clean_name, artist, album_name)
    if lyrics:
        return lyrics
    
    # 来源4: 歌词.ovh
    lyrics = _search_lyrics_ovh(clean_name, artist)
    if lyrics:
        return lyrics

    return None


def _search_lrclib(song_name, clean_name, artist):
    """lrclib.net 搜索"""
    # 同时用繁体和简体搜索
    simplified_name = to_simplified(clean_name)
    simplified_artist = to_simplified(artist)
    
    search_queries = [
        f"{clean_name} {artist}",              # 繁体
        f"{simplified_name} {simplified_artist}",  # 简体
        f"{simplified_name} {artist}",          # 简体名+原歌手
        f"{song_name} {simplified_artist}",     # 原名+简体歌手
        simplified_name,                         # 只用简体名
        clean_name,                              # 只用繁体名
    ]
    
    for query in search_queries:
        url = f"{LRCLIB_SEARCH_URL}?q={urllib.parse.quote(query)}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data:
                    continue
                # 优先选择有同步歌词且歌手匹配的结果
                for result in data:
                    if result.get('syncedLyrics'):
                        if artist.lower() in result.get('artistName', '').lower() or \
                           simplified_artist.lower() in result.get('artistName', '').lower():
                            return result
                # 选择有普通歌词且歌手匹配的
                for result in data:
                    if result.get('plainLyrics'):
                        if artist.lower() in result.get('artistName', '').lower() or \
                           simplified_artist.lower() in result.get('artistName', '').lower():
                            return result
                return data[0]
        except (urllib.error.URLError, Exception):
            continue
    return None


def _get_lrclib_direct(artist, album, title):
    """lrclib.net 直接获取"""
    url = f"{LRCLIB_GET_URL}/{urllib.parse.quote(artist)}/{urllib.parse.quote(album)}/{urllib.parse.quote(title)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('syncedLyrics') or data.get('plainLyrics'):
                return data
    except Exception:
        pass
    return None


def _search_netease(song_name, artist, album_name=None):
    """网易云音乐 API 搜索（使用简体中文）"""
    s_name = to_simplified(song_name)
    s_artist = to_simplified(artist)
    query = s_name + " " + s_artist
    url = NETEASE_API + urllib.parse.quote(query)

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://music.163.com/',
        })
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))

        songs = data.get('result', {}).get('songs', [])
        if not songs:
            return None

        # 遍历搜索结果，放宽匹配条件
        for s in songs[:5]:
            s_artist_list = [a['name'] for a in s.get('artists', [])]
            s_title = s.get('name', '')

            # 检查歌手是否包含目标歌手（或简体版本）
            s_artist_str = ', '.join(s_artist_list)
            artist_match = (
                artist in s_artist_str or
                s_artist_str in artist or
                to_simplified(artist) in to_simplified(s_artist_str) or
                any(to_simplified(a) in to_simplified(artist) or to_simplified(artist) in to_simplified(a)
                    for a in s_artist_list)
            )

            # 检查歌曲名是否相似（去掉后缀后比较）
            title_clean = re.sub(r'\s*[-（(].*$', '', s_title).strip()
            name_clean = re.sub(r'\s*[-（(].*$', '', s_name).strip()
            stitle_clean = re.sub(r'\s*[-（(].*$', '', to_simplified(s_title)).strip()
            sname_clean = to_simplified(name_clean)

            # 歌名匹配：任一方向包含关系，或简化后包含
            title_match = (
                sname_clean in stitle_clean or
                stitle_clean in sname_clean or
                len(set(sname_clean) & set(stitle_clean)) > min(len(stitle_clean), len(sname_clean)) * 0.5
            )

            if artist_match or title_match:
                lrc_id = s.get('id')
                if lrc_id:
                    lrc_text = _fetch_netease_lrc(lrc_id)
                    if lrc_text:
                        return lrc_text

        # 最后尝试第一个结果
        first_song = songs[0]
        if first_song.get('id'):
            return _fetch_netease_lrc(first_song['id'])

    except Exception:
        pass
    return None


def _fetch_netease_lrc(song_id):
    """获取网易云歌词"""
    url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=-1&tv=-1"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://music.163.com/',
        })
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        lrc = data.get('lrc', {})
        if lrc and lrc.get('lyric'):
            return lrc['lyric']
    except Exception:
        pass
    return None


def _search_lyrics_ovh(song_name, artist):
    """lyrics.ovh 搜索"""
    s_name = to_simplified(song_name)
    s_artist = to_simplified(artist)
    
    # 尝试多种组合
    queries = [
        (s_artist, s_name),
        (s_artist, song_name),
        (artist, s_name),
    ]
    
    for q_artist, q_title in queries:
        url = f"{LYRICS_OVH_API}{urllib.parse.quote(q_artist)}/{urllib.parse.quote(q_title)}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                text = response.read().decode('utf-8')
                if text and text != 'Not Found' and len(text) > 20:
                    lines = text.strip().split('\n')
                    lrc_lines = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            lrc_lines.append(line)
                    if lrc_lines:
                        return '\n'.join(lrc_lines)
        except Exception:
            pass
    return None


def _search_qq_music(song_name, artist, album_name=None):
    """QQ音乐搜索歌词（使用 c.y.qq.com API）"""
    s_name = to_simplified(song_name)
    s_artist = to_simplified(artist)
    
    # QQ音乐搜索接口返回 JSONP 格式，需要特殊处理
    query = s_name + " " + s_artist
    url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={urllib.parse.quote(query)}&format=json&n=3&t=0"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://y.qq.com/',
        })
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        songs = data.get('data', {}).get('song', {}).get('list', [])
        if not songs:
            # 尝试只搜歌名
            url2 = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={urllib.parse.quote(s_name)}&format=json&n=5&t=0"
            req2 = urllib.request.Request(url2, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://y.qq.com/',
            })
            with urllib.request.urlopen(req2, timeout=8) as response2:
                data2 = json.loads(response2.read().decode('utf-8'))
            songs = data2.get('data', {}).get('song', {}).get('list', [])
        
        if not songs:
            return None
        
        for song in songs[:5]:
            mid = song.get('mid') or song.get('songmid')
            if not mid:
                continue
            
            # 获取歌词
            lyrics = _fetch_qq_lyrics(mid)
            if lyrics:
                return lyrics
        
        # 尝试第一首
        first_mid = songs[0].get('mid') or songs[0].get('songmid')
        if first_mid:
            return _fetch_qq_lyrics(first_mid)

    except Exception:
        pass
    return None


def _fetch_qq_lyrics(song_mid):
    """获取QQ音乐歌词"""
    url = f"https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_yqq.fcg?songmid={song_mid}&format=json"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://y.qq.com/',
        })
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        lyric_str = data.get('lyric', '')
        if lyric_str:
            import base64
            decoded = base64.b64decode(lyric_str).decode('utf-8')
            if decoded and len(decoded) > 20:
                return decoded
    except Exception:
        pass
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


def download_lyrics(albums, dry_run=False):
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

            # 搜索歌词（依次尝试 lrclib, 网易云, lyrics.ovh）
            lyrics = search_lyrics(song_name, artist, album_name)

            if lyrics:
                # 保存歌词文件 (.lrc + .js)
                save_lyrics(lrc_file, lyrics)
                source = ""
                if "163" in str(lyrics):
                    source = " [网易云]"
                elif len(lyrics) > 0 and not lyrics.startswith('['):
                    source = " [lyrics.ovh]"
                else:
                    source = " [lrclib]"
                print(f"✓{source}")
                success += 1
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