# 无障碍设计指南

## 一、WCAG 2.1 对比度标准

### 文本对比度要求

| 级别 | 正文文本 (<18px 或 <14px bold) | 大文本 (≥18px 或 ≥14px bold) |
|------|------------------------------|------------------------------|
| AA（必须达到） | ≥ 4.5:1 | ≥ 3:1 |
| AAA（推荐） | ≥ 7:1 | ≥ 4.5:1 |

### 非文本元素对比度（WCAG 2.1 新增）

| 元素类型 | 最小对比度 |
|---------|-----------|
| UI 组件（按钮边框、输入框） | ≥ 3:1（相对于相邻色） |
| 图形对象（图标、图表线） | ≥ 3:1 |
| 焦点指示器 | ≥ 3:1 |

### 对比度计算公式

```
相对亮度 L = 0.2126 × R + 0.7152 × G + 0.0722 × B
（其中 R/G/B 经过 gamma 校正：
  如果 sRGB ≤ 0.03928 → L_channel = sRGB / 12.92
  否则 → L_channel = ((sRGB + 0.055) / 1.055) ^ 2.4
）

对比度 = (L_lighter + 0.05) / (L_darker + 0.05)
```

---

## 二、常用配色对比度速查

### 浅色背景（#FFFFFF 白底）

| 文字颜色 | Hex | 对比度 | AA正文 | AA大文本 |
|---------|-----|--------|--------|---------|
| 纯黑 | `#000000` | 21:1 | ✅ | ✅ |
| 深灰 | `#1E293B` | 14.5:1 | ✅ | ✅ |
| 中深灰 | `#374151` | 10.3:1 | ✅ | ✅ |
| 灰色 | `#6B7280` | 5.0:1 | ✅ | ✅ |
| 浅灰 | `#9CA3AF` | 2.9:1 | ❌ | ✅ |
| 深蓝 | `#1E3A8A` | 9.8:1 | ✅ | ✅ |
| 蓝色 | `#3B82F6` | 3.1:1 | ❌ | ✅ |
| 深绿 | `#166534` | 8.3:1 | ✅ | ✅ |
| 红色 | `#DC2626` | 4.6:1 | ✅ | ✅ |
| 橙色 | `#F59E0B` | 2.0:1 | ❌ | ❌ |

### 深色背景（#0B1120 暗底）

| 文字颜色 | Hex | 对比度 | AA正文 | AA大文本 |
|---------|-----|--------|--------|---------|
| 纯白 | `#FFFFFF` | 18.6:1 | ✅ | ✅ |
| 浅灰 | `#F1F5F9` | 16.2:1 | ✅ | ✅ |
| 中灰 | `#94A3B8` | 7.0:1 | ✅ | ✅ |
| 暗灰 | `#475569` | 2.9:1 | ❌ | ✅ |
| 青色 | `#22D3EE` | 9.1:1 | ✅ | ✅ |
| 紫色 | `#A78BFA` | 5.8:1 | ✅ | ✅ |

---

## 三、色盲安全设计

### 色盲类型及影响

| 类型 | 影响人群 | 混淆色对 |
|------|---------|---------|
| Protanopia（红色盲） | 男性 1.3% | 红↔绿、红↔棕、绿↔棕 |
| Deuteranopia（绿色盲） | 男性 1.2% | 红↔绿、绿↔橙 |
| Tritanopia（蓝色盲） | 男女 0.01% | 蓝↔黄、紫↔红 |
| 全色盲 | 极少 | 仅能看到灰度 |

### 安全配色方案

**推荐的色盲友好配色对**：
- 蓝 + 橙：`#2563EB` + `#EA580C`
- 蓝 + 黄：`#1E40AF` + `#EAB308`
- 深色 + 浅色（明度差异大）
- 紫 + 绿：`#7C3AED` + `#16A34A`

**危险的配色对（应避免仅靠颜色区分）**：
- 红 + 绿（经典危险对）
- 红 + 棕
- 绿 + 棕
- 蓝 + 紫（在 Tritanopia 中）

### 补偿策略

当必须使用可能混淆的颜色时：
1. **同时使用形状**：✅ 圆形表示正向，❌ 叉形表示负向
2. **添加文字标签**：不仅用颜色，同时标注"增长"/"下降"
3. **使用图案/纹理**：实线 vs 虚线、填充 vs 条纹
4. **确保明度差异**：即使色相混淆，明暗对比仍可区分
5. **使用图标**：↑ 上升箭头，↓ 下降箭头

---

## 四、语义化 HTML 要求

### 标题层级
```html
<!-- 正确：层级递进 -->
<h1>Presentation Title</h1>
  <h2>Section Title</h2>
    <h3>Sub-section</h3>

<!-- 错误：跳过层级 -->
<h1>Title</h1>
  <h3>Sub-section</h3>  <!-- 跳过了 h2 -->
```

### ARIA 标注
```html
<!-- Slide 区域标注 -->
<section data-slide="0" aria-label="封面">...</section>
<section data-slide="1" aria-label="企业信息黑洞">...</section>

<!-- 数据卡片 -->
<div role="group" aria-label="关键数据指标">
  <div aria-label="增长率 80%">
    <span class="data-number" data-count="80" aria-hidden="true">0</span>
    <span class="sr-only">增长率百分之八十</span>
  </div>
</div>

<!-- 装饰性图标 -->
<span class="iconify" data-icon="ph:rocket-launch-bold" aria-hidden="true"></span>

<!-- 功能性图标 -->
<span class="iconify" data-icon="ph:warning-bold" role="img" aria-label="警告"></span>
```

### 屏幕阅读器辅助类
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

## 五、键盘可访问性

### 焦点管理
```css
/* 可见的焦点指示器 */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* 跳过链接 */
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  z-index: 100;
  padding: 8px 16px;
  background: var(--primary);
  color: white;
}
.skip-link:focus {
  top: 0;
}
```

### Tab 顺序
- 按视觉阅读顺序排列
- 隐藏的装饰元素加 `tabindex="-1"` 或 `aria-hidden="true"`
- 交互元素使用原生 `<button>` / `<a>` 而非 `<div onclick>`

---

## 六、自动验证清单

在生成 HTML 后执行以下检查：

```
□ 所有正文文本对比度 ≥ 4.5:1
□ 所有大标题对比度 ≥ 3:1
□ 未仅靠红/绿区分关键信息
□ 所有图片有 alt 属性（装饰性图片 alt=""）
□ 标题层级正确递进（h1 → h2 → h3）
□ 所有交互元素可通过键盘访问
□ 支持 prefers-reduced-motion
□ 语言标注正确（lang="zh-CN"）
□ 装饰性图标有 aria-hidden="true"
□ 功能性图标有 aria-label
```
