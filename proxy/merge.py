#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理订阅合并工具 - 重构版
用法: python3 merge_v2.py

功能:
1. 合并主配置和视频配置的订阅
2. 自动分类香港/非香港节点
3. 应用自定义路由规则:
   - YouTube/X视频 → Video-Group
   - OpenAI/Claude/Grok → AI-Select (非香港节点)
   - Gemini → Auto-Select (已支持香港)
   - 其他外网 → Auto-Select
   - 国内流量 → DIRECT
4. 广告屏蔽 (X/Twitter广告)
"""

import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Any

warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')

import requests
import yaml
from dotenv import load_dotenv

# 加载本地模块
from rules_data import (
    get_youtube_rules, get_ai_rules, AD_BLOCK_RULES, HK_KEYWORDS
)

# 加载环境变量
load_dotenv()

# 配置
MAIN_URL = os.getenv('MAIN_CONFIG_URL')
VIDEO_URL = os.getenv('VIDEO_CONFIG_URL')
MAIN_NAME = os.getenv('MAIN_CONFIG_NAME', '主配置')
VIDEO_NAME = os.getenv('VIDEO_CONFIG_NAME', '视频配置')
OUTPUT_PATH = os.getenv('OUTPUT_PATH', './merged.yaml')
USE_CACHE = os.getenv('USE_CACHE', 'false').lower() == 'true'
CACHE_DIR = './cache'
RULES_CONF_PATH = './rules.conf'

if not MAIN_URL or not VIDEO_URL:
    raise ValueError("请设置 MAIN_CONFIG_URL 和 VIDEO_CONFIG_URL 环境变量")

HEADERS = {'User-Agent': 'Clash/1.18.0'}


class ConfigMerger:
    """配置合并器"""
    
    def __init__(self):
        self.main_config = None
        self.video_config = None
        self.rules_conf = []
        
    def download(self, url: str, name: str) -> Dict:
        """下载订阅配置"""
        cache_file = Path(CACHE_DIR) / f"{name}.yaml"
        
        if USE_CACHE and cache_file.exists():
            print(f"使用缓存: {name}")
            return yaml.safe_load(cache_file.read_text())
        
        print(f"下载: {name}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        config = yaml.safe_load(resp.text)
        
        if USE_CACHE:
            cache_file.parent.mkdir(exist_ok=True)
            cache_file.write_text(resp.text)
        
        return config
    
    def load_rules_conf(self) -> List[str]:
        """加载自定义规则文件"""
        if not Path(RULES_CONF_PATH).exists():
            return []
        
        rules = []
        for line in open(RULES_CONF_PATH, 'r', encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('-'):
                    line = line[1:].strip()
                rules.append(line)
        return rules
    
    def is_hk_node(self, name: str) -> bool:
        """判断是否为香港节点"""
        return any(kw.lower() in name.lower() for kw in HK_KEYWORDS)
    
    def categorize_main_nodes(self, proxies: List[Dict]) -> Dict[str, List[Dict]]:
        """分类主配置节点为香港/非香港"""
        hk, non_hk = [], []
        for p in proxies:
            p = p.copy()
            orig_name = p.get('name', '')
            p['name'] = f"{MAIN_NAME} | {orig_name}"
            (hk if self.is_hk_node(orig_name) else non_hk).append(p)
        return {'hk': hk, 'non_hk': non_hk}
    
    def prefix_video_nodes(self, proxies: List[Dict]) -> List[Dict]:
        """为视频配置节点添加前缀"""
        return [{**p, 'name': f"{VIDEO_NAME} | {p['name']}"}
                for p in proxies]
    
    def create_proxy_groups(self, video_nodes: List[Dict], 
                           main_hk: List[Dict], 
                           main_non_hk: List[Dict]) -> List[Dict]:
        """创建代理组"""
        video_names = [n['name'] for n in video_nodes]
        main_hk_names = [n['name'] for n in main_hk]
        main_non_hk_names = [n['name'] for n in main_non_hk]
        main_all = main_hk_names + main_non_hk_names
        all_names = main_all + video_names
        
        return [
            {
                'name': 'Auto-Select',
                'type': 'url-test',
                'proxies': main_all or ['Global-Group'],
                'url': 'https://www.cloudflare.com/cdn-cgi/trace',
                'interval': 300
            },
            {
                'name': 'Video-Auto',
                'type': 'url-test',
                'proxies': video_names or ['Global-Group'],
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
                'proxies': main_non_hk_names or ['Global-Group'],
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
    
    def should_skip_original_rule(self, rule: str, rules_conf_targets: set) -> bool:
        """判断是否应该跳过原配置的某条规则"""
        # 跳过国内规则
        if 'GEOIP,CN' in rule or 'MATCH,' in rule:
            return True
        
        # 跳过 YouTube 相关规则
        if 'youtube' in rule.lower():
            return True
        
        # 跳过 AI 相关规则（不包括 Gemini，因为没添加显式规则）
        if any(kw in rule.lower() for kw in ['openai', 'chatgpt', 'claude', 'anthropic', 'grok']):
            return True
        
        # 跳过私有IP段
        if any(ip in rule for ip in ['IP-CIDR,10.', 'IP-CIDR,172.16.', 'IP-CIDR,192.168.', 'IP-CIDR,127.']):
            return True
        
        # 跳过与 rules.conf 冲突的规则
        parts = rule.split(',')
        if len(parts) >= 2 and parts[1].strip().lower() in rules_conf_targets:
            return True
        
        return False
    
    def fix_proxy_group_ref(self, rule: str, our_groups: List[str]) -> str:
        """修复规则中引用的代理组"""
        parts = rule.split(',')
        if len(parts) < 3:
            return rule
        
        # 找到代理组位置（通常是最后一个或倒数第二个）
        def fix_group_name(name: str) -> str:
            if name == '🔰 选择节点':
                return 'Auto-Select'
            if name not in our_groups and name not in ['DIRECT', 'REJECT']:
                return 'Global-Group'
            return name
        
        # 简单情况：代理组在最后
        if len(parts) == 3:
            parts[2] = fix_group_name(parts[2].strip())
        # 复杂情况：有 no-resolve 等选项
        elif len(parts) >= 4:
            if parts[-1].strip() in ['no-resolve', 'no-ip']:
                parts[-2] = fix_group_name(parts[-2].strip())
            else:
                parts[-1] = fix_group_name(parts[-1].strip())
        
        return ','.join(parts)
    
    def process_original_rules(self, original_rules: List[str], 
                              rules_conf: List[str],
                              our_groups: List[str]) -> List[str]:
        """处理原配置的规则：过滤冲突 + 修复代理组引用"""
        # 提取 rules.conf 中的目标
        conf_targets = set()
        for rule in rules_conf:
            parts = rule.split(',')
            if len(parts) >= 2:
                conf_targets.add(parts[1].strip().lower())
        
        result = []
        for rule in original_rules:
            if self.should_skip_original_rule(rule, conf_targets):
                continue
            result.append(self.fix_proxy_group_ref(rule, our_groups))
        
        return result
    
    def save_config(self, config: Dict, output_path: Path):
        """保存配置为 Flow Style YAML"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # 基本配置
            f.write(f"port: {config['port']}\n")
            f.write(f"socks-port: {config['socks-port']}\n")
            f.write(f"allow-lan: {str(config['allow-lan']).lower()}\n")
            f.write(f"mode: {config['mode']}\n")
            f.write(f"log-level: {config['log-level']}\n")
            f.write(f"external-controller: {config['external-controller']}\n")
            f.write(f"unified-delay: {str(config['unified-delay']).lower()}\n")
            
            # Proxies（单行格式）
            f.write("proxies:\n")
            for proxy in config['proxies']:
                proxy_str = yaml.dump(proxy, default_flow_style=True, 
                                     allow_unicode=True, sort_keys=False, 
                                     width=float('inf'))
                proxy_str = ' '.join(proxy_str.replace('\n', ' ').split())
                f.write(f"  - {proxy_str}\n")
            
            # Proxy-groups
            f.write(yaml.dump({'proxy-groups': config['proxy-groups']}, 
                            allow_unicode=True, default_flow_style=False))
            
            # Rules
            f.write("rules:\n")
            for rule in config['rules']:
                f.write(f"  - {rule}\n")
    
    def merge(self):
        """执行合并"""
        # 1. 加载配置
        self.main_config = self.download(MAIN_URL, MAIN_NAME)
        self.video_config = self.download(VIDEO_URL, VIDEO_NAME)
        self.rules_conf = self.load_rules_conf()
        
        # 2. 处理节点
        main_nodes = self.categorize_main_nodes(self.main_config.get('proxies', []))
        video_nodes = self.prefix_video_nodes(self.video_config.get('proxies', []))
        all_proxies = main_nodes['hk'] + main_nodes['non_hk'] + video_nodes
        
        # 3. 创建代理组
        proxy_groups = self.create_proxy_groups(
            video_nodes, main_nodes['hk'], main_nodes['non_hk']
        )
        our_group_names = [g['name'] for g in proxy_groups]
        
        # 4. 处理主配置的代理组
        for group in self.main_config.get('proxy-groups', []):
            if group['name'] in our_group_names or group['name'] == '🔰 选择节点':
                continue
            
            # 修复节点名称引用
            group = group.copy()
            name_map = {n['name'].split(f'{MAIN_NAME} | ')[-1]: n['name'] 
                       for n in main_nodes['hk'] + main_nodes['non_hk']}
            
            if 'proxies' in group:
                group['proxies'] = [
                    name_map.get(p, 'Auto-Select' if p == '🔰 选择节点' else p)
                    for p in group['proxies']
                ]
            
            proxy_groups.append(group)
            our_group_names.append(group['name'])
        
        # 5. 构建规则
        youtube_rules = [f"{r},Video-Group" for r in get_youtube_rules()]
        ai_rules = [f"{r},AI-Select" for r in get_ai_rules()]
        ad_rules = [f"{r},REJECT" for r in AD_BLOCK_RULES]
        
        original_rules = self.process_original_rules(
            self.main_config.get('rules', []),
            self.rules_conf,
            our_group_names
        )
        
        # 6. 合并所有规则
        all_rules = (
            self.rules_conf +                          # 自定义规则（最高优先级）
            ['GEOIP,CN,DIRECT,no-resolve'] +           # 国内直连
            ad_rules +                                  # 广告屏蔽
            youtube_rules +                             # YouTube
            ai_rules +                                  # AI服务
            original_rules +                            # 原配置规则
            ['MATCH,🐟 漏网之鱼']                       # 兜底
        )
        
        # 7. 构建最终配置
        merged_config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': False,
            'mode': 'Rule',
            'log-level': 'info',
            'external-controller': '127.0.0.1:9090',
            'unified-delay': True,
            'proxies': all_proxies,
            'proxy_groups': proxy_groups,
            'rules': all_rules
        }
        
        # 8. 保存
        output = Path(OUTPUT_PATH)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.save_config(merged_config, output)
        
        # 9. 统计
        print(f"\n配置已保存: {OUTPUT_PATH}")
        print(f"节点: 视频{len(video_nodes)} + 主配置香港{len(main_nodes['hk'])} + 非香港{len(main_nodes['non_hk'])}")
        print(f"代理组: {len(proxy_groups)}")
        print(f"规则: 自定义{len(self.rules_conf)} + YouTube{len(youtube_rules)} + AI{len(ai_rules)} + 广告{len(ad_rules)}")


def main():
    try:
        ConfigMerger().merge()
        print("\n完成!")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
