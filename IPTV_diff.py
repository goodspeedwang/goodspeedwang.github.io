# 三个文件路径，以后可直接修改
FILE_A = "iptv.bj.m3u8"   # 基准文件
FILE_B = "temp.m3u"       # 对比文件
OUT_HTML = "temp.html"    # 输出文件
BASE_URL = "http://192.168.10.30:5140/rtp/"  # rtp 地址前缀

import re

def build_map(path):
    """Build dict addr -> channel name (from the EXTINF line above)."""
    result = {}
    name = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#EXTINF"):
                m = re.search(r",(.+)$", line)
                name = m.group(1).strip() if m else "?"
            elif "rtp/" in line:
                m = re.search(r"rtp/(\d+\.\d+\.\d+\.\d+:\d+)", line)
                if m and name is not None:
                    result.setdefault(m.group(1), name)
    return result

def sort_key(addr):
    return [int(p) for p in addr.replace(":", ".").split(".")]

a = build_map(FILE_A)
b = build_map(FILE_B)

a_set = set(a)
b_set = set(b)

only_a = sorted(a_set - b_set, key=sort_key)
only_b = sorted(b_set - a_set, key=sort_key)

html = []
html.append("<!DOCTYPE html>")
html.append("<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
html.append("<title>IPTV 差异对比</title>")
html.append("<style>")
html.append("body{font-family:-apple-system,Segoe UI,Arial,sans-serif;margin:24px;background:#fafafa;color:#222}")
html.append("h1{font-size:20px}")
html.append("p{color:#666}")
html.append(".wrap{display:flex;gap:16px;align-items:flex-start}")
html.append(".card{flex:1;background:#fff;border:1px solid #e3e3e3;border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.05)}")
html.append(".card h2{margin:0 0 12px;font-size:16px;display:flex;justify-content:space-between;align-items:center}")
html.append(".count{font-size:13px;color:#888;font-weight:normal}")
html.append("table{width:100%;border-collapse:collapse;font-size:14px}")
html.append("th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #f0f0f0}")
html.append("th{color:#666;font-weight:600}")
html.append(".addr{font-family:ui-monospace,Menlo,monospace;color:#c7254e}")
html.append(".addr a{color:#c7254e;text-decoration:none}")
html.append(".addr a:hover{text-decoration:underline}")
html.append("@media(max-width:720px){.wrap{flex-direction:column}}")
html.append("</style></head><body>")
html.append(f"<h1>IPTV 差异对比：{FILE_A} vs {FILE_B}</h1>")
html.append(f"<p>对比基于 rtp 地址（形如 <code>239.3.1.63:8116</code>），仅列出两边各自独有的条目。</p>")
html.append("<div class=\"wrap\">")

html.append("<div class=\"card\">")
html.append(f"<h2>仅在 {FILE_A} 中 <span class=\"count\">{len(only_a)} 条</span></h2>")
html.append("<table><tr><th>#</th><th>频道</th><th>rtp 地址</th></tr>")
for i, addr in enumerate(only_a, 1):
    url = BASE_URL + addr
    html.append(f"<tr><td>{i}</td><td>{a.get(addr,'?')}</td><td class=\"addr\"><a href=\"{url}\">{url}</a></td></tr>")
html.append("</table></div>")

html.append("<div class=\"card\">")
html.append(f"<h2>仅在 {FILE_B} 中 <span class=\"count\">{len(only_b)} 条</span></h2>")
html.append("<table><tr><th>#</th><th>频道</th><th>rtp 地址</th></tr>")
for i, addr in enumerate(only_b, 1):
    url = BASE_URL + addr
    html.append(f"<tr><td>{i}</td><td>{b.get(addr,'?')}</td><td class=\"addr\"><a href=\"{url}\">{url}</a></td></tr>")
html.append("</table></div>")

html.append("</div></body></html>")

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"only_{FILE_A}: {len(only_a)}  only_{FILE_B}: {len(only_b)}")
