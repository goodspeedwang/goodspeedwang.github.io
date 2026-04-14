#!/usr/bin/env python3
"""
遍历指定目录，生成 JS 数据文件供 photo.html 以 file:// 协议直接引用。
输出数据结构兼容 extractItems() 的返回格式: { images: [...], folders: [...] }
每个文件夹节点携带 mtime 用于增量缓存。
支持多源目录，生成多个 JS 文件。

用法:
    python3 generate_info.py

配置: config.env 中定义 SOURCE_DIRS 列表
"""

import os
import sys
import json
import time

# 实时输出，禁用缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.env")

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.tiff',
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
}

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}


def load_config():
    """从 config.env 加载配置"""
    config = {}
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip().strip('"').strip("'")
    return config


def parse_source_dirs(config_raw):
    """
    解析源目录列表。
    支持格式：
      - 单行单路径:  SOURCE_DIRS=/path/to/dir
      - 多行多路径:  每行一个路径
      - JSON数组:   SOURCE_DIRS=["/path1", "/path2"]
    返回 [(name, output_js), ...] 列表
    """
    raw = config_raw.get('SOURCE_DIRS', '')
    if not raw:
        return []

    # 尝试 JSON 数组格式
    if raw.startswith('['):
        try:
            paths = json.loads(raw)
            return [make_source_entry(p) for p in paths if p]
        except json.JSONDecodeError:
            pass

    # 逗号分隔或换行分隔
    for sep in [',', '\n']:
        if sep in raw and sep != '\n' or (sep == '\n' and '\n' in raw):
            paths = [p.strip().strip('"').strip("'") for p in raw.split(sep) if p.strip()]
            entries = [make_source_entry(p) for p in paths if p]
            break
    else:
        entries = [make_source_entry(raw)] if raw else []

    # 去重（按输出文件名）
    seen = set()
    unique = []
    for e in entries:
        if e[1] not in seen:
            seen.add(e[1])
            unique.append(e)
    return unique


def make_source_entry(path):
    """从路径推导 (name, output_js)"""
    dir_name = os.path.basename(os.path.normpath(path))
    js_name = f"{dir_name.lower()}.js"
    return (path, js_name)


# ====== 配置 ======
config = load_config()
SOURCE_ENTRIES = parse_source_dirs(config)

if not SOURCE_ENTRIES:
    print("错误: 未在 config.env 中找到 SOURCE_DIRS 配置")
    sys.exit(1)


# ========== 树构建 ==========

def scan_dir(dirpath):
    """用 os.scandir 扫描目录，返回 (dirs, files)"""
    dirs = []
    files = []
    try:
        with os.scandir(dirpath) as entries:
            for entry in sorted(entries, key=lambda e: e.name):
                name = entry.name
                if name.startswith('.') or name.startswith('._'):
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        dirs.append(name)
                        continue
                    elif not entry.is_file(follow_symlinks=False):
                        continue
                except OSError:
                    continue

                ext = os.path.splitext(name)[1].lower()
                if ext in MEDIA_EXTENSIONS:
                    files.append(name)
    except PermissionError:
        print(f"  [跳过无权限] {dirpath}")
    except OSError:
        print(f"  [读取失败] {dirpath}")

    return dirs, files


def build_tree(dirpath, rel_path="", cache=None):
    """
    递归构建目录树。
    缓存命中时复用 images[]，仍逐层递归确保深层变更不被遗漏。
    """
    display_path = rel_path or os.path.basename(dirpath)

    try:
        current_mtime = os.stat(dirpath).st_mtime
    except OSError:
        current_mtime = 0

    old_node = find_cached_node(cache, rel_path) if cache else None

    if old_node and old_node.get('mtime') == current_mtime:
        images = old_node.get('images', [])
        cached_folders = old_node.get('folders', [])
        folder_names = [f['name'] for f in cached_folders]

        folders = []
        for d in folder_names:
            dir_full = os.path.join(dirpath, d)
            sub_rel = os.path.join(rel_path, d) if rel_path else d
            dir_url = (rel_path + '/' + d) if rel_path else d
            child_data = build_tree(dir_full, sub_rel, cache=cache)
            folders.append({"name": d, "url": dir_url, **child_data})

        result = {"images": images, "folders": folders, "mtime": current_mtime}
        _print_stats(display_path, images, folder_names, True)
        return result

    else:
        dirs, files = scan_dir(dirpath)

        rel_prefix = rel_path + '/' if rel_path else ''
        images = [{"name": f, "url": rel_prefix + f} for f in files]

        folders = []
        for d in dirs:
            dir_full = os.path.join(dirpath, d)
            sub_rel = os.path.join(rel_path, d) if rel_path else d
            dir_url = rel_prefix + d
            child_data = build_tree(dir_full, sub_rel, cache=cache)
            folders.append({"name": d, "url": dir_url, **child_data})

        result = {"images": images, "folders": folders, "mtime": current_mtime}
        _print_stats(display_path, images, dirs, False)
        return result


def _print_stats(display_path, images, folder_list, is_cache_hit):
    """打印扫描结果统计"""
    img_count = len(images)
    vid_count = sum(1 for i in images
                    if os.path.splitext(i["name"])[1].lower() in VIDEO_EXTENSIONS)
    pic_count = img_count - vid_count
    parts = []
    if pic_count > 0:
        parts.append(f"{pic_count} 图")
    if vid_count > 0:
        parts.append(f"{vid_count} 视频")
    if len(folder_list) > 0:
        parts.append(f"{len(folder_list)} 子目录")
    status = "[cache]" if is_cache_hit else ""
    print(f"  {'[cache]' if is_cache_hit else '  扫描'}: {display_path}/  -> {', '.join(parts)}  {status}".rstrip(), flush=True)


def find_cached_node(cache, rel_path):
    """在旧树中按路径找到对应节点"""
    if cache is None:
        return None
    parts = rel_path.split('/') if rel_path else []
    node = cache
    for p in parts:
        found = False
        for sub in node.get('folders', []):
            if sub.get('name') == p:
                node = sub
                found = True
                break
        if not found:
            return None
    return node


# ========== 缓存读写 ==========

def load_tree_cache(output_file):
    """从 JS 文件的 GALLERY_DATA 中读取带 mtime 的树结构作为缓存"""
    if not os.path.isfile(output_file):
        return None
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        start_marker = 'const GALLERY_DATA = '
        idx = content.find(start_marker)
        if idx < 0:
            return None
        idx += len(start_marker)
        depth = 0
        i = idx
        while i < len(content):
            ch = content[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(content[idx:i + 1])
            i += 1
    except (json.JSONDecodeError, OSError):
        pass
    return None


# ========== 统计 ==========

def count_items(data):
    img_count = len(data["images"])
    folder_count = len(data["folders"])
    total_folders = folder_count
    for f in data["folders"]:
        sub_img, sub_folder = count_items(f)
        img_count += sub_img
        total_folders += sub_folder
    return img_count, total_folders


def collect_all_names(node):
    """收集一棵树下所有文件夹路径和文件名，用于对比"""
    folders = set()
    files = set()

    def walk(n, prefix=""):
        for f in n.get('folders', []):
            fpath = prefix + "/" + f['name'] if prefix else f['name']
            folders.add(fpath)
            walk(f, fpath)
        for img in n.get('images', []):
            fpath = prefix + "/" + img['name'] if prefix else img['name']
            files.add(fpath)

    walk(node)
    return folders, files


# ========== 主流程 ==========

def process_one(source_dir, output_js):
    """处理单个源目录：加载缓存 -> 构建树 -> 对比变化 -> 写入文件"""
    output_path = os.path.join(SCRIPT_DIR, output_js)

    if not os.path.isdir(source_dir):
        print(f"跳过: 源目录不存在: {source_dir}")
        return None, None, None

    tree_cache = load_tree_cache(output_path)

    t0 = time.time()
    tree = build_tree(source_dir, cache=tree_cache)
    elapsed = time.time() - t0

    total_imgs, total_folders = count_items(tree)

    # 变化对比
    change_str = ""
    if tree_cache is not None:
        old_folders, old_files = collect_all_names(tree_cache)
        new_folders, new_files = collect_all_names(tree)
        changes = []
        added_folders = new_folders - old_folders
        removed_folders = old_folders - new_folders
        added_files = new_files - old_files
        removed_files = old_files - new_files
        if added_folders:
            changes.append(f"+{len(added_folders)} 文件夹")
        if removed_folders:
            changes.append(f"-{len(removed_folders)} 文件夹")
        if added_files:
            changes.append(f"+{len(added_files)} 文件")
        if removed_files:
            changes.append(f"-{len(removed_files)} 文件")
        if not changes:
            changes.append("无变化")
        change_str = ", ".join(changes)

    # 写入 JS 文件
    js_content = f"""// Auto-generated by generate_info.py
// Source: {source_dir}
// Folders: {total_folders}, Media files: {total_imgs}

const GALLERY_DATA = {{
  "sourceDir": "{source_dir}",
  "images": {json.dumps(tree.get('images', []), ensure_ascii=False)},
  "folders": {json.dumps(tree.get('folders', []), ensure_ascii=False)},
  "mtime": {tree.get('mtime', 0)}
}};
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    return total_folders, total_imgs, change_str, elapsed, output_path


def main():
    grand_start = time.time()

    for i, (source_dir, output_js) in enumerate(SOURCE_ENTRIES):
        label = f"[{i + 1}/{len(SOURCE_ENTRIES)}] "
        print(f"\n{'='*50}")
        print(f"{label}处理: {os.path.basename(source_dir)} -> {output_js}")
        print(f"{'='*50}")

        result = process_one(source_dir, output_js)
        if result is None:
            continue

        total_folders, total_imgs, change_str, elapsed, output_path = result

        base_msg = f"  文件夹: {total_folders}, 图片/视频: {total_imgs}"
        if change_str:
            print(f"{base_msg}  |  {change_str}")
        else:
            print(base_msg)
        print(f"  已生成: {output_path}")
        print(f"  耗时: {elapsed:.2f} 秒")

    total_elapsed = time.time() - grand_start
    print(f"\n全部完成，总耗时: {total_elapsed:.2f} 秒")


if __name__ == '__main__':
    main()
