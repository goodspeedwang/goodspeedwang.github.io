# Radio 电台播放器

一款在线电台播放器，支持 M3U8 播放列表格式，可播放 HLS 流媒体。

## 产品说明

### 功能特性

- **电台分组**：按类别分组展示电台频道
- **频道列表**：显示频道 logo 和名称
- **在线播放**：支持 HLS 流媒体播放
- **播放控制**：使用原生 HTML5 audio 控件

### 使用方式

1. 打开 `radio/` 页面
2. 浏览分组列表，点击选择电台
3. 底部播放器自动开始播放

## 技术说明

### 文件结构

```
radio/
├── index.html          # 主页面
├── radio.js            # 播放器逻辑
├── radio.css           # 样式文件
├── radio.m3u8          # 电台播放列表
├── img/                # 频道图片
│   ├── fhzw.png
│   └── fhzx.png
└── README.md           # 说明文档
```

### 技术栈

- **前端**：原生 HTML5 + CSS3 + JavaScript
- **流媒体**：hls.js（HLS 协议支持）
- **字体**：Apple SF 字体

### 核心模块

#### 播放列表解析（radio.js）

- `fetchM3U8(url)`：获取 M3U8 播放列表
- `parseM3U8(lines)`：解析 M3U8 格式，提取频道信息
- `createStationElement(station)`：创建频道 DOM 元素
- `createGroupElement(title, stations)`：创建分组 DOM 元素

#### M3U8 格式

播放列表使用标准 M3U8 格式：

```m3u8
#EXTINF:-1 tvg-logo="频道logo" group-title="分组名",频道名称
https://stream-url.m3u8
```

### 数据来源

- [Radioline](https://www.radioline.co/)
- [zhibo.fm](https://zhibo.fm/)
- [worldradiomap](https://worldradiomap.com/)
- [蜻蜓FM](https://m.qtfm.cn/categories/5)
- [Kimentanm](https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/radio.m3u)

## 添加新电台

编辑 `radio.m3u8` 文件，按以下格式添加：

```m3u8
#EXTINF:-1 tvg-logo="logo_url" group-title="分组名",频道名称
流媒体地址
```

## 注意事项

1. 需要通过 HTTP 服务器访问
2. HLS 流需要浏览器支持或使用 hls.js
3. 部分 HLS 流可能有跨域限制