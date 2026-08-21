import re
import urllib.request

# 配置（可直接修改）
BASE_FILE = "base.m3u8"                                   # 本地基准频道列表
REMOTE_URL = "https://raw.githubusercontent.com/qwerttvv/Beijing-IPTV/refs/heads/master/IPTV-Unicom.m3u"  # 远程节目单
OUT_HTML = "temp.html"                                    # 输出文件
BASE_URL = "http://192.168.10.30:5140/rtp/"               # rtp 地址前缀（用于生成可点击链接）

def build_map(text):
    """Build dict addr -> channel name。

    规则：
    - 仅以 #EXTINF 开头的行（真正的指令，非注释）作为频道名。
    - 仅非 # 开头的行（排除被 # 注释掉的行）作为 rtp 地址。
    - 支持 rtp/ 和 rtp:// 两种格式。
    """
    result = {}
    name = None
    for line in text.splitlines():
        line = line.rstrip("\n")
        if line.startswith("#EXTINF"):
            m = re.search(r",(.+)$", line)
            name = m.group(1).strip() if m else "?"
        elif not line.startswith("#"):
            m = re.search(r"rtp[://]+(\d+\.\d+\.\d+\.\d+:\d+)", line)
            if m and name is not None:
                result.setdefault(m.group(1), name)
    return result

def sort_key(addr):
    return [int(p) for p in addr.replace(":", ".").split(".")]

def fetch(url):
    """下载远程节目单，返回文本内容（不落盘）。"""
    print(f"正在下载：{url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8", errors="ignore")
    print(f"已下载（{len(data)} 字节）")
    return data

# 1. 下载远程节目单（仅在内存中）
remote_text = fetch(REMOTE_URL)

# 2. 解析本地与远程
with open(BASE_FILE, encoding="utf-8", errors="ignore") as f:
    local = build_map(f.read())
remote = build_map(remote_text)

local_set = set(local)
remote_set = set(remote)

# 3. 找出新出现的电台（在远程、不在本地）
new_addrs = sorted(remote_set - local_set, key=sort_key)
# 本地有、远程没有的（可能下线的，附在另一栏便于对照）
gone_addrs = sorted(local_set - remote_set, key=sort_key)

# 4. 生成 temp.html（与 IPTV_diff.py 风格一致）
html = []
html.append("<!DOCTYPE html>")
html.append("<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
html.append("<title>IPTV 新节目单对比</title>")
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
html.append(".addr{font-family:ui-monospace,Menlo,monospace;color:#c7254e;word-break:break-all}")
html.append(".copy{display:inline-block;margin-left:6px;cursor:pointer;user-select:none;color:#888;font-size:13px}")
html.append(".copy:hover{color:#3a9c3a}")
html.append(".copy.copied{color:#3a9c3a}")
html.append("@media(max-width:720px){.wrap{flex-direction:column}}")
html.append("</style></head><body>")
html.append("<script>")
html.append("function copyUrl(btn){")
html.append("  const t=btn.getAttribute('data-url');")
html.append("  navigator.clipboard.writeText(t).then(()=>{")
html.append("    const old=btn.textContent; btn.textContent='✓'; btn.classList.add('copied');")
html.append("    setTimeout(()=>{btn.textContent=old; btn.classList.remove('copied');}, 1200);")
html.append("  });")
html.append("}")
html.append("</script>")
html.append(f"<h1>IPTV 新节目单对比：远程 vs {BASE_FILE}</h1>")
html.append(f"<p>对比基于 rtp 地址（形如 <code>239.3.1.63:8116</code>），列出远程相对本地新出现 / 消失的电台。点击 📋 复制带代理的地址。</p>")
html.append("<div class=\"wrap\">")

html.append("<div class=\"card\">")
html.append(f"<h2>远程新出现的电台 <span class=\"count\">{len(new_addrs)} 条</span></h2>")
html.append("<table><tr><th>#</th><th>频道</th><th>rtp 地址</th></tr>")
for i, addr in enumerate(new_addrs, 1):
    url = BASE_URL + addr
    html.append(f"<tr><td>{i}</td><td>{remote.get(addr,'?')}</td><td class=\"addr\">{url}<span class=\"copy\" data-url=\"{url}\" onclick=\"copyUrl(this)\" title=\"复制\">📋</span></td></tr>")
html.append("</table></div>")

html.append("<div class=\"card\">")
html.append(f"<h2>本地有但远程消失的 <span class=\"count\">{len(gone_addrs)} 条</span></h2>")
html.append("<table><tr><th>#</th><th>频道</th><th>rtp 地址</th></tr>")
for i, addr in enumerate(gone_addrs, 1):
    url = BASE_URL + addr
    html.append(f"<tr><td>{i}</td><td>{local.get(addr,'?')}</td><td class=\"addr\">{url}<span class=\"copy\" data-url=\"{url}\" onclick=\"copyUrl(this)\" title=\"复制\">📋</span></td></tr>")
html.append("</table></div>")

html.append("</div></body></html>")

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"新出现: {len(new_addrs)} 条  消失: {len(gone_addrs)} 条 -> 已生成 {OUT_HTML}")
