#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 nav.xml 中可直连的国外站点添加到 rules.conf
"""

import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# 国外站点但可直连的白名单（手动维护）
DIRECT_SITES = {
    # 新闻媒体
    'bloomberg.com', 'scmp.com', 'chinadigitaltimes.net', 'globalnews.ca',
    'englishnewsinlevels.com', 'chinadaily.com.cn',
    # 词典/学习
    'dictionary.com', 'oxfordlearnersdictionaries.com', 'thefreedictionary.com',
    'voicetube.com', 'quodb.com', 'tjxz.cc',
    # 工具/服务
    'aqicn.org', 'shudu.one', 'kylc.com', 'ip125.com',
    'tutorialspoint.com', 'overapi.com', 'regexlib.com',
    'readthedocs.org', 'readthedocs.io',
    # 金融/投资
    'simplywall.st', 'worldgovernmentbonds.com', 'mysmartadvisor.com',
    # 社区/内容
    'v2ex.com', 'sspai.com', 'dida365.com',
    'abskoop.com', 'neikuw.com', 'jiumodiary.com', 'xiaolipan.com',
    'fast8.com', '80sgod.com',
    # 工具
    'picsart.com', 'krea.ai', 'raphael.app',
    # 其他
    'cnbeta.com.tw', 'zol.com.cn', 'pchome.net', 'pcpop.com',
}

# 需要代理的站点（不添加）
PROXY_SITES = {
    'chatgpt.com', 'docs.google.com', 'gemini.google.com', 'mail.google.com',
    'news.google.com', 'notion.so', 'perplexity.ai', 'poe.com',
    'twitter.com', 'web.archive.org', 'web.skype.com', 'youtube.com',
    'gitpod.io', 'v4.www-y2mate.com',
}

# 本地/私有地址（不添加）
PRIVATE_SITES = {
    '192.168.100.1', '127.0.0.1', 'localhost',
}

# 中国域名后缀（会通过 GEOIP,CN 自动直连）
CN_SUFFIXES = ('.cn', '.com.cn', '.net.cn', '.org.cn', '.gov.cn', '.edu.cn', '.mil.cn')


def extract_domains_from_nav(xml_path):
    """从 nav.xml 提取所有域名"""
    tree = ET.parse(xml_path)
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
    
    return domains


def load_existing_rules(rules_path):
    """加载现有的 rules.conf 中的域名"""
    existing = set()
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
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
    except FileNotFoundError:
        pass
    return existing


def get_domain_suffix(domain):
    """获取主域名"""
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain


def main():
    import argparse
    parser = argparse.ArgumentParser(description='添加直连站点到 rules.conf')
    parser.add_argument('--nav', default='../nav.xml', help='nav.xml 路径')
    parser.add_argument('--rules', default='./rules.conf', help='rules.conf 路径')
    parser.add_argument('--dry-run', action='store_true', help='预览不写入')
    args = parser.parse_args()
    
    # 提取 nav.xml 中的域名
    nav_domains = extract_domains_from_nav(args.nav)
    
    # 加载已有规则
    existing_rules = load_existing_rules(args.rules)
    
    # 找出需要添加的站点
    to_add = []
    skipped_cn = []
    for domain in nav_domains:
        if domain in existing_rules:
            continue
        if domain in PRIVATE_SITES:
            continue
        if domain in PROXY_SITES:
            continue
        
        # 跳过中国域名（会通过 GEOIP,CN 自动直连）
        if any(domain.endswith(suffix) for suffix in CN_SUFFIXES):
            skipped_cn.append(domain)
            continue
        
        # 检查是否在 DIRECT_SITES 中（包括子域名匹配）
        domain_suffix = get_domain_suffix(domain)
        if domain in DIRECT_SITES or domain_suffix in DIRECT_SITES:
            to_add.append(domain)
    
    print("="*60)
    print(f"找到 {len(to_add)} 个可直连站点需要添加:")
    print("="*60)
    for domain in sorted(to_add):
        suffix = get_domain_suffix(domain)
        if domain == suffix:
            print(f"  - DOMAIN-SUFFIX,{domain},DIRECT")
        else:
            print(f"  - DOMAIN,{domain},DIRECT")
    
    if skipped_cn:
        print(f"\n跳过 {len(skipped_cn)} 个中国域名（GEOIP,CN自动直连）:")
        for domain in sorted(skipped_cn)[:10]:  # 只显示前10个
            print(f"  - {domain}")
        if len(skipped_cn) > 10:
            print(f"  ... 还有 {len(skipped_cn)-10} 个")
    
    if not to_add:
        print("没有需要添加的新站点")
        return
    
    if args.dry_run:
        print("\n[预览模式] 未实际写入文件")
        return
    
    # 写入 rules.conf
    print(f"\n写入到 {args.rules}...")
    with open(args.rules, 'a', encoding='utf-8') as f:
        f.write('\n# 从 nav.xml 自动添加的直连站点\n')
        for domain in sorted(to_add):
            suffix = get_domain_suffix(domain)
            if domain == suffix:
                f.write(f'- DOMAIN-SUFFIX,{domain},DIRECT\n')
            else:
                f.write(f'- DOMAIN,{domain},DIRECT\n')
    
    print(f"已添加 {len(to_add)} 条规则")


if __name__ == '__main__':
    main()
