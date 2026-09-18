# goodspeedwang.github.io

个人主页（GitHub Pages），包含多个小工具 / 子站点：

- `music/` — 音乐播放器，歌词以 `.lrc` 形式存放
- `radio/` — 网络电台
- `jogging/` — 跑步记录
- `iptv/` — IPTV 播放
- `photo/` — 相册
- 其它：`nav.html` / `nav.xml`（导航）、`qr.html`、`password.html`、`medication.html` 等

`index.html` 为占位首页，导航内容由 `nav.xml` 定义。

## 音乐歌词

歌词存放在 `music/songs/<专辑名>/<歌曲名>.lrc`，由播放器 `music/music.js`
通过 `fetch()` 直接读取并解析（使用 `parseLRC`），**无需**预先转换成 `.js` 文件。

> 注意：由于使用了 `fetch()`，直接以 `file://` 方式双击打开页面时歌词无法加载。
> 本地预览请启动静态服务器（见下）。部署到 GitHub Pages 后为同源 HTTP 访问，正常工作。

歌词下载可参考 `music/scripts/download_lyrics.py`。

## 本地预览与发布

```bash
# 本地预览（fetch 需要 HTTP 环境，不能用 file://）
python3 -m http.server 8000
# 然后访问 http://localhost:8000

# 发布：提交并推送到 GitHub
./push.sh
```
