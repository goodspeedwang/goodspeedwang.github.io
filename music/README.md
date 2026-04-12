# Music 音乐播放器

一款 Spotify 风格的网页音乐播放器，支持专辑浏览、歌曲播放和播放状态记忆。

## 产品说明

### 功能特性

- **专辑浏览**：左侧边栏显示专辑列表，点击可切换专辑
- **歌曲列表**：展示当前专辑的所有歌曲，显示歌曲序号、名称和时长
- **播放控制**：支持播放/暂停、上一首、下一首
- **进度显示**：实时显示播放进度和当前时间
- **状态记忆**：自动保存播放状态，刷新页面后恢复上次播放位置
- **自动播放**：歌曲播放完毕后自动播放下一首，专辑播完后自动切换到下一张专辑

### 使用方式

1. 打开 `music/` 页面
2. 点击左侧专辑列表选择专辑
3. 点击歌曲或"播放全部"开始播放
4. 使用底部控制栏控制播放

## 技术说明

### 文件结构

```
music/
├── index.html              # 主页面
├── music.js                # 播放器核心逻辑
├── album.js                # 专辑数据配置
├── song-duration-data.js   # 歌曲时长数据（自动生成）
├── music.css               # 样式文件
├── scripts/
│   └── generate_music_durations.py  # 生成歌曲时长脚本
└── songs/                  # 歌曲文件目录
    ├── 专辑名1/
    │   ├── 歌曲1.mp3
    │   └── 歌曲2.mp3
    └── ...
```

### 技术栈

- **前端**：原生 HTML5 + CSS3 + JavaScript（无框架依赖）
- **音频**：HTML5 Audio API
- **存储**：localStorage（保存播放状态）
- **构建工具**：Python + ffprobe（生成歌曲时长数据）

### 核心模块

#### MusicPlayerApp（music.js）

播放器主模块，采用 IIFE 封装：

- **状态管理**：`state` 对象管理当前专辑、歌曲索引、播放状态
- **DOM 缓存**：`elements` 对象缓存所有 DOM 元素引用
- **事件绑定**：`bindPlayerControls()` 绑定控制按钮，`bindAudioEvents()` 绑定音频事件
- **播放逻辑**：`playSong()`、`playNextSong()`、`playPreviousSong()`
- **状态持久化**：`persistPlaybackState()` 保存到 localStorage

#### 专辑数据（album.js）

```javascript
const ALBUM = [
    {
        name: "专辑名称",
        artist: "艺术家",
        cover: "封面图片URL",
        songs: ["歌曲1", "歌曲2", ...]
    },
    ...
];
```

### 歌曲时长生成

使用 `scripts/generate_music_durations.py` 脚本：

```bash
cd music/scripts
python3 generate_music_durations.py
```

脚本会：
1. 遍历 `songs/` 目录下所有 MP3 文件
2. 使用 ffprobe 获取音频时长
3. 生成 `song-duration-data.js` 文件

**依赖**：需要系统安装 ffprobe（ffmpeg）

### 播放状态存储

使用 localStorage 保存：
- `currentAlbum`：当前专辑索引
- `currentSong`：当前歌曲索引

### 注意事项

1. **歌曲文件命名**：歌曲文件名中的 `/` 会被替换为 `_`
2. **路径格式**：歌曲路径为 `songs/{专辑名}/{歌曲名}.mp3`
3. **跨域限制**：需要通过 HTTP 服务器访问，不能直接打开 HTML 文件

## 添加新专辑

1. 在 `songs/` 目录下创建专辑文件夹
2. 将 MP3 文件放入专辑文件夹
3. 在 `album.js` 中添加专辑配置
4. 运行 `python3 scripts/generate_music_durations.py` 更新时长数据