import re

# 配置：基准文件 + {输出文件: 代理前缀} 的 KV 映射（可直接修改）
BASE_FILE = "base.m3u8"
PROXIES = {
    "me.m3u8": "http://192.168.10.30:5140/",   # 南边
    "parents.m3u8": "http://192.168.1.101:5140/",  # 北边
}

def convert(text, proxy):
    """将文本中所有 rtp:// 和 rtsp:// 地址加上代理前缀，并去掉协议后的 //。"""
    # rtp://239.3.1.x:port -> proxy + rtp/239.3.1.x:port
    # rtsp://host/...       -> proxy + rtsp/host/...
    text = re.sub(r"rtp://(\d+\.\d+\.\d+\.\d+:\d+)",
                  lambda m: proxy + "rtp/" + m.group(1), text)
    text = re.sub(r"rtsp://([^\s\"']+)",
                  lambda m: proxy + "rtsp/" + m.group(1), text)
    return text

with open(BASE_FILE, encoding="utf-8") as f:
    content = f.read()

for out_file, proxy in PROXIES.items():
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(convert(content, proxy))
    print(f"已生成 {out_file}（{proxy}）")
