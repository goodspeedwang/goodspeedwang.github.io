#!/usr/bin/env python3
"""
用法:
    python3 server.py [端口] [目录]

默认端口: 8080
默认目录: 当前目录

接口:
    GET /            -> 目录列表 HTML（含子文件夹 + 图片/视频）
    GET /subdir/     -> 子目录列表
    GET /subdir/file -> 返回文件，支持 ETag / Last-Modified 304
"""

import os
import sys
import hashlib
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.utils import formatdate, parsedate
from datetime import datetime, timezone
from urllib.parse import unquote, quote

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.tiff',
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
}

PORT = int(sys.argv[1] if len(sys.argv) > 1 else 8080)
SERVE_DIR = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else '.')


def list_dir(dirpath):
    dirs, files = [], []
    for name in sorted(os.listdir(dirpath)):
        if name.startswith('.'):
            continue
        full = os.path.join(dirpath, name)
        if os.path.isdir(full):
            dirs.append(name)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in MEDIA_EXTENSIONS:
                files.append(name)
    return dirs, files


def get_etag(stat):
    raw = f"{stat.st_mtime}-{stat.st_size}"
    return hashlib.md5(raw.encode()).hexdigest()


def build_directory_html(dirpath, url_path):
    dirs, files = list_dir(dirpath)
    display_name = url_path.rstrip("/").split("/")[-1] if url_path else "/"
    title = f"Directory listing for {display_name}"
    rows = []
    if url_path:
        rows.append('<li><a href="../">../</a></li>')
    for name in dirs:
        rows.append(f'<li><a href="{quote(name)}/">{name}/</a></li>')
    for name in files:
        rows.append(f'<li><a href="{quote(name)}">{name}</a></li>')
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
        url_path = unquote(self.path).strip('/')
        filepath = os.path.realpath(os.path.join(SERVE_DIR, url_path))

        # 防止路径穿越
        if filepath != SERVE_DIR and not filepath.startswith(SERVE_DIR + os.sep):
            self.send_error(403)
            return

        if os.path.isdir(filepath):
            self.handle_dir(filepath, url_path)
        elif os.path.isfile(filepath):
            self.handle_file(filepath)
        else:
            self.send_error(404)

    def handle_dir(self, dirpath, url_path):
        stat = os.stat(dirpath)
        etag = get_etag(stat)
        last_modified = formatdate(stat.st_mtime, usegmt=True)

        if_none_match = self.headers.get('If-None-Match')
        if_modified_since = self.headers.get('If-Modified-Since')

        if if_none_match and if_none_match == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_cors()
            self.end_headers()
            return

        if if_modified_since and not if_none_match:
            try:
                since = parsedate(if_modified_since)
                since_ts = datetime(*since[:6], tzinfo=timezone.utc).timestamp()
                if stat.st_mtime <= since_ts:
                    self.send_response(304)
                    self.send_header('Last-Modified', last_modified)
                    self.send_cors()
                    self.end_headers()
                    return
            except Exception:
                pass

        body = build_directory_html(dirpath, url_path)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Last-Modified', last_modified)
        self.send_header('ETag', etag)
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def handle_file(self, filepath):
        # 只允许访问媒体文件和 HTML
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in MEDIA_EXTENSIONS and ext != '.html':
            self.send_error(403)
            return

        stat = os.stat(filepath)
        etag = get_etag(stat)
        last_modified = formatdate(stat.st_mtime, usegmt=True)
        mime = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

        # 304 检查：ETag 优先，其次 Last-Modified
        if_none_match = self.headers.get('If-None-Match')
        if_modified_since = self.headers.get('If-Modified-Since')

        if if_none_match and if_none_match == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_cors()
            self.end_headers()
            return

        if if_modified_since and not if_none_match:
            try:
                since = parsedate(if_modified_since)
                since_ts = datetime(*since[:6], tzinfo=timezone.utc).timestamp()
                if stat.st_mtime <= since_ts:
                    self.send_response(304)
                    self.send_header('Last-Modified', last_modified)
                    self.send_cors()
                    self.end_headers()
                    return
            except Exception:
                pass

        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', stat.st_size)
        self.send_header('Last-Modified', last_modified)
        self.send_header('ETag', etag)
        # 媒体文件缓存一年，HTML 不缓存
        if ext in MEDIA_EXTENSIONS:
            self.send_header('Cache-Control', 'max-age=31536000, immutable')
        else:
            self.send_header('Cache-Control', 'no-cache')
        self.send_cors()
        self.end_headers()

        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                self.wfile.write(chunk)


if __name__ == '__main__':
    print(f"服务目录: {SERVE_DIR}")
    print(f"监听端口: {PORT}")
    print(f"访问地址: http://localhost:{PORT}/")
    print("Ctrl+C 退出\n")
    HTTPServer(('', PORT), Handler).serve_forever()
