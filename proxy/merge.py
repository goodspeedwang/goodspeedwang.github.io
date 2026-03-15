#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理订阅合并工具
用于合并两个 Clash 订阅，并自定义路由规则
"""

import os
import sys
import warnings

# 忽略 urllib3 的 OpenSSL 警告（macOS LibreSSL 兼容性问题）
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')

import requests
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from io import StringIO
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置（从环境变量读取）
MAIN_URL = os.getenv('MAIN_CONFIG_URL')
VIDEO_URL = os.getenv('VIDEO_CONFIG_URL')
MAIN_NAME = os.getenv('MAIN_CONFIG_NAME', '主配置')
VIDEO_NAME = os.getenv('VIDEO_CONFIG_NAME', '视频配置')
OUTPUT_PATH = os.getenv('OUTPUT_PATH', './merged.yaml')
USE_CACHE = os.getenv('USE_CACHE', 'false').lower() == 'true'
CACHE_DIR = './cache'

# 检查必需的环境变量
if not MAIN_URL or not VIDEO_URL:
    raise ValueError(
        "请设置环境变量 MAIN_CONFIG_URL 和 VIDEO_CONFIG_URL。\n"
        "复制 .env.example 为 .env 并填入真实的订阅链接。"
    )

# 请求头
HEADERS = {
    'User-Agent': 'Clash/1.18.0'
}

# YouTube 规则（2025-06-06 更新）
YOUTUBE_RULES = [
    # DOMAIN-SUFFIX (179条)
    "DOMAIN-SUFFIX,ggpht.cn",
    "DOMAIN-SUFFIX,ggpht.com",
    "DOMAIN-SUFFIX,googlevideo.com",
    "DOMAIN-SUFFIX,gvt1.com",
    "DOMAIN-SUFFIX,gvt2.com",
    "DOMAIN-SUFFIX,video.google.com",
    "DOMAIN-SUFFIX,wide-youtube.l.google.com",
    "DOMAIN-SUFFIX,withyoutube.com",
    "DOMAIN-SUFFIX,youtu.be",
    "DOMAIN-SUFFIX,youtube",
    "DOMAIN-SUFFIX,youtube-nocookie.com",
    "DOMAIN-SUFFIX,youtube-ui.l.google.com",
    "DOMAIN-SUFFIX,youtube.ae",
    "DOMAIN-SUFFIX,youtube.al",
    "DOMAIN-SUFFIX,youtube.am",
    "DOMAIN-SUFFIX,youtube.at",
    "DOMAIN-SUFFIX,youtube.az",
    "DOMAIN-SUFFIX,youtube.ba",
    "DOMAIN-SUFFIX,youtube.be",
    "DOMAIN-SUFFIX,youtube.bg",
    "DOMAIN-SUFFIX,youtube.bh",
    "DOMAIN-SUFFIX,youtube.bo",
    "DOMAIN-SUFFIX,youtube.by",
    "DOMAIN-SUFFIX,youtube.ca",
    "DOMAIN-SUFFIX,youtube.cat",
    "DOMAIN-SUFFIX,youtube.ch",
    "DOMAIN-SUFFIX,youtube.cl",
    "DOMAIN-SUFFIX,youtube.co",
    "DOMAIN-SUFFIX,youtube.co.ae",
    "DOMAIN-SUFFIX,youtube.co.at",
    "DOMAIN-SUFFIX,youtube.co.cr",
    "DOMAIN-SUFFIX,youtube.co.hu",
    "DOMAIN-SUFFIX,youtube.co.id",
    "DOMAIN-SUFFIX,youtube.co.il",
    "DOMAIN-SUFFIX,youtube.co.in",
    "DOMAIN-SUFFIX,youtube.co.jp",
    "DOMAIN-SUFFIX,youtube.co.ke",
    "DOMAIN-SUFFIX,youtube.co.kr",
    "DOMAIN-SUFFIX,youtube.co.ma",
    "DOMAIN-SUFFIX,youtube.co.nz",
    "DOMAIN-SUFFIX,youtube.co.th",
    "DOMAIN-SUFFIX,youtube.co.tz",
    "DOMAIN-SUFFIX,youtube.co.ug",
    "DOMAIN-SUFFIX,youtube.co.uk",
    "DOMAIN-SUFFIX,youtube.co.ve",
    "DOMAIN-SUFFIX,youtube.co.za",
    "DOMAIN-SUFFIX,youtube.co.zw",
    "DOMAIN-SUFFIX,youtube.com",
    "DOMAIN-SUFFIX,youtube.com.ar",
    "DOMAIN-SUFFIX,youtube.com.au",
    "DOMAIN-SUFFIX,youtube.com.az",
    "DOMAIN-SUFFIX,youtube.com.bd",
    "DOMAIN-SUFFIX,youtube.com.bh",
    "DOMAIN-SUFFIX,youtube.com.bo",
    "DOMAIN-SUFFIX,youtube.com.br",
    "DOMAIN-SUFFIX,youtube.com.by",
    "DOMAIN-SUFFIX,youtube.com.co",
    "DOMAIN-SUFFIX,youtube.com.do",
    "DOMAIN-SUFFIX,youtube.com.ec",
    "DOMAIN-SUFFIX,youtube.com.ee",
    "DOMAIN-SUFFIX,youtube.com.eg",
    "DOMAIN-SUFFIX,youtube.com.es",
    "DOMAIN-SUFFIX,youtube.com.gh",
    "DOMAIN-SUFFIX,youtube.com.gr",
    "DOMAIN-SUFFIX,youtube.com.gt",
    "DOMAIN-SUFFIX,youtube.com.hk",
    "DOMAIN-SUFFIX,youtube.com.hn",
    "DOMAIN-SUFFIX,youtube.com.hr",
    "DOMAIN-SUFFIX,youtube.com.jm",
    "DOMAIN-SUFFIX,youtube.com.jo",
    "DOMAIN-SUFFIX,youtube.com.kw",
    "DOMAIN-SUFFIX,youtube.com.lb",
    "DOMAIN-SUFFIX,youtube.com.lv",
    "DOMAIN-SUFFIX,youtube.com.ly",
    "DOMAIN-SUFFIX,youtube.com.mk",
    "DOMAIN-SUFFIX,youtube.com.mt",
    "DOMAIN-SUFFIX,youtube.com.mx",
    "DOMAIN-SUFFIX,youtube.com.my",
    "DOMAIN-SUFFIX,youtube.com.ng",
    "DOMAIN-SUFFIX,youtube.com.ni",
    "DOMAIN-SUFFIX,youtube.com.om",
    "DOMAIN-SUFFIX,youtube.com.pa",
    "DOMAIN-SUFFIX,youtube.com.pe",
    "DOMAIN-SUFFIX,youtube.com.ph",
    "DOMAIN-SUFFIX,youtube.com.pk",
    "DOMAIN-SUFFIX,youtube.com.pt",
    "DOMAIN-SUFFIX,youtube.com.py",
    "DOMAIN-SUFFIX,youtube.com.qa",
    "DOMAIN-SUFFIX,youtube.com.ro",
    "DOMAIN-SUFFIX,youtube.com.sa",
    "DOMAIN-SUFFIX,youtube.com.sg",
    "DOMAIN-SUFFIX,youtube.com.sv",
    "DOMAIN-SUFFIX,youtube.com.tn",
    "DOMAIN-SUFFIX,youtube.com.tr",
    "DOMAIN-SUFFIX,youtube.com.tw",
    "DOMAIN-SUFFIX,youtube.com.ua",
    "DOMAIN-SUFFIX,youtube.com.uy",
    "DOMAIN-SUFFIX,youtube.com.ve",
    "DOMAIN-SUFFIX,youtube.cr",
    "DOMAIN-SUFFIX,youtube.cz",
    "DOMAIN-SUFFIX,youtube.de",
    "DOMAIN-SUFFIX,youtube.dk",
    "DOMAIN-SUFFIX,youtube.ee",
    "DOMAIN-SUFFIX,youtube.es",
    "DOMAIN-SUFFIX,youtube.fi",
    "DOMAIN-SUFFIX,youtube.fr",
    "DOMAIN-SUFFIX,youtube.ge",
    "DOMAIN-SUFFIX,youtube.googleapis.com",
    "DOMAIN-SUFFIX,youtube.gr",
    "DOMAIN-SUFFIX,youtube.gt",
    "DOMAIN-SUFFIX,youtube.hk",
    "DOMAIN-SUFFIX,youtube.hr",
    "DOMAIN-SUFFIX,youtube.hu",
    "DOMAIN-SUFFIX,youtube.ie",
    "DOMAIN-SUFFIX,youtube.in",
    "DOMAIN-SUFFIX,youtube.iq",
    "DOMAIN-SUFFIX,youtube.is",
    "DOMAIN-SUFFIX,youtube.it",
    "DOMAIN-SUFFIX,youtube.jo",
    "DOMAIN-SUFFIX,youtube.jp",
    "DOMAIN-SUFFIX,youtube.kr",
    "DOMAIN-SUFFIX,youtube.kz",
    "DOMAIN-SUFFIX,youtube.la",
    "DOMAIN-SUFFIX,youtube.lk",
    "DOMAIN-SUFFIX,youtube.lt",
    "DOMAIN-SUFFIX,youtube.lu",
    "DOMAIN-SUFFIX,youtube.lv",
    "DOMAIN-SUFFIX,youtube.ly",
    "DOMAIN-SUFFIX,youtube.ma",
    "DOMAIN-SUFFIX,youtube.md",
    "DOMAIN-SUFFIX,youtube.me",
    "DOMAIN-SUFFIX,youtube.mk",
    "DOMAIN-SUFFIX,youtube.mn",
    "DOMAIN-SUFFIX,youtube.mx",
    "DOMAIN-SUFFIX,youtube.my",
    "DOMAIN-SUFFIX,youtube.ng",
    "DOMAIN-SUFFIX,youtube.ni",
    "DOMAIN-SUFFIX,youtube.nl",
    "DOMAIN-SUFFIX,youtube.no",
    "DOMAIN-SUFFIX,youtube.pa",
    "DOMAIN-SUFFIX,youtube.pe",
    "DOMAIN-SUFFIX,youtube.ph",
    "DOMAIN-SUFFIX,youtube.pk",
    "DOMAIN-SUFFIX,youtube.pl",
    "DOMAIN-SUFFIX,youtube.pr",
    "DOMAIN-SUFFIX,youtube.pt",
    "DOMAIN-SUFFIX,youtube.qa",
    "DOMAIN-SUFFIX,youtube.ro",
    "DOMAIN-SUFFIX,youtube.rs",
    "DOMAIN-SUFFIX,youtube.ru",
    "DOMAIN-SUFFIX,youtube.sa",
    "DOMAIN-SUFFIX,youtube.se",
    "DOMAIN-SUFFIX,youtube.sg",
    "DOMAIN-SUFFIX,youtube.si",
    "DOMAIN-SUFFIX,youtube.sk",
    "DOMAIN-SUFFIX,youtube.sn",
    "DOMAIN-SUFFIX,youtube.soy",
    "DOMAIN-SUFFIX,youtube.sv",
    "DOMAIN-SUFFIX,youtube.tn",
    "DOMAIN-SUFFIX,youtube.tv",
    "DOMAIN-SUFFIX,youtube.ua",
    "DOMAIN-SUFFIX,youtube.ug",
    "DOMAIN-SUFFIX,youtube.uy",
    "DOMAIN-SUFFIX,youtube.vn",
    "DOMAIN-SUFFIX,youtubeeducation.com",
    "DOMAIN-SUFFIX,youtubeembeddedplayer.googleapis.com",
    "DOMAIN-SUFFIX,youtubefanfest.com",
    "DOMAIN-SUFFIX,youtubegaming.com",
    "DOMAIN-SUFFIX,youtubego.co.id",
    "DOMAIN-SUFFIX,youtubego.co.in",
    "DOMAIN-SUFFIX,youtubego.com",
    "DOMAIN-SUFFIX,youtubego.com.br",
    "DOMAIN-SUFFIX,youtubego.id",
    "DOMAIN-SUFFIX,youtubego.in",
    "DOMAIN-SUFFIX,youtubei.googleapis.com",
    "DOMAIN-SUFFIX,youtubekids.com",
    "DOMAIN-SUFFIX,youtubemobilesupport.com",
    "DOMAIN-SUFFIX,yt.be",
    "DOMAIN-SUFFIX,ytimg.com",
    # DOMAIN-KEYWORD
    "DOMAIN-KEYWORD,youtube",
    # X.com 视频
    "DOMAIN-SUFFIX,video.twimg.com",
    "DOMAIN-SUFFIX,pscp.tv",
    "DOMAIN-KEYWORD,video.twimg.com",
    # IP-CIDR
    "IP-CIDR,172.110.32.0/21",
    "IP-CIDR,216.73.80.0/20",
    "IP-CIDR6,2620:120:e000::/40",
]

# AI 服务规则（2025-06-06 更新）
AI_RULES = [
    # OpenAI / ChatGPT (35条)
    "DOMAIN,browser-intake-datadoghq.com",
    "DOMAIN,chat.openai.com.cdn.cloudflare.net",
    "DOMAIN,openai-api.arkoselabs.com",
    "DOMAIN,openaicom-api-bdcpf8c6d2e9atf6.z01.azurefd.net",
    "DOMAIN,openaicomproductionae4b.blob.core.windows.net",
    "DOMAIN,production-openaicom-storage.azureedge.net",
    "DOMAIN,static.cloudflareinsights.com",
    "DOMAIN-SUFFIX,ai.com",
    "DOMAIN-SUFFIX,algolia.net",
    "DOMAIN-SUFFIX,api.statsig.com",
    "DOMAIN-SUFFIX,auth0.com",
    "DOMAIN-SUFFIX,chatgpt.com",
    "DOMAIN-SUFFIX,chatgpt.livekit.cloud",
    "DOMAIN-SUFFIX,client-api.arkoselabs.com",
    "DOMAIN-SUFFIX,events.statsigapi.net",
    "DOMAIN-SUFFIX,featuregates.org",
    "DOMAIN-SUFFIX,host.livekit.cloud",
    "DOMAIN-SUFFIX,identrust.com",
    "DOMAIN-SUFFIX,intercom.io",
    "DOMAIN-SUFFIX,intercomcdn.com",
    "DOMAIN-SUFFIX,launchdarkly.com",
    "DOMAIN-SUFFIX,oaistatic.com",
    "DOMAIN-SUFFIX,oaiusercontent.com",
    "DOMAIN-SUFFIX,observeit.net",
    "DOMAIN-SUFFIX,openai.com",
    "DOMAIN-SUFFIX,openaiapi-site.azureedge.net",
    "DOMAIN-SUFFIX,openaicom.imgix.net",
    "DOMAIN-SUFFIX,segment.io",
    "DOMAIN-SUFFIX,sentry.io",
    "DOMAIN-SUFFIX,stripe.com",
    "DOMAIN-SUFFIX,turn.livekit.cloud",
    "DOMAIN-KEYWORD,openai",
    "IP-CIDR,24.199.123.28/32",
    "IP-CIDR,64.23.132.171/32",
    "IP-ASN,20473",
    # Gemini / Google AI (13条)
    "DOMAIN,ai.google.dev",
    "DOMAIN,alkalimakersuite-pa.clients6.google.com",
    "DOMAIN,makersuite.google.com",
    "DOMAIN-SUFFIX,bard.google.com",
    "DOMAIN-SUFFIX,deepmind.com",
    "DOMAIN-SUFFIX,deepmind.google",
    "DOMAIN-SUFFIX,gemini.google.com",
    "DOMAIN-SUFFIX,generativeai.google",
    "DOMAIN-SUFFIX,proactivebackend-pa.googleapis.com",
    "DOMAIN-SUFFIX,apis.google.com",
    "DOMAIN-KEYWORD,colab",
    "DOMAIN-KEYWORD,developerprofiles",
    "DOMAIN-KEYWORD,generativelanguage",
    # Anthropic / Claude (3条，2025-06-06 更新)
    "DOMAIN,cdn.usefathom.com",
    "DOMAIN-SUFFIX,anthropic.com",
    "DOMAIN-SUFFIX,claude.ai",
    # Grok / X.AI (新增)
    "DOMAIN-SUFFIX,x.ai",
    "DOMAIN-SUFFIX,grok.com",
    "DOMAIN-KEYWORD,grok",
]

# 香港节点关键词
HK_KEYWORDS = ["HK", "Hong Kong", "香港", "HongKong", "HONG KONG"]

# rules.conf 文件路径
RULES_CONF_PATH = './rules.conf'


def get_china_direct_rules() -> List[str]:
    """获取国内直连规则列表（最高优先级）"""
    rules = []

    # 只保留 GEOIP,CN 规则（不包含具体的域名规则）
    rules.append('GEOIP,CN,DIRECT,no-resolve')

    return rules


def download_subscription(url: str, name: str) -> Dict[str, Any]:
    """下载订阅配置"""
    cache_file = os.path.join(CACHE_DIR, f"{name}.yaml")

    # 检查是否使用缓存
    if USE_CACHE and os.path.exists(cache_file):
        print(f"使用缓存的 {name} 订阅...")
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"{name} 订阅加载成功（缓存），包含 {len(config.get('proxies', []))} 个节点")
            return config
        except Exception as e:
            print(f"加载缓存失败: {e}，将重新下载")

    # 下载订阅
    print(f"正在下载 {name} 订阅...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        config = yaml.safe_load(response.text)
        print(f"{name} 订阅下载成功，包含 {len(config.get('proxies', []))} 个节点")

        # 保存到缓存
        if USE_CACHE:
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                print(f"{name} 订阅已缓存到: {cache_file}")
            except Exception as e:
                print(f"保存缓存失败: {e}")

        return config
    except requests.RequestException as e:
        print(f"下载 {name} 订阅失败: {e}")
        raise


def is_hk_node(node_name: str) -> bool:
    """判断是否为香港节点"""
    for keyword in HK_KEYWORDS:
        if keyword.lower() in node_name.lower():
            return True
    return False


def load_rules_conf() -> List[str]:
    """加载 rules.conf 文件中的规则"""
    rules = []
    if os.path.exists(RULES_CONF_PATH):
        print(f"加载自定义规则文件: {RULES_CONF_PATH}")
        try:
            with open(RULES_CONF_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if line and not line.startswith('#'):
                        # 移除行首的 - 前缀（如果有）
                        if line.startswith('-'):
                            line = line[1:].strip()
                        rules.append(line)
            print(f"已加载 {len(rules)} 条自定义规则")
        except Exception as e:
            print(f"加载 rules.conf 失败: {e}")
    else:
        print(f"未找到 rules.conf 文件，将不添加自定义规则")
    return rules


def categorize_nodes(proxies: List[Dict[str, Any]], source_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """分类节点：香港节点和非香港节点"""
    hk_nodes = []
    non_hk_nodes = []

    for proxy in proxies:
        # 修改节点名称，添加来源前缀
        proxy = proxy.copy()
        original_name = proxy.get('name', '')
        proxy['name'] = f"{source_name} | {original_name}"

        if is_hk_node(original_name):
            hk_nodes.append(proxy)
        else:
            non_hk_nodes.append(proxy)

    return {
        'hk': hk_nodes,
        'non_hk': non_hk_nodes
    }


def create_proxy_groups(video_nodes: List[Dict[str, Any]],
                       main_non_hk_nodes: List[Dict[str, Any]],
                       all_nodes: List[Dict[str, Any]],
                       main_name: str,
                       video_name: str) -> List[Dict[str, Any]]:
    """创建代理组"""
    video_names = [node['name'] for node in video_nodes]
    main_non_hk_names = [node['name'] for node in main_non_hk_nodes]
    all_names = [node['name'] for node in all_nodes]

    proxy_groups = [
        {
            'name': 'Auto-Select',
            'type': 'url-test',
            'proxies': all_names if all_names else ['Global-Group'],
            'url': 'https://www.cloudflare.com/cdn-cgi/trace',
            'interval': 300
        },
        {
            'name': 'Video-Auto',
            'type': 'url-test',
            'proxies': video_names if video_names else ['Global-Group'],
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300
        },
        {
            'name': 'Video-Group',
            'type': 'select',
            'proxies': ['Video-Auto', 'DIRECT', *video_names, 'Global-Group']
        },
        {
            'name': 'AI-NonHK-Group',
            'type': 'select',
            'proxies': ['DIRECT', *main_non_hk_names, 'Global-Group']
        },
        {
            'name': 'AI-Select',
            'type': 'url-test',
            'proxies': main_non_hk_names if main_non_hk_names else ['Global-Group'],
            'url': 'https://www.cloudflare.com/cdn-cgi/trace',
            'interval': 300
        },
        {
            'name': 'Global-Group',
            'type': 'select',
            'proxies': ['Auto-Select', 'DIRECT', *all_names]
        },
        {
            'name': '🐟 漏网之鱼',
            'type': 'select',
            'proxies': ['Global-Group']
        },
    ]

    return proxy_groups


def create_rules(cloudfare_nodes: List[Dict[str, Any]],
                ai_select_group: str) -> List[str]:
    """创建规则"""
    rules = []

    # YouTube 规则
    for rule in YOUTUBE_RULES:
        rules.append(f"{rule},Video-Group")

    # AI 服务规则
    for rule in AI_RULES:
        rules.append(f"{rule},{ai_select_group}")

    # 不在这里添加 MATCH 规则，它应该在所有规则的最后面

    return rules


def filter_and_fix_rules(original_rules: List[str], custom_rules: List[str], rules_conf: List[str], our_proxy_groups: List[str]) -> List[str]:
    """过滤并修复原有规则"""
    # 从 rules.conf 中提取所有匹配目标（域名、IP段等），用于冲突检测
    rules_conf_targets = set()
    for rule in rules_conf:
        parts = rule.split(',')
        if len(parts) >= 2:
            # 提取第二个字段作为目标（域名、IP段等）
            target = parts[1].strip()
            rules_conf_targets.add(target.lower())

    # 过滤和修复原有规则
    filtered_rules = []
    for rule in original_rules:
        skip = False

        # 跳过原配置中的 GEOIP,CN 规则（我们会添加自己的国内直连规则作为最高优先级）
        if 'GEOIP,CN' in rule:
            skip = True

        # 跳过原配置中的 MATCH 规则（我们会添加自己的 MATCH 规则在最后）
        if rule.startswith('MATCH,'):
            skip = True

        # 跳过原配置中的 YouTube 相关规则（我们的自定义规则会覆盖）
        if 'youtube' in rule.lower():
            skip = True

        # 跳过原配置中的 AI 服务相关规则（我们的自定义规则会覆盖）
        if any(keyword in rule.lower() for keyword in ['openai', 'chatgpt', 'claude', 'anthropic', 'gemini', 'bard']):
            skip = True

        # 检测国内 IP 段（私有 IP）
        if any(ip in rule for ip in ['IP-CIDR,10.', 'IP-CIDR,172.16.', 'IP-CIDR,192.168.', 'IP-CIDR,127.']):
            skip = True

        # 冲突检测：如果规则的目标与 rules.conf 中的目标相同，则跳过
        if not skip:
            parts = rule.split(',')
            if len(parts) >= 2:
                target = parts[1].strip()
                if target.lower() in rules_conf_targets:
                    skip = True

        if not skip:
            # 修复规则：将不存在的代理组替换为 Global-Group
            # 规则格式: TYPE,MATCH,PROXY-GROUP[,OPTION]
            # 或者: TYPE,MATCH[,OPTION],PROXY-GROUP
            # 需要找到代理组名称（通常是第三个或第四个字段）
            rule_parts = rule.split(',')

            # 检查是否有中间字段（如 no-resolve）
            # 如果规则长度是4，且最后一个部分是常见选项，则代理组在第三个位置
            if len(rule_parts) == 4:
                last_part = rule_parts[-1].strip()
                if last_part in ['no-resolve', 'no-ip', 'reject', 'direct']:
                    # 代理组在第三个位置
                    proxy_group = rule_parts[2].strip()
                    # 先将 🔰 选择节点 替换为 Auto-Select
                    if proxy_group == '🔰 选择节点':
                        rule_parts[2] = 'Auto-Select'
                    elif proxy_group not in our_proxy_groups:
                        rule_parts[2] = 'Global-Group'
                else:
                    # 代理组在最后一个位置
                    proxy_group = last_part
                    # 先将 🔰 选择节点 替换为 Auto-Select
                    if proxy_group == '🔰 选择节点':
                        rule_parts[-1] = 'Auto-Select'
                    elif proxy_group not in our_proxy_groups:
                        rule_parts[-1] = 'Global-Group'
            elif len(rule_parts) == 3:
                # 代理组在最后一个位置
                proxy_group = rule_parts[2].strip()
                # 先将 🔰 选择节点 替换为 Auto-Select
                if proxy_group == '🔰 选择节点':
                    rule_parts[2] = 'Auto-Select'
                elif proxy_group not in our_proxy_groups:
                    rule_parts[2] = 'Global-Group'
            elif len(rule_parts) >= 5:
                # 更复杂的规则格式，尝试找到代理组
                # 通常是倒数第一个，或者倒数第三个（如果最后是no-resolve）
                last_part = rule_parts[-1].strip()
                if last_part in ['no-resolve', 'no-ip', 'reject', 'direct']:
                    if len(rule_parts) >= 4:
                        proxy_group = rule_parts[-3].strip()
                        # 先将 🔰 选择节点 替换为 Auto-Select
                        if proxy_group == '🔰 选择节点':
                            rule_parts[-3] = 'Auto-Select'
                        elif proxy_group not in our_proxy_groups:
                            rule_parts[-3] = 'Global-Group'
                else:
                    proxy_group = last_part
                    # 先将 🔰 选择节点 替换为 Auto-Select
                    if proxy_group == '🔰 选择节点':
                        rule_parts[-1] = 'Auto-Select'
                    elif proxy_group not in our_proxy_groups:
                        rule_parts[-1] = 'Global-Group'

            rule = ','.join(rule_parts)
            filtered_rules.append(rule)

    return filtered_rules


def format_proxy_yaml(proxy: Dict[str, Any]) -> str:
    """将代理配置格式化为 Flow Style 的 YAML 字符串"""
    return "  " + yaml.dump(proxy, allow_unicode=True, default_flow_style=True, sort_keys=False).strip()


def save_config_with_flow_style(config: Dict[str, Any], output_path: Path):
    """保存配置，proxies 使用 Flow Style（和 ikuuu 一致的格式）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入基本配置（使用小写的 true/false）
        f.write(f"port: {config['port']}\n")
        f.write(f"socks-port: {config['socks-port']}\n")
        f.write(f"allow-lan: {str(config['allow_lan']).lower()}\n")
        f.write(f"mode: {config['mode']}\n")
        f.write(f"log-level: {config['log_level']}\n")
        f.write(f"external-controller: {config['external_controller']}\n")
        f.write(f"unified-delay: {str(config['unified_delay']).lower()}\n")
        
        # 写入 proxies（使用 Flow Style，单行格式）
        f.write("proxies:\n")
        for proxy in config['proxies']:
            # 转换为单行 YAML
            proxy_str = yaml.dump(proxy, allow_unicode=True, default_flow_style=True, sort_keys=False, width=2147483647)
            proxy_str = proxy_str.replace('\n', ' ')  # 将多行合并为一行
            proxy_str = ' '.join(proxy_str.split())  # 去除多余空格
            f.write(f"  - {proxy_str}\n")
        
        # 写入其他配置
        f.write(yaml.dump({'proxy-groups': config['proxy_groups']}, allow_unicode=True, default_flow_style=False, sort_keys=False))
        f.write("rules:\n")
        for rule in config['rules']:
            f.write(f"  - {rule}\n")


def merge_subscriptions():
    """合并订阅配置"""
    # 加载自定义规则文件（最高优先级）
    rules_conf = load_rules_conf()

    # 下载订阅
    main_config = download_subscription(MAIN_URL, MAIN_NAME)
    video_config = download_subscription(VIDEO_URL, VIDEO_NAME)

    # 分类节点（主配置用于 AI 服务）
    main_nodes = categorize_nodes(main_config.get('proxies', []), MAIN_NAME)
    video_nodes = [node.copy() for node in video_config.get('proxies', [])]
    for node in video_nodes:
        node['name'] = f"{VIDEO_NAME} | {node['name']}"

    # 合并所有节点
    all_proxies = video_nodes + main_nodes['hk'] + main_nodes['non_hk']

    # 创建代理组
    proxy_groups = create_proxy_groups(
        video_nodes,
        main_nodes['non_hk'],
        all_proxies,
        MAIN_NAME,
        VIDEO_NAME
    )

    # 创建节点名称映射（原始名称 -> 带前缀的名称）
    # 用于修复主配置代理组中的节点引用
    node_name_map = {}
    for node in main_nodes['hk'] + main_nodes['non_hk']:
        original_name = node['name'].split(f'{MAIN_NAME} | ')[-1]
        node_name_map[original_name] = node['name']

    # 保留主配置中的代理组（除了我们已有的组）
    our_proxy_group_names = [group['name'] for group in proxy_groups]
    main_proxy_groups = main_config.get('proxy-groups', [])
    for group in main_proxy_groups:
        # 跳过 🔰 选择节点 组，将其替换为 Auto-Select
        if group['name'] == '🔰 选择节点':
            continue
        if group['name'] not in our_proxy_group_names:
            # 修复代理组中的节点名称，添加前缀
            group = group.copy()
            if 'proxies' in group:
                new_proxies = []
                for proxy in group['proxies']:
                    if proxy == '🔰 选择节点':
                        # 将 🔰 选择节点 替换为 Global-Select（Auto-Select 的别名）
                        # 因为 url-test 类型不能被直接引用，需要通过 select 类型的组
                        new_proxies.append('Auto-Select')
                    elif proxy in node_name_map:
                        new_proxies.append(node_name_map[proxy])
                    else:
                        # 保留DIRECT、REJECT等特殊值，以及其他代理组名称
                        new_proxies.append(proxy)
                group['proxies'] = new_proxies
            proxy_groups.append(group)
            our_proxy_group_names.append(group['name'])

    # 创建自定义规则
    custom_rules = create_rules(video_nodes, 'AI-Select')

    # 过滤并修复原有规则（使用主配置的规则作为基础）
    original_rules = main_config.get('rules', [])
    filtered_rules = filter_and_fix_rules(original_rules, custom_rules, rules_conf, our_proxy_group_names)

    # 合并规则：rules.conf（最高优先级）+ 国内直连规则 + 视频/AI规则 + 其他规则
    # rules.conf 的优先级最高，放在最前面
    # 国内直连规则放在第二位
    # 注意：国内域名规则要在 main 配置的域名规则之前，避免被覆盖
    china_rules = get_china_direct_rules()

    # 将 MATCH 规则放在最后面
    all_rules = rules_conf + china_rules + custom_rules + filtered_rules + ['MATCH,🐟 漏网之鱼']

    # 构建最终配置
    merged_config = {
        'port': 7890,
        'socks-port': 7891,
        'allow_lan': False,
        'mode': 'Rule',
        'log_level': 'info',
        'external_controller': '127.0.0.1:9090',
        'unified_delay': True,
        'proxies': all_proxies,
        'proxy_groups': proxy_groups,
        'rules': all_rules
    }

    # 保存配置（使用 Flow Style 格式）
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_config_with_flow_style(merged_config, output_path)

    print(f"\n配置已保存到: {OUTPUT_PATH}")
    print(f"统计信息:")
    print(f"  - 总节点数: {len(all_proxies)}")
    print(f"    - {VIDEO_NAME} 节点: {len(video_nodes)}")
    print(f"    - {MAIN_NAME} 香港节点: {len(main_nodes['hk'])}")
    print(f"    - {MAIN_NAME} 非香港节点: {len(main_nodes['non_hk'])}")
    print(f"  - 代理组数: {len(proxy_groups)}")
    print(f"  - 规则数: {len(all_rules)}")
    print(f"    - rules.conf 自定义规则: {len(rules_conf)}")
    print(f"    - 国内直连规则: {len(china_rules)}")
    print(f"    - YouTube 规则: {len(YOUTUBE_RULES)}")
    print(f"    - AI 服务规则: {len(AI_RULES)}")
    print(f"    - 其他规则: {len(filtered_rules)}")


def main():
    """主函数"""
    try:
        merge_subscriptions()
        print("\n合并完成！")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
