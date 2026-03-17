#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 nav.xml 中的站点，测试哪些国外站点可以直连
"""

import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import subprocess
import time
import re

# 已知需要代理的域名（不需要测试）
PROXY_DOMAINS = {
    # Google 系列
    'google.com', 'googleapis.com', 'googleusercontent.com', 'gstatic.com',
    'youtube.com', 'youtu.be', 'ytimg.com', 'googlevideo.com',
    'gmail.com',
    # 社交媒体
    'twitter.com', 'x.com', 'twimg.com', 't.co',
    'facebook.com', 'fbcdn.net', 'instagram.com',
    # AI 服务
    'openai.com', 'chatgpt.com', 'claude.ai', 'anthropic.com',
    'gemini.google.com', 'poe.com', 'perplexity.ai',
    # 其他已知需要代理
    'notion.so', 'web.archive.org', 'gitpod.io', 'skype.com',
}

# 已知可以直连的域名（中国公司或有国内 CDN）
DIRECT_DOMAINS = {
    # 国内站点
    'zhihu.com', 'baidu.com', 'jd.com', 'taobao.com', 'tmall.com',
    'weibo.com', '163.com', 'qq.com', 'bilibili.com', 'douyin.com',
    'smzdm.com', 'gaode.com', 'xiaohongshu.com',
    'csdn.net', 'cnblogs.com', 'juejin.cn',
    'aliyundrive.com', 'weiyun.com', 'docs.qq.com',
    'xueqiu.com', 'jisilu.cn', 'eastmoney.com',
    'doubao.com', 'deepseek.com', 'wenxiaobai.com',
    'youdao.com', '126.com', '10010.com', '189.cn',
    'sina.com.cn', 'sinopecsales.com', 'kongfz.com',
    'dygod.net', 'bugutv.org', 'ixigua.com', 'yangshipin.cn',
    'tencent.com', 'coding.net', 'cloudstudio.net',
    'hiksemi.cn', 'k12media.cn', 'mafengwo.cn',
    'qyer.com', 'elvxing.net', 'daoduoduo.com',
    'cmbchina.com', 'spdbccc.com.cn', 'spdb.com.cn', '95559.com.cn',
    # 有国内 CDN 的国外站点
    'microsoft.com', 'bing.com', 'msn.com', 'asp.net',
    'apple.com', 'icloud.com',
    'amap.com', 'cambridge.org',
    # 新闻媒体（可直连）
    'zaobao.com', 'chinatimes.com', 'scmp.com', 'globalnews.ca',
    'chinadaily.com.cn', 'chinadigitaltimes.net', 'bloomberg.com',
    # 词典/学习类（可直连）
    'dictionary.com', 'thefreedictionary.com', 'oxfordlearnersdictionaries.com',
    'iciba.com', 'dict.cn', 'quodb.com', 'englishnewsinlevels.com',
    'voicetube.com', 'tjxz.cc',
    # 技术/开发类（可直连）
    'tutorialspoint.com', 'cnbeta.com.tw', 'zol.com.cn', 'pchome.net', 'pcpop.com',
    'readthedocs.org', 'readthedocs.io', 'overapi.com', 'regexlib.com',
    # 工具类（可直连）
    'aqicn.org', 'waqi.info', 'ip125.com', 'ipinfo.io', 'shudu.one',
    'picsart.com', 'krea.ai', 'kylc.com',
    # 金融/投资类（可直连）
    'worldgovernmentbonds.com', 'simplywall.st', 'mysmartadvisor.com',
    # 其他可直连
    'v2ex.com', 'sspai.com', 'dida365.com', 'xiezuocat.com',
    'abskoop.com', 'neikuw.com', 'jiumodiary.com', 'xiaolipan.com', 'fast8.com',
    'raphael.app', '80sgod.com',
}

# 不需要添加的域名（本地IP、下载工具等）
SKIP_DOMAINS = {
    '192.168.100.1',  # 本地IPTV
    '127.0.0.1', 'localhost',
}

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
                domain = parsed.netloc.lower()
                # 移除端口和 www 前缀
                domain = domain.split(':')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]
                if domain:
                    domains.add(domain)
    
    return domains

def get_domain_suffix(domain):
    """获取主域名（去掉子域名）"""
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain

def is_chinese_domain(domain):
    """判断是否是中国域名"""
    # 常见的中国域名后缀
    cn_suffixes = ['.cn', '.com.cn', '.net.cn', '.org.cn', '.gov.cn', '.edu.cn']
    for suffix in cn_suffixes:
        if domain.endswith(suffix):
            return True
    
    # 检查是否在已知直连列表中
    domain_suffix = get_domain_suffix(domain)
    for direct in DIRECT_DOMAINS:
        if domain == direct or domain.endswith('.' + direct) or direct.endswith('.' + domain_suffix):
            return True
    
    return False

def is_known_proxy_domain(domain):
    """判断是否是已知需要代理的域名"""
    domain_suffix = get_domain_suffix(domain)
    for proxy in PROXY_DOMAINS:
        if domain == proxy or domain.endswith('.' + proxy) or proxy == domain_suffix:
            return True
    return False

def test_direct_connection(domain, timeout=5):
    """测试域名是否可以直连"""
    try:
        # 使用 curl 测试，只获取头部，设置超时
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             '--connect-timeout', str(timeout), '-m', str(timeout + 2),
             '-H', 'User-Agent: Mozilla/5.0',
             f'https://{domain}'],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        
        http_code = result.stdout.strip()
        # 200-399 都是成功的响应
        if http_code.isdigit() and 200 <= int(http_code) < 400:
            return True, http_code
        
        # 尝试 HTTP
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             '--connect-timeout', str(timeout), '-m', str(timeout + 2),
             '-H', 'User-Agent: Mozilla/5.0',
             f'http://{domain}'],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        
        http_code = result.stdout.strip()
        if http_code.isdigit() and 200 <= int(http_code) < 400:
            return True, http_code
        
        return False, http_code
    except subprocess.TimeoutExpired:
        return False, 'TIMEOUT'
    except Exception as e:
        return False, str(e)

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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='扫描 nav.xml 中的站点')
    parser.add_argument('--nav', default='../nav.xml', help='nav.xml 路径')
    parser.add_argument('--rules', default='./rules.conf', help='rules.conf 路径')
    parser.add_argument('--test', action='store_true', help='测试站点连通性（较慢）')
    parser.add_argument('--add', action='store_true', help='自动添加可直连的国外站点到 rules.conf')
    args = parser.parse_args()
    
    print("="*60)
    print("扫描 nav.xml 中的站点")
    print("="*60)
    
    # 提取域名
    domains = extract_domains_from_nav(args.nav)
    print(f"\n共提取到 {len(domains)} 个域名")
    
    # 加载已有规则
    existing_rules = load_existing_rules(args.rules)
    print(f"rules.conf 中已有 {len(existing_rules)} 个域名规则")
    
    # 分类
    chinese_domains = set()
    proxy_domains = set()
    skip_domains = set()
    unknown_domains = set()
    
    for domain in sorted(domains):
        if domain in existing_rules or get_domain_suffix(domain) in existing_rules:
            continue  # 已在规则中
        
        if domain in SKIP_DOMAINS or any(domain.endswith('.' + skip) for skip in SKIP_DOMAINS):
            skip_domains.add(domain)
            continue
        
        if is_chinese_domain(domain):
            chinese_domains.add(domain)
        elif is_known_proxy_domain(domain):
            proxy_domains.add(domain)
        else:
            unknown_domains.add(domain)
    
    print(f"\n分类结果:")
    print(f"  - 中国站点（跳过）: {len(chinese_domains)}")
    print(f"  - 已知需要代理: {len(proxy_domains)}")
    print(f"  - 跳过（本地IP等）: {len(skip_domains)}")
    print(f"  - 需要测试的未知站点: {len(unknown_domains)}")
    
    if chinese_domains:
        print(f"\n中国站点:")
        for d in sorted(chinese_domains):
            print(f"  - {d}")
    
    if proxy_domains:
        print(f"\n已知需要代理的站点:")
        for d in sorted(proxy_domains):
            print(f"  - {d}")
    
    if skip_domains:
        print(f"\n跳过的站点（本地IP等）:")
        for d in sorted(skip_domains):
            print(f"  - {d}")
    
    if unknown_domains:
        print(f"\n未知站点（需要判断是否直连）:")
        
        # 使用 heuristics 判断
        direct_candidates = set()
        proxy_candidates = set()
        
        # 基于域名特征判断
        for domain in unknown_domains:
            suffix = get_domain_suffix(domain)
            
            # 国外媒体、新闻站点通常可以直连
            if any(kw in domain for kw in ['news', 'times', 'post', 'daily', 'journal', 'herald']):
                direct_candidates.add(domain)
            # .edu 结尾的教育站点
            elif domain.endswith('.edu'):
                direct_candidates.add(domain)
            # 知名可以直连的站点
            elif suffix in {'cambridge.org', 'oxfordlearnersdictionaries.com', 'voicetube.com',
                           'v2ex.com', 'scmp.com', 'zaobao.com', 'chinatimes.com',
                           'globalnews.ca', 'bloomberg.com', 'picsart.com', 'krea.ai'}:
                direct_candidates.add(domain)
            # AI 相关
            elif any(kw in domain for kw in ['ai', 'chat', 'gpt']):
                proxy_candidates.add(domain)
            else:
                # 需要测试
                proxy_candidates.add(domain)
        
        # 显示建议直连的站点
        if direct_candidates:
            print(f"\n建议直连的站点 ({len(direct_candidates)}):")
            for d in sorted(direct_candidates):
                print(f"  - {d}")
        
        # 显示建议代理的站点
        if proxy_candidates:
            print(f"\n建议代理的站点 ({len(proxy_candidates)}):")
            for d in sorted(proxy_candidates):
                print(f"  - {d}")
        
        # 测试连通性
        if args.test:
            print(f"\n测试连通性...")
            test_results = []
            
            for domain in sorted(unknown_domains):
                print(f"  测试 {domain}...", end=' ', flush=True)
                success, code = test_direct_connection(domain)
                test_results.append((domain, success, code))
                status = '✓ 可直连' if success else f'✗ {code}'
                print(status)
                time.sleep(0.5)  # 避免请求过快
            
            # 显示测试结果
            print(f"\n测试结果:")
            direct_sites = [r for r in test_results if r[1]]
            proxy_sites = [r for r in test_results if not r[1]]
            
            if direct_sites:
                print(f"\n可以直连的站点 ({len(direct_sites)}):")
                for d, _, code in direct_sites:
                    print(f"  - {d} (HTTP {code})")
            
            if proxy_sites:
                print(f"\n需要代理的站点 ({len(proxy_sites)}):")
                for d, _, code in proxy_sites:
                    print(f"  - {d} ({code})")
        
        # 添加到 rules.conf
        if args.add and direct_candidates:
            print(f"\n添加到 rules.conf...")
            with open(args.rules, 'a', encoding='utf-8') as f:
                f.write('\n# 自动添加的直连站点\n')
                for domain in sorted(direct_candidates):
                    # 判断用 DOMAIN 还是 DOMAIN-SUFFIX
                    if domain.count('.') >= 2:
                        suffix = get_domain_suffix(domain)
                        f.write(f'- DOMAIN-SUFFIX,{suffix},DIRECT\n')
                    else:
                        f.write(f'- DOMAIN,{domain},DIRECT\n')
                    print(f"  + {domain}")
            print(f"已添加 {len(direct_candidates)} 条规则")

if __name__ == '__main__':
    main()
