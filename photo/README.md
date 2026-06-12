# Photo Gallery

基于 Python 后端 + 纯前端的单页相册/视频浏览器，支持目录树导航、图片分组、随机排序、全屏查看等功能。

## 项目架构

```
photo/
├── photo.html            # 前端单页应用（Gallery UI）
├── server.py             # Python HTTP 服务器（后端）
├── generate_info.py       # 目录扫描 & JSON 数据生成脚本
├── config.env             # 源目录配置（不提交 git）
├── start-photo-server.sh  # 一键启动脚本
├── girl.json              # 生成的目录数据
└── README.md
```

## 工作流程

```
1. 配置源目录         config.env → SOURCE_DIRS
2. 扫描生成数据       generate_info.py → girl.json
3. 启动服务器         server.py [port] [media_dir]
4. 浏览器访问         http://localhost:8080/photo.html
```

---

## 模块详细说明

### 1. `generate_info.py` — 数据生成器

遍历指定源目录，生成 JSON 数据文件供后端加载。

**功能：**
- 递归扫描目录，收集图片/视频文件
- 按 `mtime` 增量缓存：目录未变更时复用旧数据
- 对比新旧数据，输出变化统计（新增/删除的文件夹和文件）
- 支持多源目录，每个源生成独立 JSON 文件

**用法：**
```bash
python3 generate_info.py
```

**配置：** 在 `config.env` 中设置 `SOURCE_DIRS`：
```env
# 逗号分隔
SOURCE_DIRS="/path/to/dir1,/path/to/dir2"

# 或 JSON 数组
SOURCE_DIRS=["/path1", "/path2"]
```

**输出 JSON 结构：**
```json
{
  "sourceDir": "/原始/源/目录",
  "images": [{ "name": "file.jpg", "url": "file.jpg" }],
  "folders": [
    {
      "name": "子目录名",
      "url": "子目录名",
      "images": [...],
      "folders": [...],
      "mtime": 1234567890.0
    }
  ],
  "mtime": 1234567890.0,
  "_stats": {
    "totalFolders": 42,
    "totalMedia": 1024
  }
}
```

**JSON 文件命名规则：** 取源目录最后一级目录名转小写，如 `/Photo/girl` → `girl.json`。当前仅配置了 `girl` 源目录。

**支持的媒体格式：**
- 图片：`.jpg` `.jpeg` `.png` `.gif` `.webp` `.bmp` `.heic` `.tiff`
- 视频：`.mp4` `.mov` `.avi` `.mkv` `.webm` `.m4v`

---

### 2. `server.py` — HTTP 服务器

多线程 HTTP 服务器，读取 JSON 数据驱动前端。

**功能：**
- 从 JSON 数据生成兼容前端的目录 HTML（`<a href>` 列表）
- 提供媒体文件服务（从磁盘读取，支持 ETag/304 缓存）
- 媒体文件设置长期缓存（`max-age=31536000, immutable`）
- 路径安全检查（防止目录遍历攻击）
- URL 解码日志输出

**用法：**
```bash
python3 server.py [端口] [媒体目录]
# 默认端口: 8080
# 媒体目录: 用于定位实际媒体文件
```

**路由规则：**

| 请求路径 | 处理方式 |
|---------|---------|
| `/photo.html` | 从 APP_DIR 读取前端页面 |
| `/` 或 `/subdir/` | 从 JSON 数据生成目录 HTML |
| `/subdir/file.ext` | 从磁盘读取媒体文件 |

**JSON 文件选择：** 优先 `girl.json`，回退到目录下任意 `.json` 文件。

---

### 3. `photo.html` — 前端 Gallery

纯前端单页应用，无框架依赖，原生 JS + CSS 实现。

#### 核心功能

| 功能 | 说明 |
|------|------|
| 目录树导航 | 左侧侧边栏，递归加载子目录，支持展开/折叠 |
| 文件夹卡片 | 初始展示文件夹网格，自动加载预览图 |
| 图片分组 | 同名文件（第一段点号前）归为一组，如 `IMG_001.jpg` 和 `IMG_001.bikini.jpg` |
| 分组排序 | 无后缀 > bikini > nude > remove > 其他 |
| 随机模式 | 图片组为单位 Fisher-Yates 洗牌（加密安全随机） |
| 精彩模式 | 过滤只显示含 `nude`/`bikini`/`remove` 关键字的组 |
| 暗/亮主题 | CSS 变量切换，localStorage 持久化 |
| 视频播放 | 内联播放 + 进度条 + 静音切换 |
| 全屏查看 | 双击进入，支持浏览器全屏 API |
| 缩略图面板 | 右侧显示当前图片组内所有缩略图 |

#### 快捷键

| 按键 | 功能 |
|------|------|
| ← → | 切换图片组 |
| ↑ ↓ | 切换组内图片（组内只有一张时等同切换组） |
| 双击 | 进入全屏 |
| ESC | 退出全屏 |

#### 图片分组规则

图片组仅在同一个文件夹下生效。

分组是一个多步处理流程，规则按顺序依次应用（不互斥）：

**步骤 1**：小红书图片（按用户名分组）
  - 文件名包含"来自小红书网页版"时，按下划线分隔取倒数第二段（用户名）
  - 例：`享受皇帝岛🫧_1_屁屁吃猪_来自小红书网页版.jpg` → 组: `屁屁吃猪`

**步骤 2**：去除变体后缀（取第一个点号前的部分）
  - 去除 `.bikini`、`.nude`、`.remove` 等变体标记
  - 例：`IMG001xxxxxxx.bikini.jpg` → `IMG001xxxxxxx`

**步骤 3**：长文件名前缀合并（文件名>10位且前4位完全相同）
  - 经步骤2处理后的名称超过10位，且前4位相同，则按前4位归为同一组
  - 例：`IMG001xxxxxxx` 和 `IMG001xxxxxx1` → 前4位均为 `IMG0` → 组: `IMG0`

**综合示例：**
  IMG001xxxxxxx.jpg        → 步骤2: IMG001xxxxxxx → 步骤3: 组: IMG0
  IMG001xxxxxxx.bikini.jpg → 步骤2: IMG001xxxxxxx → 步骤3: 组: IMG0
  IMG001xxxxxxx.nude.png   → 步骤2: IMG001xxxxxxx → 步骤3: 组: IMG0
  IMG001xxxxxx1.jpg        → 步骤2: IMG001xxxxxx1 → 步骤3: 组: IMG0

  短文件名（不触发步骤3）：
  IMG_001.jpg       → 步骤2: IMG_001 (7位≤10) → 组: IMG_001
  IMG_001.bikini.jpg → 步骤2: IMG_001 (7位≤10) → 组: IMG_001

#### 组内排序规则

```
优先级：无后缀(0) > bikini(1) > nude(2) > remove(3) > 其他(4)
同优先级：部分数少的在前
同部分数：数字后缀升序
最终：字母顺序

示例排序结果：
  IMG_001.jpg               (无后缀, 1部分)
  IMG_001.png               (无后缀, 1部分)
  IMG_001.bikini.jpg        (bikini, 2部分)
  IMG_001.bikini.1.jpg      (bikini, 3部分, 后缀1)
  IMG_001.nude.jpg          (nude, 2部分)
  IMG_001.remove.jpg        (remove, 2部分)
  IMG_001.remove.bikini.jpg (remove, 3部分)
```

---

### 4. `start-photo-server.sh` — 启动脚本

一键启动服务器，自动杀端口占用进程。

```bash
./start-photo-server.sh
# 默认端口 8080，媒体目录指向 /Volumes/Home1/Photo/...
```

### 5. `config.env` — 配置文件

定义源目录列表，供 `generate_info.py` 读取。

```env
SOURCE_DIRS="/your/photo/directory"
```

> 注意：此文件不提交到 git（包含本地路径）

---

## 使用步骤

### 1. 配置源目录

编辑 `config.env`，设置你的图片/视频目录：

```env
SOURCE_DIRS="/your/photo/directory"
```

### 2. 生成数据

```bash
python3 generate_info.py
```

### 3. 启动服务

```bash
# 方式一：一键启动
./start-photo-server.sh

# 方式二：手动启动
python3 server.py 8080 /your/media/directory
```

### 4. 浏览器访问

打开 `http://localhost:8080/photo.html`

---

## 技术要点

- **无框架依赖**：前端纯原生 JS + CSS，单文件交付
- **增量缓存**：`generate_info.py` 基于 `mtime` 判断是否需要重新扫描
- **安全随机**：使用 `crypto.getRandomValues()` 生成洗牌随机数
- **ETag 缓存**：服务端对目录 HTML 和文件均支持 304 响应
- **路径安全**：服务端检查文件路径，防止 `../` 目录遍历
- **兼容 Apache**：前端 `extractItems()` 解析标准目录 HTML，因此也支持直接挂载在 Apache/Nginx 的 `autoindex` 模式下使用
