#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全性检查脚本
用于检查代码中是否包含敏感信息
"""

import os
import re
from pathlib import Path


def check_file_for_secrets(filepath: Path) -> list:
    """检查文件中是否包含敏感信息"""
    secrets = []

    # 跳过文档文件的检查（因为文档中可能有示例代码）
    if filepath.suffix in ['.md', '.txt']:
        return secrets

    sensitive_patterns = [
        r'no-mad-world',  # ikuuu 域名
        r'dpdns',  # 动态域名
        r'[a-f0-9]{32}',  # UUID
        r'clash=3&extend=1',  # 订阅链接特征
    ]

    if not filepath.exists():
        return secrets

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in sensitive_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        secrets.append(f"{filepath.name}:{i}: {line.strip()[:100]}")
    except Exception as e:
        print(f"无法读取文件 {filepath}: {e}")

    return secrets


def main():
    """主函数"""
    print("=" * 60)
    print("安全性检查")
    print("=" * 60)

    # 定义要检查的文件
    safe_files = [
        'merge.py',
        'requirements.txt',
        '需求文档.md',
        '.gitignore',
        '.env.example',
    ]

    sensitive_files = [
        '.env',
        'merged.yaml',
    ]

    all_secrets = []

    # 检查安全文件（不应该包含敏感信息）
    print("\n检查安全文件（不应该包含敏感信息）:")
    for filename in safe_files:
        filepath = Path(filename)
        if filepath.exists():
            secrets = check_file_for_secrets(filepath)
            if secrets:
                print(f"  ❌ {filename} 发现敏感信息:")
                all_secrets.extend(secrets)
                for secret in secrets[:3]:  # 只显示前3个
                    print(f"     - {secret}")
            else:
                print(f"  ✅ {filename} 检查通过")

    # 检查敏感文件（应该被忽略）
    print("\n检查敏感文件（应该被 Git 忽略）:")
    gitignore_path = Path('.gitignore')
    ignored_files = []

    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        for filename in sensitive_files:
            filepath = Path(filename)
            if filepath.exists():
                # 检查是否被忽略
                is_ignored = False
                for pattern in ignore_patterns:
                    if pattern.replace('*', '') in str(filepath.name):
                        is_ignored = True
                        break

                if is_ignored:
                    print(f"  ✅ {filename} 已被 .gitignore 忽略")
                    ignored_files.append(filename)
                else:
                    print(f"  ⚠️  {filename} 可能未被忽略")

    # 总结
    print("\n" + "=" * 60)
    print("检查总结:")
    print("=" * 60)

    if all_secrets:
        print(f"❌ 发现 {len(all_secrets)} 处敏感信息！")
        print("   请立即修复后再提交代码！")
        return 1
    else:
        print("✅ 未在安全文件中发现敏感信息")

    if len(ignored_files) == len(sensitive_files):
        print(f"✅ 所有敏感文件 ({len(sensitive_files)} 个) 均已被忽略")
    else:
        print(f"⚠️  部分敏感文件未被忽略")

    print("\n可以安全提交的文件:")
    for filename in safe_files:
        if Path(filename).exists():
            print(f"  - {filename}")

    print("\n不应该提交的文件:")
    for filename in sensitive_files:
        if Path(filename).exists():
            print(f"  - {filename}")

    return 0


if __name__ == '__main__':
    exit(main())
