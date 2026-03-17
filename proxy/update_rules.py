#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
脚本名称: update_rules.py
作用: 扫描 nav.xml 中的站点，自动识别可直连的国外站点并添加到 rules.conf

工作流程:
1. 从 nav.xml 提取所有域名
2. 过滤掉：
   - 已存在于 rules.conf 的域名
   - 需要代理的站点（Google/Twitter/AI等）
   - 中国域名（.cn/.com.cn等，通过 GEOIP,CN 自动直连）
   - DNS解析到国内IP的站点
3. 将符合条件的国外可直连站点添加到 rules.conf

用法:
  python3 update_rules.py --dry-run    # 预览模式，查看会添加哪些站点
  python3 update_rules.py              # 执行添加

注意事项:
  - 需要在 proxy/ 目录下运行
  - 依赖 dig 命令（系统自带）
  - DIRECT_SITES 白名单需要手动维护，添加已知可直连的国外站点
================================================================================
"""

import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import subprocess
import sys

# 国外站点但可直连的白名单
DIRECT_SITES = {
    # 新闻媒体
    'bloomberg.com', 'scmp.com', 'chinadigitaltimes.net', 'globalnews.ca',
    'englishnewsinlevels.com',
    # 词典/学习
    'dictionary.com', 'oxfordlearnersdictionaries.com', 'thefreedictionary.com',
    'voicetube.com', 'quodb.com', 'tjxz.cc',
    # 工具/服务
    'aqicn.org', 'ip125.com', 'shudu.one', 'kylc.com',
    'tutorialspoint.com', 'overapi.com', 'regexlib.com',
    'readthedocs.org', 'readthedocs.io',
    # 金融/投资
    'simplywall.st', 'worldgovernmentbonds.com', 'mysmartadvisor.com',
    # 社区/内容
    'v2ex.com', 'sspai.com',
    'abskoop.com', 'neikuw.com', 'xiaolipan.com', 'fast8.com', '80sgod.com',
    # 工具
    'picsart.com', 'krea.ai', 'raphael.app',
    # 其他
    'cnbeta.com.tw', 'cambridge.org',
}

# 需要代理的站点
PROXY_SITES = {
    'chatgpt.com', 'docs.google.com', 'gemini.google.com', 'mail.google.com',
    'news.google.com', 'notion.so', 'perplexity.ai', 'poe.com',
    'twitter.com', 'web.archive.org', 'web.skype.com', 'youtube.com',
    'gitpod.io', 'v4.www-y2mate.com',
}

# 跳过中国域名后缀
CN_SUFFIXES = ('.cn', '.com.cn', '.net.cn', '.org.cn', '.gov.cn', '.edu.cn')


def get_domains_from_nav(xml_path='../nav.xml'):
    """从 nav.xml 提取域名"""
    tree = ET.parse(xml_path)
    domains = set()
    for url in tree.getroot().iter('网址'):
        addr = url.find('地址')
        if addr is not None and addr.text:
            parsed = urlparse(addr.text.strip())
            if parsed.netloc:
                domain = parsed.netloc.lower().split(':')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]
                if domain and not domain.startswith('192.168.') and not domain.startswith('127.'):
                    domains.add(domain)
    return domains


def load_existing_rules(rules_path='./rules.conf'):
    """加载现有规则中的域名"""
    existing = set()
    try:
        with open(rules_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('- DOMAIN-SUFFIX,') or line.startswith('- DOMAIN,'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        existing.add(parts[1].strip().lower())
    except FileNotFoundError:
        pass
    return existing


def get_main_domain(domain):
    """获取主域名"""
    parts = domain.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else domain


def check_dns(domain):
    """检查域名DNS解析，返回 (ip, is_china)"""
    try:
        result = subprocess.run(
            ['dig', '+short', domain],
            capture_output=True, text=True, timeout=5
        )
        ips = [line.strip() for line in result.stdout.split('\n') 
               if line.strip() and not line.strip().startswith(';')]
        if not ips:
            return None, False
        
        ip = ips[0]
        # 简单判断国内IP段
        china_prefixes = (
            '1.', '27.', '36.', '39.', '42.', '43.', '49.', '58.', '59.', '60.', '61.',
            '101.', '103.', '106.', '110.', '111.', '112.', '113.', '114.', '115.',
            '116.', '117.', '118.', '119.', '120.', '121.', '122.', '123.', '124.',
            '125.', '126.', '139.', '140.', '144.', '150.', '153.', '163.', '171.',
            '175.', '180.', '182.', '183.', '202.', '203.', '210.', '211.', '218.',
            '219.', '220.', '221.', '222.', '223.'
        )
        is_china = any(ip.startswith(p) for p in china_prefixes)
        return ip, is_china
    except:
        return None, False


def main():
    dry_run = '--dry-run' in sys.argv
    
    # 获取所有域名
    nav_domains = get_domains_from_nav()
    existing = load_existing_rules()
    
    print(f"nav.xml 域名总数: {len(nav_domains)}")
    print(f"rules.conf 已有规则: {len(existing)}")
    
    # 分类
    to_add = []
    skipped = {'proxy': [], 'china_domain': [], 'china_ip': [], 'existing': []}
    
    for domain in sorted(nav_domains):
        if domain in existing or get_main_domain(domain) in existing:
            skipped['existing'].append(domain)
            continue
        if domain in PROXY_SITES or get_main_domain(domain) in PROXY_SITES:
            skipped['proxy'].append(domain)
            continue
        if any(domain.endswith(s) for s in CN_SUFFIXES):
            skipped['china_domain'].append(domain)
            continue
        
        # 检查是否在白名单
        main = get_main_domain(domain)
        if domain not in DIRECT_SITES and main not in DIRECT_SITES:
            continue
        
        # DNS检查
        ip, is_china = check_dns(domain)
        if is_china:
            skipped['china_ip'].append(f"{domain} ({ip})")
            continue
        
        to_add.append(domain)
    
    # 输出结果
    print(f"\n可添加的站点: {len(to_add)}")
    for d in sorted(to_add):
        print(f"  + {d}")
    
    if skipped['existing']:
        print(f"\n已存在: {len(skipped['existing'])}个")
    if skipped['proxy']:
        print(f"\n需要代理: {len(skipped['proxy'])}个")
        for d in skipped['proxy'][:5]:
            print(f"  - {d}")
    if skipped['china_domain']:
        print(f"\n中国域名(.cn等): {len(skipped['china_domain'])}个")
    if skipped['china_ip']:
        print(f"\n国内IP解析: {len(skipped['china_ip'])}个")
        for d in skipped['china_ip'][:5]:
            print(f"  - {d}")
    
    if not to_add:
        print("\n没有需要添加的新站点")
        return
    
    if dry_run:
        print("\n[预览模式] 未写入文件")
        return
    
    # 写入文件
    with open('./rules.conf', 'a') as f:
        f.write('\n# 自动添加的直连站点\n')
        for domain in sorted(to_add):
            main = get_main_domain(domain)
            rule_type = 'DOMAIN-SUFFIX' if domain == main else 'DOMAIN'
            f.write(f'- {rule_type},{domain},DIRECT\n')
    
    print(f"\n已添加 {len(to_add)} 条规则到 rules.conf")


if __name__ == '__main__':
    main()
