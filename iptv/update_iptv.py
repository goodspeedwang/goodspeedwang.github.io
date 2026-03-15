#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV频道列表更新脚本
基于新的北京联通IPTV频道列表更新iptv.bj.m3u8文件
"""

import re
import urllib.request
import urllib.error
import ssl
import os
import socket
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class Channel:
    """频道数据结构"""
    rtp_address: str  # rtp地址，作为唯一标识
    name: str  # 新列表中的原始名称
    tvg_id: str = ""
    tvg_name: str = ""
    tvg_logo: str = ""
    group_title: str = ""
    display_name: str = ""  # 显示名称
    is_new: bool = False  # 是否新增频道
    url: str = ""  # 转换后的URL
    is_available: Optional[bool] = None  # 是否可用（None=未检测, True=可用, False=空台）
    test_message: str = ""  # 检测结果信息


class IPTVUpdater:
    """IPTV频道列表更新器"""

    # 新文件URL
    NEW_LIST_URL = "https://gist.githubusercontent.com/sdhzdmzzl/93cf74947770066743fff7c7f4fc5820/raw/2ce1dfe71ae7a5b36677f94d5f4ead165d3d46ea/bj-unicom-iptv.m3u"

    # udpxy代理配置
    PROXY_HOST = "192.168.100.1"
    PROXY_PORT = 5140

    # 分组排序权重
    GROUP_ORDER = {
        "高清|央视": 1,
        "高清|卫视": 2,
        "高清|北京": 3,
        "高清|IPTV": 4,
        "高清|数字": 5,
        "高清|购物": 6,
        "高清|区县": 7,
        "高清|其他": 8,
        "4K": 9,
        "少儿": 10,
        "标清|央视": 11,
        "标清|卫视": 12,
        "标清|北京": 13,
        "标清|IPTV": 14,
        "标清|数字": 15,
        "标清|购物": 16,
        "标清|区县": 17,
        "标清|其他": 18,
    }

    def __init__(self, old_file_path: str, output_path: str):
        self.old_file_path = old_file_path
        self.output_path = output_path
        self.old_channels: Dict[str, Channel] = {}  # rtp_address -> Channel
        self.new_channels: List[Channel] = []
        self.processed_channels: List[Channel] = []

        # 日志记录
        self.log_new_channels: List[Channel] = []
        self.log_duplicates: List[Tuple[str, List[str]]] = []
        self.log_fallback_groups: List[Tuple[str, str]] = []

    def parse_old_file(self) -> None:
        """解析旧文件，建立rtp地址到频道信息的映射"""
        print(f"正在解析旧文件: {self.old_file_path}")

        with open(self.old_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析EXTINF和URL
        pattern = r'#EXTINF:-1([^\n]*)\n([^\n]+)'
        matches = re.findall(pattern, content)

        for extinf, url in matches:
            # 提取rtp地址
            rtp_match = re.search(r'239\.3\.1\.\d+:\d+', url)
            if not rtp_match:
                continue

            rtp_address = rtp_match.group()

            # 解析EXTINF属性
            channel = Channel(rtp_address=rtp_address, name="")

            # 提取tvg-id
            id_match = re.search(r'tvg-id="([^"]*)"', extinf)
            if id_match:
                channel.tvg_id = id_match.group(1)

            # 提取tvg-name
            name_match = re.search(r'tvg-name="([^"]*)"', extinf)
            if name_match:
                channel.tvg_name = name_match.group(1)

            # 提取tvg-logo
            logo_match = re.search(r'tvg-logo="([^"]*)"', extinf)
            if logo_match:
                channel.tvg_logo = logo_match.group(1)

            # 提取group-title
            group_match = re.search(r'group-title="([^"]*)"', extinf)
            if group_match:
                old_group = group_match.group(1)
                channel.group_title = self._convert_group_title(old_group)

            # 提取显示名称（逗号后的内容）
            display_match = re.search(r',([^\n]+)$', extinf)
            if display_match:
                channel.display_name = display_match.group(1).strip()

            channel.url = url.strip()
            self.old_channels[rtp_address] = channel

        print(f"  解析完成，共 {len(self.old_channels)} 个频道")

    def _convert_group_title(self, old_group: str) -> str:
        """将旧分组标题转换为新格式"""
        # 判断清晰度
        is_hd = "高清" in old_group or "4K" in old_group
        is_4k = "4K" in old_group
        is_sd = "标清" in old_group

        if is_4k:
            return "4K"

        # 判断类型
        if "央视" in old_group or "CCTV" in old_group:
            return "高清|央视" if is_hd else "标清|央视"
        elif "卫视" in old_group:
            return "高清|卫视" if is_hd else "标清|卫视"
        elif "北京" in old_group or "BRTV" in old_group or "BTV" in old_group:
            return "高清|北京" if is_hd else "标清|北京"
        elif "IPTV" in old_group:
            return "高清|IPTV" if is_hd else "标清|IPTV"
        elif "少儿" in old_group:
            return "少儿"

        # 默认返回
        return "高清|其他" if is_hd else "标清|其他"

    def fetch_new_list(self, local_file: Optional[str] = None) -> str:
        """获取新列表内容，优先从网络获取，失败时可使用本地文件"""
        # 首先尝试从网络获取
        if local_file is None:
            print(f"正在获取新列表: {self.NEW_LIST_URL}")

            try:
                # 创建SSL上下文，忽略证书验证
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                req = urllib.request.Request(
                    self.NEW_LIST_URL,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )

                with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                    content = response.read().decode('utf-8')
                    print(f"  获取成功，内容长度: {len(content)} 字符")
                    return content
            except Exception as e:
                print(f"  网络获取失败: {e}")
                print(f"  请手动下载列表保存为本地文件，或使用 --local 参数指定本地文件")
                raise
        else:
            # 从本地文件读取
            print(f"正在从本地文件读取: {local_file}")
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  读取成功，内容长度: {len(content)} 字符")
            return content

    def parse_new_list(self, content: str) -> None:
        """解析新列表"""
        print("正在解析新列表...")

        # 解析 #EXTINF:-1,频道名称\nrtp://...
        pattern = r'#EXTINF:-1,([^\n]*)\n(rtp://[^\n]+)'
        matches = re.findall(pattern, content)

        temp_channels: Dict[str, Channel] = {}
        duplicates: Dict[str, List[str]] = defaultdict(list)

        for name, rtp_url in matches:
            # 提取rtp地址
            rtp_match = re.search(r'239\.3\.1\.\d+:\d+', rtp_url)
            if not rtp_match:
                continue

            rtp_address = rtp_match.group()

            # 清理频道名称
            clean_name = self._clean_channel_name(name)

            # 检查重复
            if rtp_address in temp_channels:
                duplicates[rtp_address].append(clean_name)
                continue

            channel = Channel(rtp_address=rtp_address, name=clean_name)
            temp_channels[rtp_address] = channel

        self.new_channels = list(temp_channels.values())

        # 记录重复
        for rtp, names in duplicates.items():
            all_names = [temp_channels[rtp].name] + names
            self.log_duplicates.append((rtp, all_names))

        print(f"  解析完成，共 {len(self.new_channels)} 个频道")
        print(f"  发现 {len(duplicates)} 个重复地址")

    def _clean_channel_name(self, name: str) -> str:
        """清理频道名称"""
        # 移除问号、多余空格等
        name = name.strip()
        name = re.sub(r'[？\?]+', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name

    def process_channels(self) -> None:
        """处理频道，匹配旧数据，分类，标记新增"""
        print("正在处理频道...")

        for channel in self.new_channels:
            # 检查是否为新增频道
            if channel.rtp_address not in self.old_channels:
                channel.is_new = True

                # 推断频道信息
                self._infer_channel_info(channel)

                # 添加到新增日志
                self.log_new_channels.append(channel)
            else:
                # 复用旧信息
                old_channel = self.old_channels[channel.rtp_address]
                channel.tvg_id = old_channel.tvg_id
                channel.tvg_name = old_channel.tvg_name
                channel.tvg_logo = old_channel.tvg_logo
                channel.display_name = old_channel.display_name

                # 重新分类
                channel.group_title = self._classify_channel(channel)

            # 生成URL
            channel.url = f"http://192.168.100.1:5140/rtp/{channel.rtp_address}"

            self.processed_channels.append(channel)

        # 按分组排序
        self.processed_channels.sort(key=lambda c: (
            self.GROUP_ORDER.get(c.group_title, 99),
            self._get_channel_sort_key(c)
        ))

        print(f"  处理完成，新增频道: {len(self.log_new_channels)} 个")

    def _get_channel_sort_key(self, channel: Channel) -> tuple:
        """获取频道排序key，CCTV频道按数字排序"""
        name = channel.display_name or channel.name
        tvg_name = channel.tvg_name or ""

        # 检查是否为CCTV频道（不含CGTN）
        cctv_match = re.search(r'CCTV[-\s]*(\d+|[\u4e00-\u9fa5]+)', name, re.I)
        if cctv_match and 'CGTN' not in name.upper():
            cctv_num_str = cctv_match.group(1)
            # CCTV1-17 按数字排序
            try:
                cctv_num = int(cctv_num_str)
                # CCTV4主频排在欧洲/美洲版本之前
                if cctv_num == 4:
                    # 检查是否是欧洲或美洲版本
                    if '欧洲' in name or 'EUO' in name.upper():
                        return (0, 4.2, name)  # CCTV4欧洲
                    elif '美洲' in name or 'AME' in name.upper():
                        return (0, 4.3, name)  # CCTV4美洲
                    else:
                        return (0, 4.1, name)  # CCTV4主频
                return (0, cctv_num, name)  # CCTV频道排在最前，按数字排序
            except ValueError:
                # CCTV+中文（如CCTV5+）
                if cctv_num_str in ['五', '5'] or '+' in name:
                    return (0, 5.5, name)  # CCTV5+排在CCTV5和CCTV6之间
                # 其他特殊情况
                return (1, name)

        # CGTN频道单独排序
        if 'CGTN' in name.upper():
            # 提取CGTN后面的语言标识排序
            cgtn_order = {
                '新闻': 1, 'NEWS': 1,
                '记录': 2, 'DOCUMENTARY': 2,
                '西班牙语': 3, 'ESPANOL': 3,
                '法语': 4, 'FRENCH': 4,
                '阿拉伯语': 5, 'ARABIC': 5,
                '俄语': 6, 'RUSSIAN': 6,
            }
            for key, order in cgtn_order.items():
                if key in name.upper():
                    return (2, order, name)
            return (2, 99, name)

        # 其他频道按名称排序
        return (3, name)

    def _infer_channel_info(self, channel: Channel) -> None:
        """推断新频道的信息"""
        name = channel.name

        # 清理名称中的清晰度标识，用于匹配
        base_name = re.sub(r'(高清|标清|4K|超高清|SDR|HDR)', '', name, flags=re.I).strip()

        # 尝试从旧频道中查找相似名称的频道获取信息
        for old_channel in self.old_channels.values():
            old_name = old_channel.tvg_name or old_channel.display_name
            if old_name and (base_name in old_name or old_name in base_name):
                channel.tvg_id = old_channel.tvg_id
                channel.tvg_name = old_channel.tvg_name
                channel.tvg_logo = old_channel.tvg_logo
                break

        # 如果没有匹配到，使用新名称作为tvg-name
        if not channel.tvg_name:
            channel.tvg_name = base_name

        # 设置显示名称
        channel.display_name = name

        # 分类
        channel.group_title = self._classify_channel(channel)

    def _classify_channel(self, channel: Channel) -> str:
        """根据频道名称分类"""
        name = channel.name.upper()
        tvg_name = (channel.tvg_name or "").upper()
        display_name = (channel.display_name or "").upper()

        # 判断清晰度
        is_hd = any(kw in channel.name for kw in ["高清", "HD", "超高清"])
        is_4k = "4K" in channel.name or "超高清" in channel.name
        is_sd = "标清" in channel.name

        if is_4k:
            return "4K"

        # 少儿频道（跨清晰度）
        if any(kw in name or kw in tvg_name for kw in ["少儿", "卡通", "动画", "BABY", "青少", "学生", "卡酷"]):
            return "少儿"

        # IPTV专属频道（优先级高于央视）
        iptv_keywords = ["IPTV", "睛彩", "淘剧场", "淘电影", "淘娱乐", "淘BABY", "淘", "热播剧场", "经典电影", "魅力时尚", "少儿动画", "IPTV戏曲", "IPTV早教"]
        if any(kw.upper() in name or kw.upper() in display_name for kw in iptv_keywords):
            return "高清|IPTV" if is_hd else "标清|IPTV"

        # 央视（不含IPTV前缀的）
        if any(kw in name or kw in tvg_name for kw in ["CCTV", "CGTN"]):
            return "高清|央视" if is_hd else "标清|央视"

        # 区县台（北京各区县，优先级高于北京本地）
        district_keywords = ["朝阳", "密云", "房山", "通州", "延庆", "门头沟", "昌平", "顺义", "大兴", "海淀", "西城", "东城", "丰台", "石景山", "怀柔", "平谷"]
        if any(kw in name for kw in district_keywords):
            return "高清|区县" if is_hd else "标清|区县"

        # 北京本地
        if any(kw in name or kw in tvg_name for kw in ["北京", "BRTV", "BTV"]):
            return "高清|北京" if is_hd else "标清|北京"

        # 卫视
        if "卫视" in name or "卫视" in tvg_name:
            return "高清|卫视" if is_hd else "标清|卫视"

        # 购物频道
        shopping_keywords = ["购物", "聚鲨", "优购物", "家有购物", "时尚购物", "央广购物", "财富天下"]
        if any(kw in name for kw in shopping_keywords):
            return "高清|购物" if is_hd else "标清|购物"

        # 数字/专业频道（兜底）
        return "高清|数字" if is_hd else "标清|数字"

    def generate_m3u8(self) -> str:
        """生成M3U8文件内容"""
        lines = ['#EXTM3U x-tvg-url="http://epg.51zmt.top:8000/e.xml.gz"', '']

        current_group = ""

        for channel in self.processed_channels:
            # 分组标题
            if channel.group_title != current_group:
                current_group = channel.group_title
                lines.append(f"# {current_group}")
                lines.append("")

            # EXTINF行
            extinf_parts = ['#EXTINF:-1']

            if channel.tvg_id:
                extinf_parts.append(f'tvg-id="{channel.tvg_id}"')
            else:
                extinf_parts.append('tvg-id=""')

            if channel.tvg_name:
                extinf_parts.append(f'tvg-name="{channel.tvg_name}"')
            else:
                extinf_parts.append('tvg-name=""')

            if channel.tvg_logo:
                extinf_parts.append(f'tvg-logo="{channel.tvg_logo}"')
            else:
                extinf_parts.append('tvg-logo=""')

            extinf_parts.append(f'group-title="{channel.group_title}"')

            if channel.is_new:
                extinf_parts.append('x-add="true"')

            extinf_line = ' '.join(extinf_parts)

            # 显示名称
            display_name = channel.display_name or channel.name
            extinf_line += f',{display_name}'

            lines.append(extinf_line)
            lines.append(channel.url)
            lines.append("")

        return '\n'.join(lines)

    def save_output(self, content: str) -> None:
        """保存输出文件"""
        print(f"正在保存到: {self.output_path}")

        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  保存完成")

    def test_channel_availability(self, channel: Channel, timeout: int = 3, strict: bool = False) -> Tuple[bool, str]:
        """
        测试单个频道是否可用（是否为空台）
        通过连接udpxy代理测试RTP地址，并实际读取数据验证

        Args:
            channel: 频道对象
            timeout: 超时时间(秒)
            strict: 严格模式 - True时只用GET验证数据，能识别真正的空台；
                           False时GET失败后用HEAD备选，保留可能有效的频道
        """
        url = f"http://{self.PROXY_HOST}:{self.PROXY_PORT}/rtp/{channel.rtp_address}"

        # 第一步：尝试GET请求读取实际数据
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'VLC/3.0.18 LibVLC/3.0.18')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                content_type = response.headers.get('Content-Type', '')

                try:
                    data = response.read(2048)

                    if len(data) == 0:
                        return False, "空台 (无数据)"

                    # 检查 MPEG-TS 同步字节 0x47
                    sync_count = 0
                    for i in range(len(data)):
                        if data[i] == 0x47:
                            if i + 188 <= len(data) and data[i + 188] == 0x47:
                                sync_count += 1

                    if sync_count >= 2:
                        return True, f"OK ({content_type})"
                    elif len(data) < 100:
                        return False, f"空台 (数据不足: {len(data)}字节)"
                    else:
                        if len(data) >= 1024:
                            return True, f"OK ({content_type}, 数据{len(data)}字节)"
                        return False, f"空台 (无有效TS数据)"

                except socket.timeout:
                    if strict:
                        return False, "空台 (读取超时)"
                    return True, "待定 (读取超时，保留)"

        except urllib.error.HTTPError as e:
            if strict:
                # 严格模式：直接判定为空台
                return False, f"空台 (HTTP {e.code})"

            # 宽松模式：尝试HEAD请求作为备选
            if e.code == 503:
                return self._test_with_head(channel, timeout, "GET 503")
            if e.code in [404, 400, 502]:
                return False, f"空台 (HTTP {e.code})"
            return self._test_with_head(channel, timeout, f"GET {e.code}")

        except urllib.error.URLError as e:
            error_msg = str(e.reason)
            if 'Connection refused' in error_msg:
                return False, "连接被拒绝(空台)"
            if 'timed out' in error_msg:
                if strict:
                    return False, "空台 (连接超时)"
                return self._test_with_head(channel, timeout, "GET超时")
            if 'No route to host' in error_msg or 'unreachable' in error_msg:
                return False, "主机不可达"
            return False, f"连接错误: {error_msg[:50]}"

        except socket.timeout:
            if strict:
                return False, "空台 (GET超时)"
            return self._test_with_head(channel, timeout, "GET超时")

        except Exception as e:
            return False, f"错误: {str(e)[:50]}"

    def _test_with_head(self, channel: Channel, timeout: int, reason: str) -> Tuple[bool, str]:
        """
        使用HEAD请求作为备选检测方法（仅在宽松模式下使用）
        当GET请求失败时使用，检查udpxy是否能接受该RTP地址
        """
        url = f"http://{self.PROXY_HOST}:{self.PROXY_PORT}/rtp/{channel.rtp_address}"

        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'VLC/3.0.18 LibVLC/3.0.18')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                content_type = response.headers.get('Content-Type', '')
                # HEAD成功，说明udpxy能接受该地址，保留
                return True, f"OK ({content_type})"

        except urllib.error.HTTPError as e:
            if e.code == 503:
                # HEAD也返回503，可能是网络环境问题，保留
                return True, f"待定 ({reason}->HEAD 503，保留)"
            return False, f"空台 ({reason}->HEAD {e.code})"

        except Exception as e:
            # HEAD失败，保守起见保留
            return True, f"待定 ({reason}->HEAD失败，保留)"

    def filter_unavailable_channels(self, timeout: int = 3, max_workers: int = 20, strict: bool = False) -> List[Channel]:
        """
        批量检测频道可用性，过滤掉空台
        返回可用频道列表

        Args:
            timeout: 超时时间(秒)
            max_workers: 并发数
            strict: 严格模式 - True时能识别真正的空台，False时保留可能有效的频道
        """
        print(f"\n开始检测频道可用性...")
        print(f"代理: http://{self.PROXY_HOST}:{self.PROXY_PORT}")
        print(f"超时: {timeout}秒, 并发: {max_workers}, 严格模式: {strict}")
        print("-" * 60)

        available_channels = []
        unavailable_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有检测任务
            future_to_channel = {
                executor.submit(self.test_channel_availability, ch, timeout, strict): ch
                for ch in self.processed_channels
            }

            # 处理结果
            completed = 0
            total = len(self.processed_channels)

            for future in as_completed(future_to_channel):
                channel = future_to_channel[future]
                completed += 1

                try:
                    is_available, message = future.result()
                    channel.is_available = is_available
                    channel.test_message = message

                    status = "✓" if is_available else "✗"
                    print(f"[{completed}/{total}] {channel.display_name or channel.name:25s} {status} {message}")

                    if is_available:
                        available_channels.append(channel)
                    else:
                        unavailable_count += 1

                except Exception as e:
                    print(f"[{completed}/{total}] {channel.display_name or channel.name:25s} ✗ 检测异常: {e}")
                    channel.is_available = False
                    channel.test_message = f"检测异常: {e}"
                    unavailable_count += 1

        print("-" * 60)
        print(f"检测完成: 可用 {len(available_channels)} 个, 空台 {unavailable_count} 个")

        return available_channels

    def print_log(self) -> None:
        """打印处理日志"""
        print("\n" + "=" * 60)
        print("处理日志")
        print("=" * 60)

        # 新增频道
        print(f"\n【新增频道】共 {len(self.log_new_channels)} 个")
        for ch in self.log_new_channels:
            print(f"  - {ch.name} ({ch.rtp_address}) -> {ch.group_title}")

        # 重复频道
        print(f"\n【重复频道】共 {len(self.log_duplicates)} 个地址重复")
        for rtp, names in self.log_duplicates:
            print(f"  - {rtp}: {', '.join(names)}")

        # 兜底分组
        fallback = [ch for ch in self.processed_channels if "其他" in ch.group_title]
        print(f"\n【兜底分组】共 {len(fallback)} 个频道使用兜底分组")
        for ch in fallback:
            print(f"  - {ch.name} -> {ch.group_title}")

        print("\n" + "=" * 60)

    def run(self, local_file: Optional[str] = None, test_channels: bool = False,
            test_timeout: int = 3, test_workers: int = 20, strict: bool = False) -> None:
        """运行更新流程"""
        print("=" * 60)
        print("IPTV频道列表更新")
        print("=" * 60 + "\n")

        # 1. 解析旧文件
        self.parse_old_file()

        # 2. 获取并解析新列表
        new_content = self.fetch_new_list(local_file)
        self.parse_new_list(new_content)

        # 3. 处理频道
        self.process_channels()

        # 4. 检测频道可用性（可选）
        if test_channels:
            self.processed_channels = self.filter_unavailable_channels(
                timeout=test_timeout, max_workers=test_workers, strict=strict
            )
            if not self.processed_channels:
                print("\n警告: 没有可用频道！请检查网络连接和代理配置。")
                return

        # 5. 生成M3U8
        m3u8_content = self.generate_m3u8()

        # 6. 保存输出
        self.save_output(m3u8_content)

        # 7. 打印日志
        self.print_log()

        print(f"\n处理完成！输出文件: {self.output_path}")


def main():
    """主函数"""
    import argparse

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='IPTV频道列表更新工具')
    parser.add_argument('--local', '-l', type=str, help='本地新列表文件路径')
    parser.add_argument('--old', '-o', type=str, default=os.path.join(project_root, "iptv.bj.m3u8"),
                        help='旧列表文件路径（默认: iptv.bj.m3u8）')
    parser.add_argument('--output', '-O', type=str, default=os.path.join(project_root, "iptv.bj.m3u8.new"),
                        help='输出文件路径（默认: iptv.bj.m3u8.new）')

    # 频道可用性检测参数
    parser.add_argument('--test', '-t', action='store_true',
                        help='检测频道可用性，自动过滤空台')
    parser.add_argument('--test-timeout', type=int, default=3,
                        help='检测超时时间(秒)，默认3秒')
    parser.add_argument('--test-workers', type=int, default=20,
                        help='检测并发数，默认20')
    parser.add_argument('--strict', '-s', action='store_true',
                        help='严格模式：只用GET验证数据，能识别真正的空台（需在组播源环境中运行）')
    parser.add_argument('--proxy-host', type=str, default='192.168.100.1',
                        help='udpxy代理地址，默认192.168.100.1')
    parser.add_argument('--proxy-port', type=int, default=5140,
                        help='udpxy代理端口，默认5140')

    args = parser.parse_args()

    # 创建更新器
    updater = IPTVUpdater(args.old, args.output)

    # 更新代理配置
    updater.PROXY_HOST = args.proxy_host
    updater.PROXY_PORT = args.proxy_port

    # 运行更新
    updater.run(
        local_file=args.local,
        test_channels=args.test,
        test_timeout=args.test_timeout,
        test_workers=args.test_workers,
        strict=args.strict
    )


if __name__ == "__main__":
    main()
