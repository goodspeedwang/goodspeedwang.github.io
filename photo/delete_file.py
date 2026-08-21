#!/usr/bin/env python3
"""
删除媒体文件工具
用法: python3 delete_file.py <文件名关键字>
示例: python3 delete_file.py "_1_Yolanda颖颖吖"

从 girl.json 中搜索匹配的文件，确认后删除。
"""

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "girl.json")


def collect_files_from_json(node, parent_path=""):
    """递归遍历 JSON 树，收集所有文件路径"""
    results = []
    source_dir = node.get("sourceDir", "")

    def walk(n, rel_path):
        # 当前节点的图片
        for img in n.get("images", []):
            img_rel = os.path.join(rel_path, img["url"]) if rel_path else img["url"]
            results.append((img["name"], img_rel))

        # 递归子文件夹
        for folder in n.get("folders", []):
            sub_path = os.path.join(rel_path, folder["url"]) if rel_path else folder["url"]
            walk(folder, sub_path)

    # 顶层 sourceDir 用于构建完整路径
    walk(node, "")
    return results, source_dir


def remove_image_from_json(node, filename):
    """从 JSON 树中删除所有指定文件名的图片记录，返回删除总数"""
    removed = 0

    # 从当前节点 images 中查找并删除所有同名记录
    kept = []
    for img in node.get("images", []):
        if img["name"] == filename:
            removed += 1
        else:
            kept.append(img)
    node["images"] = kept

    # 递归子文件夹
    for folder in node.get("folders", []):
        removed += remove_image_from_json(folder, filename)

    return removed


def parse_selection(text, max_count):
    """解析用户输入的多个序号选择，支持 '1 3 5'、'1,3,5'、'1-4' 等格式，返回去重后的 0 基索引列表"""
    selected = set()
    for part in text.replace(',', ' ').split():
        part = part.strip()
        if '-' in part:
            try:
                start_s, end_s = part.split('-', 1)
                start, end = int(start_s), int(end_s)
                if start > end:
                    start, end = end, start
                for n in range(start, end + 1):
                    if 1 <= n <= max_count:
                        selected.add(n - 1)
            except ValueError:
                continue
        else:
            try:
                n = int(part)
                if 1 <= n <= max_count:
                    selected.add(n - 1)
            except ValueError:
                continue
    return sorted(selected)


def update_stats(node):
    """递归更新 _stats 统计信息"""
    total_media = len(node.get("images", []))
    total_folders = len(node.get("folders", []))

    for folder in node.get("folders", []):
        sub_media, sub_folders = update_stats(folder)
        total_media += sub_media
        total_folders += sub_folders

    if "_stats" in node:
        node["_stats"]["totalMedia"] = total_media
        node["_stats"]["totalFolders"] = total_folders

    return total_media, total_folders


def main():
    if len(sys.argv) < 2:
        print("用法: python3 delete_file.py <文件名关键字>")
        print('示例: python3 delete_file.py "_1_Yolanda颖颖吖"')
        sys.exit(1)

    keyword = sys.argv[1]

    if not os.path.isfile(JSON_FILE):
        print(f"错误: 未找到 {JSON_FILE}")
        print("请先运行 python3 generate_info.py 生成数据")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    source_dir = data.get("sourceDir", "")
    if not source_dir:
        print("错误: girl.json 中未找到 sourceDir")
        sys.exit(1)

    all_files, _ = collect_files_from_json(data)
    matches = [(name, rel) for name, rel in all_files if keyword in name]

    print(f"搜索关键字: {keyword}")
    print(f"数据源: {JSON_FILE}")
    print()

    if not matches:
        print("未找到匹配的文件")
        sys.exit(0)

    # 构建完整路径
    results = []
    for name, rel in matches:
        full_path = os.path.join(source_dir, rel)
        results.append((name, full_path))

    if len(results) > 1:
        print(f"找到 {len(results)} 个匹配文件:")
        for i, (name, path) in enumerate(results, 1):
            size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.isfile(path) else 0
            print(f"  [{i}] {path}  ({size_mb:.1f} MB)")
        print()
        print("可一次性删除多个: 输入序号用空格/逗号分隔，如 '1 3 5' 或 '1-4'")
        print("输入 'all' 删除全部，输入 '0' 或留空取消")
        try:
            choice = input("请选择: ").strip()
        except EOFError:
            choice = ''

        if not choice or choice == '0':
            print("已取消")
            sys.exit(0)

        if choice.lower() == 'all':
            selected = list(range(len(results)))
        else:
            selected = parse_selection(choice, len(results))
            if not selected:
                print("无效的选择")
                sys.exit(1)
    else:
        selected = [0]

    total_size = 0
    existing = []
    missing = []
    for idx in selected:
        name, path = results[idx]
        if os.path.isfile(path):
            total_size += os.path.getsize(path)
            existing.append((idx, name, path))
        else:
            missing.append((idx, name, path))

    if missing:
        print("\n以下文件不存在，将被跳过:")
        for idx, name, path in missing:
            print(f"  [{idx + 1}] {path}")

    if not existing:
        print("没有可删除的文件")
        sys.exit(0)

    print(f"\n将删除 {len(existing)} 个文件，共 {total_size / (1024 * 1024):.1f} MB:")
    for idx, name, path in existing:
        print(f"  [{idx + 1}] {path}")

    try:
        confirm = input("确认删除? (y/N): ").strip().lower()
    except EOFError:
        confirm = ''

    if confirm == 'y':
        removed_records = 0
        deleted_files = 0
        for idx, name, path in existing:
            try:
                os.remove(path)
                deleted_files += 1
            except OSError as e:
                print(f"删除失败: {path} ({e})")
                continue
            # 从 JSON 中移除所有同名记录
            removed_records += remove_image_from_json(data, name)

        if removed_records > 0:
            update_stats(data)
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"已删除 {deleted_files} 个文件，从 JSON 移除 {removed_records} 条记录")
    else:
        print("已取消")


if __name__ == '__main__':
    main()
