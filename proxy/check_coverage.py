#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# 读取 nav.xml 中的域名
tree = ET.parse('../nav.xml')
root = tree.getroot()
domains = set()
for url_elem in root.iter('网址'):
    addr_elem = url_elem.find('地址')
    if addr_elem is not None and addr_elem.text:
        url = addr_elem.text.strip()
        if url.startswith('http'):
            parsed = urlparse(url)
            domain = parsed.netloc.lower().split(':')[0]
            if domain.startswith('www.'):
                domain = domain[4:]
            if domain:
                domains.add(domain)

# 读取现有规则
existing = set()
with open('rules.conf', 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('- DOMAIN-SUFFIX,'):
            parts = line.split(',')
            if len(parts) >= 2:
                existing.add(parts[1].strip().lower())
        elif line.startswith('- DOMAIN,'):
            parts = line.split(',')
            if len(parts) >= 2:
                existing.add(parts[1].strip().lower())

# 找出未覆盖的站点
not_covered = domains - existing

print(f'nav.xml 中的域名总数: {len(domains)}')
print(f'rules.conf 中已有的规则: {len(existing)}')
print(f'未覆盖的域名: {len(not_covered)}')
print()
print('未覆盖的域名列表:')
for d in sorted(not_covered):
    print(f'  - {d}')
