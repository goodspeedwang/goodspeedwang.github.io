#!/usr/bin/env python3
"""
用法:
    python3 server.py [端口] [相册目录]

默认端口: 8080
相册目录: 用于定位媒体文件（图片/视频）

接口:
    GET /photo.html          -> 前端页面（从 APP_DIR 读取）
    GET /                    -> 根目录列表（从 JSON 数据）
    GET /subdir/             -> 子目录列表（从 JSON 数据）
    GET /subdir/file         -> 返回媒体文件（从磁盘读取）
"""

import os
import sys
import json
import hashlib
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.utils import formatdate
from urllib.parse import unquote, quote

APP_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.tiff',
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
}

PORT = int(sys.argv[1] if len(sys.argv) > 1 else 8080)
SERVE_DIR = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else '.')


# ========== 加载 JSON 数据 ==========

def find_json_file():
    """在 APP_DIR 下查找 .json 文件（优先 girl.json）"""
    # 优先查找 girl.json
    preferred = os.path.join(APP_DIR, 'girl.json')
    if os.path.isfile(preferred):
        return preferred
    # 回退到任意 .json
    for f in os.listdir(APP_DIR):
        if f.endswith('.json'):
            return os.path.join(APP_DIR, f)
    return None


def load_gallery_data(json_path):
    """加载并构建路径查找树"""
    if not json_path:
        print("错误: 未找到 .json 数据文件")
        sys.exit(1)

    print(f"加载数据: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 构建路径 -> 节点 的查找表
    # key: "" (根) 或 "58" 或 "58/yuyu"
    tree = {'': data}
    _build_index(data.get('folders', []), '', tree)
    return data, tree, data.get('sourceDir', '')


def _build_index(folders, parent_path, index):
    """递归构建路径索引"""
    for folder in folders:
        rel_path = f"{parent_path}/{folder['url']}" if parent_path else folder['url']
        index[rel_path] = folder
        _build_index(folder.get('folders', []), rel_path, index)


# ========== 目录 HTML 生成（兼容前端 extractItems）==========

def build_dir_html(node, url_path):
    """用 JSON 数据生成与 extractItems 兼容的目录 HTML"""
    display_name = url_path.rstrip("/").split("/")[-1] if url_path else "/"
    title = f"Directory listing for {display_name}"
    rows = []

    if url_path:
        rows.append('<li><a href="../">../</a></li>')

    # 子文件夹（href 以 / 结尾）
    for f in node.get('folders', []):
        rows.append(f'<li><a href="{quote(f["url"])}/">{f["name"]}/</a></li>')

    # 图片/视频文件（href 不以 / 结尾）
    for img in node.get('images', []):
        rows.append(f'<li><a href="{quote(img["url"])}">{img["name"]}</a></li>')

    body = f"""<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
<h1>{title}</h1>
<hr>
<ul>
{''.join(rows)}
</ul>
<hr>
</body>
</html>
"""
    return body.encode('utf-8')


# ========== ETag 工具 ==========

def get_etag_for_bytes(content):
    """对 bytes 内容生成 etag"""
    return hashlib.md5(content).hexdigest()


def get_etag_for_file(stat):
    """对文件 stat 生成 etag"""
    raw = f"{stat.st_mtime}-{stat.st_size}"
    return hashlib.md5(raw.encode()).hexdigest()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        raw_path = self.path.split('?', 1)[0].split('#', 1)[0]
        # 保留尾部斜杠用于区分目录和文件
        has_trailing_slash = raw_path.endswith('/')
        url_path = unquote(raw_path).strip('/')

        # 应用文件：从 APP_DIR 读取
        if url_path == 'photo.html':
            app_file = os.path.join(APP_DIR, 'photo.html')
            if os.path.isfile(app_file):
                self.handle_file(app_file)
                return

        # 目录请求（原始路径以 / 结尾，或路径在 JSON 索引中存在）
        if has_trailing_slash or url_path in gallery_tree or url_path == '':
            self.handle_json_dir(url_path)
            return

        # 文件请求：从磁盘读取
        filepath = os.path.realpath(os.path.join(SERVE_DIR, url_path))
        if not filepath.startswith(SERVE_DIR + os.sep):
            self.send_error(403)
            return

        if os.path.isfile(filepath):
            self.handle_file(filepath)
        else:
            self.send_error(404)

    def handle_json_dir(self, rel_path):
        """根据 JSON 数据返回目录 HTML"""
        if rel_path not in gallery_tree:
            self.send_error(404)
            return

        body = build_dir_html(gallery_tree[rel_path], rel_path)
        etag = get_etag_for_bytes(body)

        # 304 检查
        if_none_match = self.headers.get('If-None-Match')
        if if_none_match == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_cors()
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('ETag', etag)
        self.send_header('Cache-Control', 'no-cache')
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def handle_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in MEDIA_EXTENSIONS and ext != '.html':
            self.send_error(403)
            return

        stat = os.stat(filepath)
        etag = get_etag_for_file(stat)
        last_modified = formatdate(stat.st_mtime, usegmt=True)
        mime = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

        # 304 检查
        if_none_match = self.headers.get('If-None-Match')
        if if_none_match == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_cors()
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', stat.st_size)
        self.send_header('Last-Modified', last_modified)
        self.send_header('ETag', etag)

        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.tiff',
                    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'):
            self.send_header('Cache-Control', 'max-age=31536000, immutable')
        else:
            self.send_header('Cache-Control', 'no-cache')

        self.send_cors()
        self.end_headers()

        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except BrokenPipeError:
            pass


if __name__ == '__main__':
    json_file = find_json_file()
    gallery_data, gallery_tree, source_dir = load_gallery_data(json_file)

    stats = gallery_data.get('_stats', {})
    print(f"数据源: {source_dir}")
    print(f"文件夹: {stats.get('totalFolders', '?')}, 媒体文件: {stats.get('totalMedia', '?')}")
    print(f"媒体目录: {SERVE_DIR}")
    print(f"监听端口: {PORT}")
    print(f"访问地址: http://localhost:{PORT}/photo.html")
    print("Ctrl+C 退出\n")

    HTTPServer(('', PORT), Handler).serve_forever()
