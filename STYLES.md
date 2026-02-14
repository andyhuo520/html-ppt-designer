# HTML PPT Designer - 完整风格指南

本文档详细列出所有 17 种视觉风格的完整配置信息。

---

## 目录

### Classic/Professional 经典专业
- [A1 - TED 演讲](#a1---ted-演讲)
- [A2 - Apple Keynote](#a2---apple-keynote)
- [A3 - Typical PPT](#a3---typical-ppt)
- [A4 - Gamma](#a4---gamma)
- [A5 - Consulting](#a5---consulting)

### Editorial/Publishing 编辑出版
- [B1 - Editorial](#b1---editorial)
- [B2 - Swiss Style](#b2---swiss-style)
- [B3 - Newspaper](#b3---newspaper)

### Design/Art 设计艺术
- [C1 - Bauhaus](#c1---bauhaus)
- [C2 - Kinfolk](#c2---kinfolk)
- [C3 - Muji](#c3---muji)
- [C4 - Brutalist](#c4---brutalist)

### Tech/Future 科技未来
- [D1 - Neo-Tokyo](#d1---neo-tokyo)
- [D2 - Dark Mode](#d2---dark-mode)
- [D3 - 红黑白科技](#d3---红黑白科技)

### Education/Creative 教育创意
- [E1 - 卡通 2.5D](#e1---卡通-25d)
- [E2 - Education](#e2---education)

---

## Classic/Professional 经典专业

### A1 - TED 演讲

**适用场景**：叙事演讲、故事分享、个人演讲

**设计特征**：
- 深色背景（#1A1A1A）
- 大尺寸全屏图片
- 半透明黑色 overlay 叠加文字
- 字号巨大（Hero 80px+）
- 单页信息密度极低（1 个核心观点）

**CSS 变量**：
```css
:root {
  --primary: #E62B1E;           /* TED 红 */
  --primary-light: #FF4136;
  --secondary: #2C2C2C;
  --accent: #FFFFFF;
  --bg-page: #1A1A1A;           /* 深黑背景 */
  --bg-card: #2C2C2C;
  --bg-section: #333333;
  --text-heading: #FFFFFF;
  --text-body: #E0E0E0;
  --text-muted: #999999;
  --border: #444444;
}
```

**推荐配图**：Unsplash 高质量照片（戏剧性、暗色调、电影感）

**推荐动画**：Cinematic（电影感缩放）

---

### A2 - Apple Keynote

**适用场景**：产品发布、品牌展示、极简主义

**设计特征**：
- 极简白底
- San Francisco 字体气质
- 留白 >60%
- 产品图居中
- 超大标题（56px+）
- 几乎无边框

**CSS 变量**：
```css
:root {
  --primary: #1D1D1F;
  --primary-light: #424245;
  --secondary: #6E6E73;
  --accent: #0071E3;            /* Apple 蓝 */
  --bg-page: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-section: #F5F5F7;
  --text-heading: #1D1D1F;
  --text-body: #424245;
  --text-muted: #86868B;
  --border: #D2D2D7;
}
```

**推荐配图**：产品照片、极简摄影、纯白背景

**推荐动画**：Fade（简洁优雅）

---

### A3 - Typical PPT

**适用场景**：商务汇报、企业内部分享、标准演示

**设计特征**：
- 深蓝(#2B579A)+浅灰背景
- 标准标题+副标题+正文层次
- 项目符号列表
- 页眉页脚
- 标准布局

**CSS 变量**：
```css
:root {
  --primary: #2B579A;           /* 商务蓝 */
  --primary-light: #4472C4;
  --secondary: #5B9BD5;
  --accent: #FFC000;            /* 金色强调 */
  --bg-page: #F0F4FA;
  --bg-card: #FFFFFF;
  --bg-section: #E8EEF7;
  --text-heading: #1F3864;
  --text-body: #404040;
  --text-muted: #808080;
  --border: #D6DCE4;
}
```

**推荐配图**：图标方案、信息图表

**推荐动画**：Slide（经典翻页）

---

### A4 - Gamma

**适用场景**：创业路演、现代化演示、在线分享

**设计特征**：
- 现代卡片式布局
- 圆角 16px
- 柔和投影
- 天蓝色(#0EA5E9)强调
- 适度留白
- 创业路演感

**CSS 变量**：
```css
:root {
  --primary: #0EA5E9;           /* 天蓝色 */
  --primary-light: #38BDF8;
  --secondary: #00CEC9;
  --accent: #F59E0B;            /* 橙色点缀 */
  --bg-page: #FAFEFF;
  --bg-card: #FFFFFF;
  --bg-section: #F0F9FF;
  --text-heading: #2D3436;
  --text-body: #545454;
  --text-muted: #A0A0A0;
  --border: #ECECEC;
  --card-radius: 16px;
  --card-shadow: 0 2px 12px rgba(14,165,233,0.08);
}
```

**推荐配图**：Unsplash 现代照片、AI 生成插图

**推荐动画**：Zoom（视觉冲击）

---

### A5 - Consulting

**适用场景**：战略咨询、数据报告、商业分析

**设计特征**：
- 深蓝+金配色
- 数据卡片密集
- 等距投影图表
- 框架模型图
- 多列并排
- KPI 大数字

**CSS 变量**：
```css
:root {
  --primary: #1E3A5F;           /* 深蓝 */
  --primary-light: #2D5F8A;
  --secondary: #4A90A4;
  --accent: #D4A843;            /* 金色 */
  --accent-warm: #C17F24;
  --bg-page: #FAFBFC;
  --bg-card: #FFFFFF;
  --bg-section: #F0F4F8;
  --text-heading: #0F2137;
  --text-body: #3A4F66;
  --text-muted: #7A8FA3;
  --border: #E2E8F0;
}
```

**推荐配图**：Excalidraw 技术图表、信息图表

**推荐动画**：Slide（专业感）

---

## Editorial/Publishing 编辑出版

### B1 - Editorial

**适用场景**：品牌故事、杂志风格、内容营销

**设计特征**：
- 衬线标题+无衬线正文
- 分栏排版
- 大面积留白
- pull-quote 大引用
- 黑白摄影配图
- 首字下沉

**CSS 变量**：
```css
:root {
  --primary: #1A1A1A;
  --primary-light: #333333;
  --secondary: #666666;
  --accent: #C0392B;            /* 深红点缀 */
  --bg-page: #FEFEFE;
  --bg-card: #FFFFFF;
  --bg-section: #F5F5F0;
  --text-heading: #1A1A1A;
  --text-body: #333333;
  --text-muted: #888888;
  --border: #E0E0E0;
  --font-heading: 'Playfair Display', 'Noto Serif SC', Georgia, serif;
  --font-body: 'Source Sans Pro', 'Noto Sans SC', sans-serif;
}
```

**推荐配图**：Unsplash Editorial 风格照片

**推荐动画**：Fade（优雅）

---

### B2 - Swiss Style

**适用场景**：设计作品集、现代主义、平面设计

**设计特征**：
- 严格网格系统
- Helvetica 无衬线
- 红色色带分割
- 不对称布局
- 信息层次分明

**CSS 变量**：
```css
:root {
  --primary: #D0021B;           /* 瑞士红 */
  --primary-light: #E63946;
  --secondary: #2C2C2C;
  --accent: #D0021B;
  --bg-page: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-section: #F2F2F2;
  --text-heading: #2C2C2C;
  --text-body: #404040;
  --text-muted: #808080;
  --border: #CCCCCC;
  --font-heading: 'Helvetica Neue', 'Arial', sans-serif;
}
```

**推荐配图**：几何装饰、图标方案

**推荐动画**：Cut（瞬间切换）

---

### B3 - Newspaper

**适用场景**：新闻资讯、时事报道、信息密集型内容

**设计特征**：
- 报纸版式
- 多栏文字
- 报头大标题
- 分割线
- 黑白灰+单色点缀
- 引用框

**CSS 变量**：
```css
:root {
  --primary: #1A1A1A;
  --primary-light: #333333;
  --secondary: #555555;
  --accent: #B22222;            /* 深红 */
  --bg-page: #F5F1EB;           /* 报纸米色 */
  --bg-card: #FFFDF7;
  --bg-section: #F0ECE3;
  --text-heading: #1A1A1A;
  --text-body: #333333;
  --text-muted: #777777;
  --border: #D4CFC5;
  --font-heading: 'Playfair Display', 'Times New Roman', serif;
}
```

**推荐配图**：纪实摄影、新闻照片

**推荐动画**：Slide（翻页感）

---

## Design/Art 设计艺术

### C1 - Bauhaus

**适用场景**：艺术教育、设计理论、创意展示

**设计特征**：
- 几何色块（红黄蓝三原色）
- 粗线条网格
- 不规则色块拼接
- 理性构成

**CSS 变量**：
```css
:root {
  --primary: #E63B2E;           /* 包豪斯红 */
  --primary-light: #FF5A4F;
  --secondary: #2B4FA2;         /* 包豪斯蓝 */
  --accent: #F5C300;            /* 包豪斯黄 */
  --bg-page: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-section: #F7F7F7;
  --text-heading: #1A1A1A;
  --text-body: #333333;
  --text-muted: #888888;
  --border: #E0E0E0;
}
```

**推荐配图**：几何装饰、AI 生成抽象艺术

**推荐动画**：Flip（3D 翻转）

---

### C2 - Kinfolk

**适用场景**：生活方式、品牌故事、温暖叙事

**设计特征**：
- 莫兰迪色调
- 自然光影质感
- 胶片颗粒感
- 温暖米色/棕色/橄榄
- 大量呼吸留白

**CSS 变量**：
```css
:root {
  --primary: #9B7B5E;           /* 温暖棕 */
  --primary-light: #B8A08A;
  --secondary: #8FA387;         /* 橄榄绿 */
  --accent: #D4AAA0;            /* 粉棕 */
  --bg-page: #FAF7F2;
  --bg-card: #FFFCF7;
  --bg-section: #F3EDE5;
  --text-heading: #5A4A3A;
  --text-body: #6B5E52;
  --text-muted: #A09585;
  --border: #E5DDD3;
}
```

**推荐配图**：Unsplash Kinfolk 风格照片

**推荐动画**：Fade（温柔）

---

### C3 - Muji

**适用场景**：极简品牌、产品展示、日式美学

**设计特征**：
- 白灰为主
- 超细线条（0.5px）
- 日式简约
- 自然材质纹理暗示
- 极致留白

**CSS 变量**：
```css
:root {
  --primary: #5C5C5C;
  --primary-light: #7A7A7A;
  --secondary: #8B7355;         /* 原木色 */
  --accent: #B8A08A;
  --bg-page: #F7F5F0;
  --bg-card: #FFFFFF;
  --bg-section: #F0EDE8;
  --text-heading: #3A3A3A;
  --text-body: #5C5C5C;
  --text-muted: #999999;
  --border: #E5E0D8;
}
```

**推荐配图**：极简摄影、纯文字排版

**推荐动画**：Fade（极简）

---

### C4 - Brutalist

**适用场景**：先锋设计、实验性项目、艺术展览

**设计特征**：
- 大字铺满
- 粗边框（3px+）
- 高对比黑白
- 原始粗犷
- 有意的"不完美"感

**CSS 变量**：
```css
:root {
  --primary: #000000;
  --primary-light: #333333;
  --secondary: #555555;
  --accent: #FF3D00;            /* 橙红 */
  --bg-page: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-section: #F0F0F0;
  --text-heading: #000000;
  --text-body: #333333;
  --text-muted: #777777;
  --border: #000000;
}
```

**推荐配图**：几何装饰、粗犷图形

**推荐动画**：Cut（粗暴切换）

---

## Tech/Future 科技未来

### D1 - Neo-Tokyo

**适用场景**：科技产品、未来主义、赛博朋克

**设计特征**：
- 深黑底(#0A0A0F)
- 霓虹粉(#FF2D6B)/青(#00B4D8)/绿(#39FF14)
- 故障艺术纹理
- 日式排版

**CSS 变量**：
```css
:root {
  --primary: #FF2D6B;           /* 霓虹粉 */
  --primary-light: #FF5A8A;
  --secondary: #00B4D8;         /* 霓虹青 */
  --accent: #39FF14;            /* 霓虹绿 */
  --bg-page: #0A0A0F;
  --bg-card: #141420;
  --bg-section: #1A1A2E;
  --text-heading: #FFFFFF;
  --text-body: #C0C0D0;
  --text-muted: #6A6A80;
  --border: rgba(255,255,255,0.08);
}
```

**推荐配图**：AI 生成科技插图、故障艺术

**推荐动画**：Cinematic（科幻感）

---

### D2 - Dark Mode

**适用场景**：开发者工具、技术文档、代码展示

**设计特征**：
- 深灰底(#0F172A)
- 冷蓝(#3B82F6)强调色
- 简洁边框
- 代码风排版
- 终端感

**CSS 变量**：
```css
:root {
  --primary: #3B82F6;           /* 冷蓝 */
  --primary-light: #60A5FA;
  --secondary: #64748B;
  --accent: #06B6D4;            /* 青色 */
  --bg-page: #0F172A;
  --bg-card: #1E293B;
  --bg-section: #1E293B;
  --text-heading: #F1F5F9;
  --text-body: #94A3B8;
  --text-muted: #475569;
  --border: rgba(148,163,184,0.15);
}
```

**推荐配图**：Excalidraw 技术图表、代码截图

**推荐动画**：Slide（专业）

---

### D3 - 红黑白科技

**适用场景**：国产科技、硬核技术、工业设计

**设计特征**：
- 严格红黑白三色
- 几何连接线（电路风）
- 等距视角图形
- 高对比

**CSS 变量**：
```css
:root {
  --primary: #E63946;           /* 科技红 */
  --primary-light: #FF5A65;
  --secondary: #1A1A1A;
  --accent: #E63946;
  --bg-page: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-section: #F5F5F5;
  --text-heading: #000000;
  --text-body: #1A1A1A;
  --text-muted: #808080;
  --border: #E0E0E0;
}
```

**推荐配图**：AI 生成红黑白插图、Excalidraw 图表

**推荐动画**：Zoom（科技感）

---

## Education/Creative 教育创意

### E1 - 卡通 2.5D

**适用场景**：儿童教育、轻松主题、趣味展示

**设计特征**：
- 扁平+柔和阴影
- 蓝+绿+橙多彩和谐
- 圆润图标
- Q 版角色
- 等距 2.5D 视角

**CSS 变量**：
```css
:root {
  --primary: #4A90E2;           /* 蓝色 */
  --primary-light: #6BB5FF;
  --secondary: #10B981;         /* 绿色 */
  --accent: #F39C12;            /* 橙色 */
  --accent-warm: #FFD93D;       /* 黄色 */
  --bg-page: #F0F7FF;
  --bg-card: #FFFFFF;
  --bg-section: #E8F4FD;
  --text-heading: #2C3E50;
  --text-body: #4A5568;
  --text-muted: #A0AEC0;
  --border: #D6E8F7;
}
```

**推荐配图**：AI 生成卡通插图

**推荐动画**：Zoom（活泼）

---

### E2 - Education

**适用场景**：在线课程、教学演示、知识分享

**设计特征**：
- 色彩编码知识点
  - 蓝=概念
  - 绿=案例
  - 橙=重点
  - 红=注意
- 互动元素暗示
- 清晰层次

**CSS 变量**：
```css
:root {
  --primary: #2563EB;           /* 蓝色-概念 */
  --primary-light: #3B82F6;
  --secondary: #10B981;         /* 绿色-案例 */
  --accent: #F59E0B;            /* 橙色-重点 */
  --highlight: #EF4444;         /* 红色-注意 */
  --bg-page: #FFF7ED;
  --bg-card: #FFFFFF;
  --bg-section: #FEF3C7;
  --text-heading: #1E293B;
  --text-body: #4B5563;
  --text-muted: #9CA3AF;
  --border: #FDE68A;
}
```

**推荐配图**：信息图表、Excalidraw 图表

**推荐动画**：Slide（教学感）

---

## 风格选择建议

### 按内容类型推荐

| 内容类型 | 推荐风格 | 备选风格 |
|---------|---------|---------|
| 演讲/叙事 | A1 TED 演讲 | D1 Neo-Tokyo, B1 Editorial |
| 产品发布 | A2 Apple Keynote | A4 Gamma |
| 商务汇报 | A3 Typical PPT | A5 Consulting |
| 数据报告 | A5 Consulting | B3 Newspaper |
| 科技主题 | D1 Neo-Tokyo | D2 Dark Mode, D3 红黑白科技 |
| 开发者/工具 | D2 Dark Mode | D1 Neo-Tokyo |
| 架构设计 | A5 Consulting | D2 Dark Mode |
| 教育/教程 | E2 Education | E1 卡通 2.5D |
| 品牌故事 | B1 Editorial | C2 Kinfolk |
| 生活方式 | C2 Kinfolk | C3 Muji |
| 艺术创意 | C1 Bauhaus | C4 Brutalist |
| 新闻资讯 | B3 Newspaper | B2 Swiss |
| 极简主义 | C3 Muji | A2 Apple Keynote |

### 按配图方案推荐

| 配图方案 | 适合风格 |
|---------|---------|
| Unsplash 照片 | A1, A2, B1, B3, C2 |
| AI 生成插图 | D1, D3, E1, C1 |
| Excalidraw 图表 | A5, D2, D3, E2 |
| 图标方案 | A3, A4, B2, C3 |
| 纯文字排版 | A2, C3, C4 |

### 按动画效果推荐

| 动画效果 | 适合风格 |
|---------|---------|
| Fade | A2, B1, C2, C3 |
| Cinematic | A1, D1 |
| Zoom | A4, D3, E1 |
| Slide | A3, A5, B3, E2 |
| Flip | C1 |
| Cut | B2, C4 |

---

## 设计原则

### 禁止事项
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

---

**文档版本**: 5.2
**最后更新**: 2026-02-15
