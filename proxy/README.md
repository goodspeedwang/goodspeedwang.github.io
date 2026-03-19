# Clash 代理订阅合并工具

自动合并两个 Clash 订阅链接，并为 YouTube 和 AI 服务配置专用路由规则。

## 功能特性

- ✅ 自动合并主配置和视频配置
- ✅ 视频流量主备模式（YouTube/X.com，Video 节点为主，Main 节点为备）
- ✅ AI 服务走主配置非香港节点（自动选择最快）
- ✅ 其他外网走主配置节点中的最快节点
- ✅ 支持新增：Grok、X.com 视频
- ✅ 自动每5分钟检测节点延迟并切换
- ✅ 配置安全：敏感信息存储在环境变量中

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置订阅链接

复制环境变量模板并填入真实的订阅链接：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 主配置：用于 AI 服务等一般用途
MAIN_CONFIG_URL=https://your-main-subscription-url
# 视频配置：用于 YouTube 等视频流媒体
VIDEO_CONFIG_URL=https://your-video-subscription-url

# 订阅名称前缀
MAIN_CONFIG_NAME=主配置
VIDEO_CONFIG_NAME=视频配置

# 输出路径
OUTPUT_PATH=./merged.yaml
```

### 3. 运行脚本

```bash
# 生成配置文件
python3 merge.py
```

生成的配置文件将保存到 `merged.yaml`。

### 4. 安全检查（可选）

在提交代码前，运行安全检查确保没有泄露敏感信息：

```bash
python3 check_security.py
```

## 代理组说明

| 代理组 | 类型 | 说明 | 默认选项 |
|--------|------|------|----------|
| **Auto-Select** | url-test | 主配置节点自动选择 | - |
| **Video-Auto** | url-test | 视频配置节点自动选择 | - |
| **Video-Group** | select | 视频手动切换 | Video-Fallback |
| **Video-Fallback** | fallback | 视频主备（Video主，Main备） | - |
| **AI-Select** | url-test | 主配置非香港节点自动选择 | - |
| **AI-NonHK-Group** | select | AI 手动切换 | - |
| **Global-Group** | select | 全局手动切换 | Auto-Select |
| **🐟 漏网之鱼** | select | 兼容组 | Global-Group |

## 路由规则

### 视频路由（186条规则）
- 目标：Video-Group（默认 Video-Fallback）
  - 默认：Video-Fallback（主备模式）
    - 主：Video 配置节点（优先使用）
    - 备：Main 配置节点（Video 不可用时启用）
  - 可手动：切换到 Video-Auto 或特定节点
- 包含：YouTube、X.com/Twitter 视频等

### AI 服务路由（54条规则）
- 目标：AI-Select（主配置非香港自动选择）
- 包含：
  - OpenAI/ChatGPT
  - Google Gemini
  - Anthropic Claude
  - X.AI Grok

### 其他流量
- 目标：Global-Group（所有节点自动选择）
- 国内流量直连

## 文件说明

```
proxy/
├── .env              # 环境变量（包含订阅链接，不提交到 Git）
├── .env.example      # 环境变量模板（提交到 Git）
├── .gitignore        # Git 忽略规则
├── merge.py          # 主程序
├── requirements.txt  # Python 依赖
├── check_security.py # 安全检查脚本
├── merged.yaml       # 生成的配置文件（不提交到 Git）
└── 需求文档.md        # 详细需求文档
```

## 安全性

✅ 所有敏感信息存储在 `.env` 文件中  
✅ `.env` 和 `merged.yaml` 已添加到 `.gitignore`  
✅ 代码中不包含任何硬编码的敏感信息  
✅ 提供安全检查脚本验证配置  

## 注意事项

⚠️ **永远不要将 `.env` 文件提交到 Git**  
⚠️ **永远不要将 `merged.yaml` 文件提交到 Git**  
⚠️ 定期运行 `check_security.py` 确保没有泄露敏感信息

## 许可证

MIT
