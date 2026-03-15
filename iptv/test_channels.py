#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测IPTV频道是否可用
测试 rtp 地址是否能正常返回数据
"""

import socket
import urllib.request
import urllib.error
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict


class ChannelTester:
    """频道可用性检测器"""

    def __init__(self, timeout: int = 5, proxy_host: str = "192.168.100.1", proxy_port: int = 5140, strict: bool = False):
        self.timeout = timeout
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.strict = strict

    def test_http_url(self, url: str) -> Tuple[bool, str]:
        """
        测试HTTP URL是否可用
        通过实际读取数据并验证是否包含有效的MPEG-TS流来判断
        """
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'VLC/3.0.18 LibVLC/3.0.18')

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content_type = response.headers.get('Content-Type', '')

                # 实际读取数据验证是否为有效的视频流
                # MPEG-TS 流的同步字节是 0x47，每 188 字节出现一次
                try:
                    data = response.read(2048)  # 读取前 2KB 数据

                    if len(data) == 0:
                        return False, "空台 (无数据)"

                    # 检查是否包含 MPEG-TS 同步字节 0x47
                    # 有效的 TS 流应该有多个同步字节
                    sync_count = 0
                    for i in range(len(data)):
                        if data[i] == 0x47:
                            # 检查是否在 188 字节边界上
                            if i + 188 <= len(data) and data[i + 188] == 0x47:
                                sync_count += 1

                    if sync_count >= 2:
                        return True, f"OK ({content_type})"
                    elif len(data) < 100:
                        # 数据太少，可能是空台
                        return False, f"空台 (数据不足: {len(data)}字节)"
                    else:
                        # 有数据但没有找到 TS 同步字节，可能是其他格式或有噪声
                        # 如果数据量足够大，仍然认为可能可用
                        if len(data) >= 1024:
                            return True, f"OK ({content_type}, 数据{len(data)}字节)"
                        return False, f"空台 (无有效TS数据)"

                except socket.timeout:
                    if self.strict:
                        return False, "空台 (读取超时)"
                    return True, "待定 (读取超时，保留)"

        except urllib.error.HTTPError as e:
            if self.strict:
                return False, f"空台 (HTTP {e.code})"
            # 宽松模式：HEAD备选
            return self._test_with_head(url, f"GET {e.code}")

        except urllib.error.URLError as e:
            error_msg = str(e.reason)

            if 'Connection refused' in error_msg:
                return False, "连接被拒绝(空台)"

            if 'timed out' in error_msg:
                if self.strict:
                    return False, "空台 (连接超时)"
                return self._test_with_head(url, "GET超时")

            if 'No route to host' in error_msg or 'unreachable' in error_msg:
                return False, "主机不可达"

            return False, f"连接错误: {error_msg[:50]}"

        except socket.timeout:
            if self.strict:
                return False, "空台 (GET超时)"
            return self._test_with_head(url, "GET超时")

        except Exception as e:
            return False, f"错误: {str(e)[:50]}"

    def _test_with_head(self, url: str, reason: str) -> Tuple[bool, str]:
        """使用HEAD请求作为备选检测方法（仅在宽松模式下使用）"""
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'VLC/3.0.18 LibVLC/3.0.18')

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content_type = response.headers.get('Content-Type', '')
                return True, f"OK ({content_type})"

        except urllib.error.HTTPError as e:
            if e.code == 503:
                return True, f"待定 ({reason}->HEAD 503，保留)"
            return False, f"空台 ({reason}->HEAD {e.code})"

        except Exception as e:
            return True, f"待定 ({reason}->HEAD失败，保留)"

    def test_rtp_url(self, rtp_address: str) -> Tuple[bool, str]:
        """
        测试RTP地址是否可用
        通过udpxy代理转换为HTTP进行测试
        """
        url = f"http://{self.proxy_host}:{self.proxy_port}/rtp/{rtp_address}"
        return self.test_http_url(url)

    def parse_m3u8(self, filepath: str) -> List[Tuple[str, str, str]]:
        """
        解析M3U8文件，返回 (频道名称, rtp地址, 完整URL) 列表
        """
        channels = []

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('#EXTINF:'):
                # 提取频道名称
                name_match = re.search(r',(.+)$', line)
                channel_name = name_match.group(1) if name_match else "未知频道"

                # 下一行是URL
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()

                    # 提取rtp地址
                    rtp_match = re.search(r'239\.3\.1\.\d+:\d+', url_line)
                    if rtp_match:
                        rtp_address = rtp_match.group()
                        channels.append((channel_name, rtp_address, url_line))

                i += 2
            else:
                i += 1

        return channels

    def test_channels(self, channels: List[Tuple[str, str, str]], max_workers: int = 10) -> Dict[str, List]:
        """
        批量测试频道，返回分类结果
        """
        results = {
            'available': [],      # 可用频道
            'unavailable': [],    # 不可用（空台）
            'timeout': [],        # 超时
            'error': []           # 其他错误
        }

        print(f"开始测试 {len(channels)} 个频道...")
        print(f"使用代理: http://{self.proxy_host}:{self.proxy_port}")
        print("-" * 60)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_channel = {
                executor.submit(self.test_rtp_url, ch[1]): ch
                for ch in channels
            }

            # 处理结果
            completed = 0
            for future in as_completed(future_to_channel):
                channel = future_to_channel[future]
                channel_name, rtp_address, url = channel
                completed += 1

                try:
                    is_available, message = future.result()

                    status = "✓ 可用" if is_available else "✗ 不可用"
                    print(f"[{completed}/{len(channels)}] {channel_name[:20]:20s} - {status}: {message}")

                    if is_available:
                        results['available'].append(channel)
                    elif '超时' in message or '超时' in message:
                        results['timeout'].append((channel, message))
                    elif '拒绝' in message or '空台' in message:
                        results['unavailable'].append((channel, message))
                    else:
                        results['error'].append((channel, message))

                except Exception as e:
                    print(f"[{completed}/{len(channels)}] {channel_name[:20]:20s} - 测试异常: {e}")
                    results['error'].append((channel, str(e)))

        print("-" * 60)
        return results

    def generate_filtered_m3u8(self, original_file: str, output_file: str, available_channels: List) -> None:
        """
        根据可用频道生成过滤后的M3U8文件
        """
        # 读取原始文件内容
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取可用频道的rtp地址集合
        available_rtps = {ch[1] for ch in available_channels}

        # 解析并过滤
        lines = content.split('\n')
        filtered_lines = [lines[0]]  # 保留头部 #EXTM3U

        i = 1
        while i < len(lines):
            line = lines[i]

            if line.startswith('#EXTINF:'):
                # 检查下一行的URL是否在可用列表中
                if i + 1 < len(lines):
                    url_line = lines[i + 1]
                    rtp_match = re.search(r'239\.3\.1\.\d+:\d+', url_line)

                    if rtp_match and rtp_match.group() in available_rtps:
                        # 保留这个频道
                        filtered_lines.append(line)
                        filtered_lines.append(url_line)
                    else:
                        # 注释掉不可用的频道
                        filtered_lines.append(f"# [不可用] {line}")
                        filtered_lines.append(f"# {url_line}")

                i += 2
            elif line.strip():
                filtered_lines.append(line)
                i += 1
            else:
                i += 1

        # 保存过滤后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered_lines))

        print(f"\n已生成过滤后的文件: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='检测IPTV频道可用性')
    parser.add_argument('input', type=str, help='输入的M3U8文件路径')
    parser.add_argument('--output', '-o', type=str, help='输出的过滤后文件路径')
    parser.add_argument('--timeout', '-t', type=int, default=5, help='超时时间(秒)，默认5秒')
    parser.add_argument('--proxy-host', type=str, default='192.168.100.1', help='udpxy代理地址')
    parser.add_argument('--proxy-port', type=int, default=5140, help='udpxy代理端口')
    parser.add_argument('--workers', '-w', type=int, default=10, help='并发测试数，默认10')
    parser.add_argument('--strict', '-s', action='store_true',
                        help='严格模式：只用GET验证数据，能识别真正的空台（需在组播源环境中运行）')
    args = parser.parse_args()

    # 创建测试器
    tester = ChannelTester(
        timeout=args.timeout,
        proxy_host=args.proxy_host,
        proxy_port=args.proxy_port,
        strict=args.strict
    )

    # 解析频道列表
    channels = tester.parse_m3u8(args.input)
    print(f"共解析到 {len(channels)} 个频道\n")

    # 测试频道
    results = tester.test_channels(channels, max_workers=args.workers)

    # 打印统计
    print("\n" + "=" * 60)
    print("测试结果统计")
    print("=" * 60)
    print(f"可用频道:     {len(results['available'])} 个")
    print(f"不可用(空台): {len(results['unavailable'])} 个")
    print(f"超时:         {len(results['timeout'])} 个")
    print(f"其他错误:     {len(results['error'])} 个")
    print("=" * 60)

    # 输出不可用的频道列表
    if results['unavailable']:
        print("\n【不可用频道列表】")
        for (name, rtp, url), msg in results['unavailable']:
            print(f"  - {name} ({rtp}): {msg}")

    # 生成过滤后的文件
    if args.output:
        tester.generate_filtered_m3u8(args.input, args.output, results['available'])


if __name__ == "__main__":
    main()
