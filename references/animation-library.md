# 动效库完整参考 v3.0

## 一、6 种翻页动画（真正不同的视觉效果）

每种动画使用完全不同的 CSS 属性组合，切换时视觉差异明显。

### 完整 CSS 定义

```css
/* ============================== */
/* 1. FADE - 纯透明度淡入淡出     */
/* ============================== */
.transition-fade .slide-leaving {
  animation: fadeOut 0.6s ease forwards;
}
.transition-fade .slide-entering {
  animation: fadeIn 0.6s ease forwards;
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ============================== */
/* 2. SLIDE - 水平滑动 translateX */
/* ============================== */
.transition-slide .slide-leaving {
  animation: slideOutLeft 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}
.transition-slide .slide-entering {
  animation: slideInRight 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

@keyframes slideOutLeft {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(-100%); opacity: 0; }
}
@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* 反向（prev 时使用） */
@keyframes slideOutRight {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}
@keyframes slideInLeft {
  from { transform: translateX(-100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* ============================== */
/* 3. CINEMATIC - 缩放+模糊+透明  */
/* ============================== */
.transition-cinematic .slide-leaving {
  animation: cinematicOut 0.8s ease forwards;
}
.transition-cinematic .slide-entering {
  animation: cinematicIn 0.8s ease forwards;
}

@keyframes cinematicOut {
  0%   { transform: scale(1); opacity: 1; filter: blur(0px); }
  100% { transform: scale(1.15); opacity: 0; filter: blur(8px); }
}
@keyframes cinematicIn {
  0%   { transform: scale(0.8); opacity: 0; filter: blur(8px); }
  100% { transform: scale(1); opacity: 1; filter: blur(0px); }
}

/* ============================== */
/* 4. CUT - 瞬间切换（无过渡）    */
/* ============================== */
.transition-cut .slide-leaving {
  opacity: 0;
  transition: none;
}
.transition-cut .slide-entering {
  opacity: 1;
  transition: none;
}

/* ============================== */
/* 5. FLIP - 3D Y轴翻转           */
/* ============================== */
.transition-flip .slides-viewport {
  perspective: 1200px;
}
.transition-flip .slide-leaving {
  animation: flipOut 0.6s ease-in forwards;
  transform-style: preserve-3d;
  backface-visibility: hidden;
}
.transition-flip .slide-entering {
  animation: flipIn 0.6s ease-out forwards;
  transform-style: preserve-3d;
  backface-visibility: hidden;
}

@keyframes flipOut {
  0%   { transform: rotateY(0deg); opacity: 1; }
  100% { transform: rotateY(-90deg); opacity: 0; }
}
@keyframes flipIn {
  0%   { transform: rotateY(90deg); opacity: 0; }
  100% { transform: rotateY(0deg); opacity: 1; }
}

/* ============================== */
/* 6. ZOOM - 中心缩放聚焦         */
/* ============================== */
.transition-zoom .slide-leaving {
  animation: zoomOut 0.5s cubic-bezier(0.4, 0, 1, 1) forwards;
}
.transition-zoom .slide-entering {
  animation: zoomIn 0.5s cubic-bezier(0, 0, 0.2, 1) forwards;
}

@keyframes zoomOut {
  from { transform: scale(1); opacity: 1; }
  to { transform: scale(0.3); opacity: 0; }
}
@keyframes zoomIn {
  from { transform: scale(2); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

### 动画对比表

| 动画 | 核心属性 | 时长 | 缓动 | 视觉效果 |
|------|---------|------|------|---------|
| **Fade** | opacity | 0.6s | ease | 柔和渐变，通用百搭 |
| **Slide** | translateX + opacity | 0.5s | cubic-bezier | 方向性滑动，有空间感 |
| **Cinematic** | scale + opacity + blur | 0.8s | ease | 电影感，戏剧张力 |
| **Cut** | 无过渡 | 0ms | - | 瞬间切换，干脆利落 |
| **Flip** | rotateY + opacity | 0.6s | ease-in/out | 3D翻页，有趣味性 |
| **Zoom** | scale + opacity | 0.5s | custom | 聚焦/缩放，有冲击力 |

---

## 二、元素入场动画 Keyframes

### 基础入场动画

```css
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-60px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(60px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.85); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes bounceIn {
  0% { opacity: 0; transform: scale(0.3); }
  50% { opacity: 1; transform: scale(1.05); }
  70% { transform: scale(0.95); }
  100% { transform: scale(1); }
}
```

### 强调/循环动画

```css
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--accent-rgb), 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(var(--accent-rgb), 0); }
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### 特殊效果动画

```css
@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}

@keyframes underlineExpand {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}

@keyframes strokeDraw {
  from { stroke-dashoffset: var(--circumference); }
  to { stroke-dashoffset: var(--target-offset); }
}

@keyframes revealLeft {
  0% { transform: scaleX(0); transform-origin: left; }
  50% { transform: scaleX(1); transform-origin: left; }
  51% { transform-origin: right; }
  100% { transform: scaleX(0); transform-origin: right; }
}
```

---

## 三、元素动画 CSS 工具类

```css
/* 基础状态 - 所有需要动画的元素默认隐藏 */
.animate-on-scroll {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.animate-on-scroll.animate-visible {
  opacity: 1;
  transform: translateY(0);
}

/* 方向变体 */
.animate-slide-left {
  opacity: 0;
  transform: translateX(-60px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.animate-slide-left.animate-visible {
  opacity: 1;
  transform: translateX(0);
}

.animate-slide-right {
  opacity: 0;
  transform: translateX(60px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.animate-slide-right.animate-visible {
  opacity: 1;
  transform: translateX(0);
}

.animate-scale {
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.animate-scale.animate-visible {
  opacity: 1;
  transform: scale(1);
}

/* 交错延迟 */
.delay-100 { transition-delay: 100ms; }
.delay-200 { transition-delay: 200ms; }
.delay-300 { transition-delay: 300ms; }
.delay-400 { transition-delay: 400ms; }
.delay-500 { transition-delay: 500ms; }
.delay-600 { transition-delay: 600ms; }
.delay-700 { transition-delay: 700ms; }
.delay-800 { transition-delay: 800ms; }

/* 减少运动偏好 */
@media (prefers-reduced-motion: reduce) {
  .animate-on-scroll,
  .animate-slide-left,
  .animate-slide-right,
  .animate-scale {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .slide-leaving, .slide-entering {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
    filter: none !important;
  }
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

---

## 四、JavaScript 动画模块

### IntersectionObserver 触发器

```javascript
function initScrollAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-visible');
          if (entry.target.dataset.count) {
            animateCounter(entry.target);
          }
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
  );

  document.querySelectorAll(
    '.animate-on-scroll, .animate-slide-left, .animate-slide-right, .animate-scale'
  ).forEach((el) => observer.observe(el));
}
```

### 数字计数器

```javascript
function animateCounter(el) {
  const target = parseFloat(el.dataset.count);
  const suffix = el.dataset.suffix || '';
  const prefix = el.dataset.prefix || '';
  const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;
  const duration = 1500;
  const start = performance.now();

  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    const current = target * eased;

    if (decimals > 0) {
      el.textContent = prefix + current.toFixed(decimals) + suffix;
    } else {
      el.textContent = prefix + Math.round(current).toLocaleString() + suffix;
    }

    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
```

---

## 五、风格-动效映射（16+ 风格）

| 风格 | 推荐翻页动画 | 元素入场 | 强调动画 | 背景动效 |
|------|------------|---------|---------|---------|
| A1 TED | **Cinematic** | fadeIn (慢) | 无 | 无 |
| A2 Apple | **Fade** | fadeInUp (慢) | 无 | 无 |
| A3 Typical PPT | **Slide** | fadeInUp | 无 | 无 |
| A4 Gamma | **Fade** | scaleIn | pulse | 无 |
| A5 Consulting | **Fade** | fadeInUp | 计数器 | 无 |
| B1 Editorial | **Cinematic** | fadeIn | 无 | 无 |
| B2 Swiss | **Cut** | fadeInUp | 无 | 无 |
| B3 Newspaper | **Cut** | fadeIn | 无 | 无 |
| C1 Bauhaus | **Flip** | scaleIn | 无 | 无 |
| C2 Kinfolk | **Fade** | fadeIn (慢) | 无 | 无 |
| C3 Muji | **Fade** | fadeIn (超慢) | 无 | 无 |
| C4 Brutalist | **Cut** | fadeInUp (快) | 无 | 无 |
| D1 Neo-Tokyo | **Zoom** | slideIn | pulse | gradientShift |
| D2 Dark Mode | **Slide** | slideIn | pulse+计数器 | gradientShift |
| D3 红黑白 | **Flip** | fadeInUp | 计数器 | 无 |
| E1 卡通 2.5D | **Slide** | bounceIn | pulse | 无 |
| E2 Education | **Slide** | bounceIn | 计数器 | 无 |

---

## 六、性能最佳实践

1. **仅动画 GPU 属性**：`transform`、`opacity`、`filter`，避免 `width`/`height`/`margin`/`top`
2. **使用 `will-change` 谨慎**：仅在即将动画的元素上使用，动画结束后移除
3. **`requestAnimationFrame`**：所有 JS 动画使用 rAF，不用 `setInterval`
4. **动画时长**：入场 0.4-0.8s，hover 0.2-0.3s，循环 2-4s
5. **缓动函数**：
   - 入场：`ease-out` 或 `cubic-bezier(0.25, 0.46, 0.45, 0.94)`
   - 退场：`ease-in`
   - 弹性：`cubic-bezier(0.34, 1.56, 0.64, 1)`
6. **IntersectionObserver** 比 scroll 事件性能好 10x
7. **`prefers-reduced-motion`** 必须支持
