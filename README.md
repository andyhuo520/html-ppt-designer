# HTML PPT Designer v5.2

**智能演示文稿设计器** - 将任何内容转化为精致的 HTML 演示文稿

## ✨ 核心特性

- 🎨 **17 种专业视觉风格** - TED 演讲、Apple Keynote、Dark Mode、红黑白科技等
- 🤖 **LLM 智能设计** - AI 根据内容自动生成最佳设计方案
- 🖼️ **多源配图系统** - 原文配图、Unsplash、AI 生成、Excalidraw 技术图表
- 🎬 **6 种翻页动画** - Fade、Cinematic、Zoom、Slide、Flip、Cut
- 📹 **视频导出** - 带 TTS 配音和内嵌字幕，支持多种语音服务
- 🎙️ **音视频转录** - 支持 YouTube、小宇宙播客、本地音频文件

## 🚀 快速开始

### 环境要求

```bash
# 系统依赖
brew install ffmpeg yt-dlp

# Python 依赖
pip install playwright edge-tts mlx-whisper
playwright install chromium
```

### 环境变量配置

```bash
# Unsplash 配图（必需）
export UNSPLASH_ACCESS_KEY="your-unsplash-access-key"

# AI 使用Zenm成插图（可选）
export ZENMUX_API_KEY="your-zenmux-api-key"

# 视频导出 TTS（可选）
export OPENAI_API_KEY="sk-..."
export VOLCENGINE_ACCESS_KEY="..."
export ZHIPUAI_API_KEY="..."
```

## 📖 使用方式

### 1. 网页转 PPT

```bash
# 抓取网页并下载原文配图
python3 scripts/fetch_webpage.py "https://example.com/article" \
  --download-images \
  --image-dir ~/Desktop/ppt_images/ \
  -o content.json
```

### 2. 音视频转 PPT

```bash
# YouTube 视频转录
python3 scripts/transcribe_audio.py "https://youtu.be/xxx"

# 小宇宙播客转录
python3 scripts/transcribe_audio.py "https://www.xiaoyuzhoufm.com/episode/xxx" \
  --mode gemini --summary

# 本地音频文件
python3 scripts/transcribe_audio.py "/path/to/podcast.mp3" \
  --mode local --output transcript.md
```

### 3. HTML PPT 转视频

```bash
# 基本用法 - Edge TTS（免费），默认启用字幕
python3 scripts/ppt_to_video.py presentation.html -o output.mp4

# 使用 OpenAI TTS（高质量）
python3 scripts/ppt_to_video.py presentation.html --tts openai -o output.mp4

# 使用火山引擎 TTS（国产推荐）
python3 scripts/ppt_to_video.py presentation.html \
  --tts volcengine --voice zh_female_tianmeixiaoyuan -o output.mp4
```

## 🎨 视觉风格

### Classic/Professional 经典专业
- **A1 TED 演讲** - 深色背景+大图 overlay，叙事演讲
- **A2 Apple Keynote** - 极简白底+超大留白，产品发布
- **A3 Typical PPT** - 深蓝+浅灰标准模板，商务汇报
- **A4 Gamma** - 现代卡片+圆角，创业路演
- **A5 Consulting** - 深蓝+金+数据驱动，战略咨询

### Editorial/Publishing 编辑出版
- **B1 Editorial** - 杂志排版+衬线字体，品牌故事
- **B2 Swiss Style** - 严格网格+红色色带，设计作品
- **B3 Newspaper** - 报纸版式+多栏文字，新闻资讯

### Design/Art 设计艺术
- **C1 Bauhaus** - 几何色块+红黄蓝三原色，艺术教育
- **C2 Kinfolk** - 莫兰迪色调+胶片质感，生活方式
- **C3 Muji** - 白灰为主+超细线条，极简品牌
- **C4 Brutalist** - 粗犷大字+高对比，先锋设计

### Tech/Future 科技未来
- **D1 Neo-Tokyo** - 霓虹粉+青+暗黑底+故障艺术，科技产品
- **D2 Dark Mode** - 深灰底+冷蓝强调+简洁边框，开发工具
- **D3 红黑白科技** - 严格三色+电路风，国产科技

### Education/Creative 教育创意
- **E1 卡通 2.5D** - 扁平阴影+多彩圆润，儿童教育
- **E2 Education** - 色彩编码+互动感，在线课程

## 📁 项目结构

```
html-ppt-designer/
├── SKILL.md                    # 完整技术文档（85KB）
├── scripts/                    # Python 脚本
│   ├── fetch_webpage.py        # 网页内容提取+配图下载
│   ├── fetch_unsplash.py       # Unsplash 配图搜索
│   ├── generate_images.py      # AI 生成插图
│   ├── transcribe_audio.py     # 音视频转录
│   ├── ppt_to_video.py         # HTML PPT 转视频
│   └── excalidraw_to_svg.py    # Excalidraw 图表转 SVG
├── templates/                  # HTML 模板
│   └── consulting.html         # 示例模板
├── references/                 # 设计参考文档
│   ├── color-system.md
│   ├── layout-patterns.md
│   ├── accessibility-guide.md
│   ├── animation-library.md
│   ├── design-philosophy.md
│   ├── image-style-red-black-white.md
│   ├── image-style-cartoon-2.5d.md
│   └── image-style-new-yorker.md
└── examples/                   # 示例文件

```

## 🎬 视频导出特性

### 内嵌字幕系统（v3.2）
- 白字黑背景圆角样式
- 按句子分割，逐句显示
- 与音频 100% 同步
- 使用 PingFang SC 字体

### TTS 服务对比

| 服务 | 费用 | 音质 | 速度 | 推荐场景 |
|------|------|------|------|---------|
| **Edge TTS** | 免费 | 良好 | 快 | 日常使用 ⭐ 推荐 |
| **OpenAI TTS** | ~$0.015/分钟 | 优秀 | 快 | 商业/高质量需求 |
| **火山引擎** | 按量付费 | 优秀 | 快 | 中文专业场景 |
| **智谱 AI** | 按量付费 | 优秀 | 快 | 中文专业场景 |
| **Fish Speech** | 免费 | 良好 | 中 | 本地部署/隐私需求 |

## 🔧 API Key 申请

### Unsplash API
1. 访问 https://unsplash.com/developers
2. 注册/登录账号
3. 创建新应用（用途：PPT 配图）
4. 获取 Access Key
5. 设置环境变量：`export UNSPLASH_ACCESS_KEY="your-key"`

### ZENMUX API
1. 访问 https://zenmux.ai
2. 注册账号并登录
3. 在控制台获取 API Key
4. 设置环境变量：`export ZENMUX_API_KEY="your-key"`
   优惠注册：https://zenmux.ai/invite/FLF08R
## 📝 设计原则

### 反 AI 审美铁律
1. ❌ 禁止千篇一律的圆角卡片堆叠
2. ❌ 禁止毫无根据的 glow/blur 装饰
3. ❌ 禁止图标当视觉主角
4. ❌ 禁止使用渐变色
5. ❌ 禁止发光效果(glow)
6. ❌ 禁止蓝+紫色彩组合

### 设计自觉
- 每一次配色必须有出处（杂志、展览、品牌案例）
- 每一处留白都是有意图的"静默表达"
- 每一个动效必须服务于叙事节奏
- 版式的张力来自"不对称的平衡"

## 📊 版本历史

- **v5.2** (2026-02-13) - 原文配图提取（零成本方案）
- **v5.1** (2026-02-13) - 控制面板增强与视觉优化
- **v5.0** (2026-02-13) - 禁止蓝紫组合
- **v4.9** (2026-02-13) - 纯色设计原则
- **v4.8** (2026-02-13) - API Key 安全修复
- **v4.7** (2026-02-12) - 国产 TTS 服务
- **v4.6** (2026-02-12) - 内嵌字幕功能
- **v4.0** (2026-02-08) - LLM 智能设计架构升级

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**作者**: Andy Hu
**版本**: 5.2
**最后更新**: 2026-02-13
