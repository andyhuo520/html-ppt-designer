#!/usr/bin/env python3
"""
HTML PPT Generator - 核心生成脚本
将 slides.json + 模板/LLM设计 → 完整 HTML 演示文稿

用法:
    # 使用 LLM 生成的 CSS（推荐）
    python generate_html.py slides.json --llm-css design.json --output presentation.html

    # 使用预设模板（fallback）
    python generate_html.py slides.json --style A1 --output presentation.html
    python generate_html.py slides.json --style B1 --images images.json -o out.html
"""

import json
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
BASE_DIR = TEMPLATES_DIR / "base"


# ============================================================================
# 风格映射（本地模板 fallback）
# ============================================================================
STYLE_MAP = {
    "A1": {"name": "ted", "class": "style-ted", "file": "classic/a1-ted.html"},
    "A2": {"name": "apple", "class": "style-apple", "file": "classic/a2-apple.html"},
    "A3": {"name": "typical", "class": "style-typical", "file": "classic/a3-typical.html"},
    "A4": {"name": "gamma", "class": "style-gamma", "file": "classic/a4-gamma.html"},
    "A5": {"name": "consulting", "class": "style-consulting", "file": "classic/a5-consulting.html"},
    "B1": {"name": "editorial", "class": "style-editorial", "file": "editorial/b1-editorial.html"},
    "B2": {"name": "swiss", "class": "style-swiss", "file": "editorial/b2-swiss.html"},
    "B3": {"name": "newspaper", "class": "style-newspaper", "file": "editorial/b3-newspaper.html"},
    "C1": {"name": "bauhaus", "class": "style-bauhaus", "file": "design/c1-bauhaus.html"},
    "C2": {"name": "kinfolk", "class": "style-kinfolk", "file": "design/c2-kinfolk.html"},
    "C3": {"name": "muji", "class": "style-muji", "file": "design/c3-muji.html"},
    "C4": {"name": "brutalist", "class": "style-brutalist", "file": "design/c4-brutalist.html"},
    "D1": {"name": "neo-tokyo", "class": "style-neo-tokyo", "file": "tech/d1-neo-tokyo.html"},
    "D2": {"name": "dark-mode", "class": "style-dark-mode", "file": "tech/d2-dark-mode.html"},
    "D3": {"name": "red-black-tech", "class": "style-red-black-tech", "file": "tech/d3-red-black-tech.html"},
    "E1": {"name": "cartoon", "class": "style-cartoon", "file": "education/e1-cartoon-2-5d.html"},
    "E2": {"name": "education", "class": "style-education", "file": "education/e2-education.html"},
}


# ============================================================================
# LLM 设计生成器
# ============================================================================
class LLMDesignGenerator:
    """处理 LLM 生成的 CSS 设计"""

    def __init__(self, design_spec: Dict):
        """
        design_spec 结构:
        {
            "concept": "设计理念描述",
            "colors": {
                "primary": "#XXXXXX",
                "primary_light": "#XXXXXX",
                "secondary": "#XXXXXX",
                "accent": "#XXXXXX",
                "bg_page": "#XXXXXX",
                "bg_card": "#XXXXXX",
                "text_heading": "#XXXXXX",
                "text_body": "#XXXXXX",
                "text_muted": "#XXXXXX"
            },
            "fonts": {
                "heading": "Font Name",
                "body": "Font Name",
                "google_fonts_url": "https://fonts.googleapis.com/css2?..."
            },
            "spacing": {
                "xs": "4px", "sm": "8px", "md": "16px", "lg": "32px", "xl": "64px"
            },
            "radius": "8px",
            "transition": "fade",
            "layouts": {
                "cover": "...CSS...",
                "content": "...CSS...",
                "quote": "...CSS...",
                "ending": "...CSS..."
            }
        }
        """
        self.spec = design_spec
        self.colors = design_spec.get("colors", self._default_colors())
        self.fonts = design_spec.get("fonts", self._default_fonts())
        self.spacing = design_spec.get("spacing", self._default_spacing())
        self.radius = design_spec.get("radius", "8px")
        self.transition = design_spec.get("transition", "fade")
        self.layouts = design_spec.get("layouts", {})
        self.concept = design_spec.get("concept", "")

    def _default_colors(self) -> Dict:
        return {
            "primary": "#1A1A1A",
            "primary_light": "#333333",
            "secondary": "#666666",
            "accent": "#E63946",
            "bg_page": "#FFFFFF",
            "bg_card": "#FFFFFF",
            "bg_section": "#F5F5F5",
            "text_heading": "#1A1A1A",
            "text_body": "#333333",
            "text_muted": "#888888",
            "border": "#E0E0E0"
        }

    def _default_fonts(self) -> Dict:
        return {
            "heading": "'Noto Serif SC', Georgia, serif",
            "body": "'Noto Sans SC', sans-serif",
            "google_fonts_url": "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;600;700&display=swap"
        }

    def _default_spacing(self) -> Dict:
        return {
            "xs": "4px", "sm": "8px", "md": "16px", "lg": "32px", "xl": "64px"
        }

    def generate_css_variables(self) -> str:
        """生成 CSS 变量定义"""
        return f"""
        :root {{
            /* 颜色系统 */
            --primary: {self.colors.get('primary', '#1A1A1A')};
            --primary-light: {self.colors.get('primary_light', '#333333')};
            --secondary: {self.colors.get('secondary', '#666666')};
            --accent: {self.colors.get('accent', '#E63946')};
            --bg-page: {self.colors.get('bg_page', '#FFFFFF')};
            --bg-card: {self.colors.get('bg_card', '#FFFFFF')};
            --bg-section: {self.colors.get('bg_section', '#F5F5F5')};
            --text-heading: {self.colors.get('text_heading', '#1A1A1A')};
            --text-body: {self.colors.get('text_body', '#333333')};
            --text-muted: {self.colors.get('text_muted', '#888888')};
            --border: {self.colors.get('border', '#E0E0E0')};

            /* 间距系统 */
            --spacing-xs: {self.spacing.get('xs', '4px')};
            --spacing-sm: {self.spacing.get('sm', '8px')};
            --spacing-md: {self.spacing.get('md', '16px')};
            --spacing-lg: {self.spacing.get('lg', '32px')};
            --spacing-xl: {self.spacing.get('xl', '64px')};

            /* 圆角 */
            --radius: {self.radius};
        }}
        """

    def generate_base_styles(self) -> str:
        """生成基础样式"""
        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}

        body {{
            font-family: {self.fonts.get('body', 'sans-serif')};
            background: var(--bg-page);
            color: var(--text-body);
            line-height: 1.6;
        }}
        """

    def generate_slide_styles(self) -> str:
        """生成幻灯片样式"""
        return """
        .slides-viewport {
            position: relative;
            width: 100%;
            height: 100vh;
            overflow: hidden;
        }

        .slide {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 80px 120px;
            opacity: 0;
            visibility: hidden;
            background: var(--bg-page);
        }

        .slide.slide-active {
            opacity: 1;
            visibility: visible;
        }

        .slide-title {
            font-family: var(--font-heading, serif);
            font-size: 48px;
            font-weight: 600;
            color: var(--text-heading);
            margin-bottom: 24px;
            line-height: 1.2;
        }

        .slide-subtitle {
            font-size: 20px;
            color: var(--primary);
            margin-bottom: 16px;
        }

        .slide-text {
            font-size: 18px;
            line-height: 1.8;
            color: var(--text-body);
            max-width: 800px;
        }

        .divider {
            width: 60px;
            height: 2px;
            background: var(--primary);
            margin: 20px auto;
        }
        """

    def generate_cover_styles(self) -> str:
        """生成封面页样式"""
        custom_css = self.layouts.get("cover", "")
        return f"""
        .slide-cover {{
            text-align: center;
            background: var(--bg-page);
        }}

        .slide-cover .cover-content {{
            max-width: 700px;
        }}

        .slide-cover .slide-title {{
            font-size: 64px;
            margin-bottom: 24px;
        }}

        .slide-cover .slide-subtitle {{
            font-size: 24px;
            color: var(--primary);
        }}

        {custom_css}
        """

    def generate_content_styles(self) -> str:
        """生成内容页样式"""
        custom_css = self.layouts.get("content", "")
        return f"""
        .slide-content {{
            text-align: center;
        }}

        .slide-content .slide-title {{
            font-size: 40px;
        }}

        .slide-content .content-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 60px;
            max-width: 1000px;
            text-align: left;
        }}

        .slide-content .main-column {{
            text-align: left;
        }}

        .slide-content .side-column {{
            text-align: center;
        }}

        .slide-content .side-image {{
            max-width: 100%;
            max-height: 280px;
            object-fit: cover;
            border-radius: var(--radius);
        }}

        {custom_css}
        """

    def generate_quote_styles(self) -> str:
        """生成金句页样式"""
        custom_css = self.layouts.get("quote", "")
        return f"""
        .slide-quote {{
            background: var(--bg-section);
        }}

        .slide-quote .quote-box {{
            background: var(--bg-card);
            padding: 50px 60px;
            max-width: 700px;
            text-align: center;
            border-radius: var(--radius);
        }}

        .slide-quote .quote-text {{
            font-size: 32px;
            font-style: italic;
            color: var(--text-heading);
            line-height: 1.6;
        }}

        {custom_css}
        """

    def generate_ending_styles(self) -> str:
        """生成结尾页样式"""
        custom_css = self.layouts.get("ending", "")
        return f"""
        .slide-ending {{
            text-align: center;
            background: var(--bg-section);
        }}

        .slide-ending .slide-title {{
            font-size: 56px;
        }}

        .slide-ending .slide-subtitle {{
            font-size: 20px;
            color: var(--primary);
        }}

        {custom_css}
        """

    def generate_control_panel_styles(self) -> str:
        """生成控制面板样式"""
        return """
        .control-panel {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 24px;
            background: var(--bg-card);
            border-radius: var(--radius);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border);
            z-index: 1000;
            transition: opacity 0.4s ease, transform 0.4s ease;
        }

        .control-panel:hover {
            opacity: 1 !important;
            pointer-events: auto !important;
            transform: translateX(-50%) translateY(0) !important;
        }

        .autoplay-toggle {
            background: none;
            border: none;
            cursor: pointer;
            color: var(--primary);
            padding: 8px;
            transition: all 0.2s;
        }

        .autoplay-toggle:hover {
            color: var(--text-heading);
        }

        .autoplay-toggle .iconify {
            font-size: 24px;
        }

        .nav-dots {
            display: flex;
            gap: 8px;
        }

        .nav-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--border);
            cursor: pointer;
            transition: all 0.2s;
        }

        .nav-dot:hover {
            background: var(--primary-light);
        }

        .nav-dot.active {
            background: var(--primary);
            transform: scale(1.3);
        }

        .slide-counter {
            font-size: 14px;
            color: var(--text-muted);
            min-width: 50px;
        }

        .style-control {
            display: flex;
            gap: 6px;
            margin-left: 12px;
            padding-left: 12px;
            border-left: 1px solid var(--border);
        }

        .style-btn {
            padding: 6px 12px;
            font-size: 11px;
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .style-btn:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        .style-btn.active {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }

        .photo-attribution {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 8px;
            text-align: center;
        }

        .photo-attribution a {
            color: var(--text-muted);
            text-decoration: none;
        }

        @media (max-width: 768px) {
            .slide {
                padding: 50px 30px;
            }
            .slide-title {
                font-size: 32px;
            }
            .slide-text {
                font-size: 16px;
            }
            .control-panel {
                padding: 10px 16px;
            }
            .style-control {
                display: none;
            }
        }
        """

    def generate_full_css(self, animations_css: str = "") -> str:
        """生成完整 CSS"""
        return f"""
        {self.generate_css_variables()}

        {self.generate_base_styles()}

        /* 幻灯片基础样式 */
        {self.generate_slide_styles()}

        /* 封面页 */
        {self.generate_cover_styles()}

        /* 内容页 */
        {self.generate_content_styles()}

        /* 金句页 */
        {self.generate_quote_styles()}

        /* 结尾页 */
        {self.generate_ending_styles()}

        /* 控制面板 */
        {self.generate_control_panel_styles()}

        /* 动画系统 */
        {animations_css}
        """

    def get_google_fonts_link(self) -> str:
        """获取 Google Fonts 链接"""
        url = self.fonts.get("google_fonts_url", "")
        if url:
            return f'<link href="{url}" rel="stylesheet">'
        return ""

    def get_font_family_style(self) -> str:
        """获取字体系列样式"""
        heading = self.fonts.get("heading", "serif")
        body = self.fonts.get("body", "sans-serif")
        return f"""
        :root {{
            --font-heading: {heading};
            --font-body: {body};
        }}
        """


# ============================================================================
# 模板引擎
# ============================================================================
class TemplateEngine:
    """简单的模板引擎，支持变量、条件、循环"""

    def __init__(self, template: str):
        self.template = template

    def render(self, context: Dict[str, Any]) -> str:
        """渲染模板"""
        result = self.template

        # 处理条件块 {{#VAR}}...{{/VAR}}
        result = self._process_conditionals(result, context)

        # 处理循环块 {{#ITEMS}}...{{/ITEMS}}
        result = self._process_loops(result, context)

        # 处理简单变量 {{VAR}}
        result = self._process_variables(result, context)

        return result

    def _process_conditionals(self, template: str, context: Dict) -> str:
        """处理条件块"""
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

        def replace_cond(match):
            var_name = match.group(1)
            content = match.group(2)
            value = context.get(var_name)

            # 检查条件是否为真
            if value and value not in [False, None, "", [], {}]:
                return content
            return ""

        return re.sub(pattern, replace_cond, template, flags=re.DOTALL)

    def _process_loops(self, template: str, context: Dict) -> str:
        """处理循环块"""
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

        def replace_loop(match):
            var_name = match.group(1)
            content = match.group(2)
            items = context.get(var_name, [])

            if not isinstance(items, list):
                # 如果不是列表，当作条件处理
                if items:
                    return content
                return ""

            result_parts = []
            for i, item in enumerate(items):
                item_content = content
                if isinstance(item, dict):
                    # 字典项：替换所有键
                    for k, v in item.items():
                        item_content = item_content.replace(f"{{{{{k}}}}}", str(v) if v else "")
                    item_content = item_content.replace("{{index}}", str(i))
                    item_content = item_content.replace("{{.}}", "")
                else:
                    # 简单值：替换 {{.}}
                    item_content = item_content.replace("{{.}}", str(item) if item else "")
                    item_content = item_content.replace("{{index}}", str(i))
                result_parts.append(item_content)

            return "".join(result_parts)

        return re.sub(pattern, replace_loop, template, flags=re.DOTALL)

    def _process_variables(self, template: str, context: Dict) -> str:
        """处理简单变量"""
        pattern = r'\{\{(\w+)\}\}'

        def replace_var(match):
            var_name = match.group(1)
            value = context.get(var_name, "")
            return str(value) if value else ""

        return re.sub(pattern, replace_var, template)


# ============================================================================
# HTML 生成器
# ============================================================================
class HTMLGenerator:
    """HTML 演示文稿生成器"""

    def __init__(self, style_code: str = "A1"):
        self.style_code = style_code.upper()
        self.style_info = STYLE_MAP.get(self.style_code, STYLE_MAP["A1"])
        self.template = self._load_template()
        self.base_css = self._load_base_css()
        self.base_js = self._load_base_js()
        self.animations_css = self._load_animations_css()

    def _load_template(self) -> str:
        """加载风格模板"""
        template_path = TEMPLATES_DIR / self.style_info["file"]
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        else:
            # 使用默认模板
            return self._get_default_template()

    def _load_base_css(self) -> str:
        """加载基础 CSS 变量"""
        css_path = BASE_DIR / "_variables.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""

    def _load_base_js(self) -> str:
        """加载基础 JS 引擎"""
        js_path = BASE_DIR / "_slide_engine.js"
        if js_path.exists():
            return js_path.read_text(encoding="utf-8")
        return ""

    def _load_animations_css(self) -> str:
        """加载动画 CSS"""
        css_path = BASE_DIR / "_animations.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""

    def _get_default_template(self) -> str:
        """获取默认模板（当风格模板不存在时）"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://code.iconify.design/3/3.1.1/iconify.min.js"></script>
    <style>
        :root {
            --primary: #1E3A5F;
            --bg-page: #FAFBFC;
            --text-heading: #0F2137;
            --text-body: #3A4F66;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Noto Sans SC', sans-serif;
            background: var(--bg-page);
            color: var(--text-body);
        }
        .slides-viewport {
            position: relative;
            width: 100%;
            height: 100vh;
            overflow: hidden;
        }
        .slide {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px;
            opacity: 0;
            visibility: hidden;
        }
        .slide.slide-active {
            opacity: 1;
            visibility: visible;
        }
        .slide-title {
            font-size: 48px;
            font-weight: 700;
            color: var(--text-heading);
            margin-bottom: 24px;
            text-align: center;
        }
        .slide-content {
            font-size: 20px;
            line-height: 1.8;
            max-width: 800px;
            text-align: center;
        }
        .slide-image {
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
            margin: 24px 0;
            border-radius: 8px;
        }
        .control-panel {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 24px;
            background: rgba(255,255,255,0.95);
            border-radius: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        .nav-dots {
            display: flex;
            gap: 8px;
        }
        .nav-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #ddd;
            cursor: pointer;
            transition: all 0.3s;
        }
        .nav-dot.active {
            background: var(--primary);
            transform: scale(1.2);
        }
        .slide-counter {
            font-size: 14px;
            color: #666;
        }
        .autoplay-toggle {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 24px;
        }
    </style>
</head>
<body class="{{STYLE_CLASS}}">
    <div class="slides-viewport transition-fade">
        {{SLIDES}}
    </div>
    <div class="control-panel">
        <button class="autoplay-toggle" onclick="autoPlay.toggle()" aria-label="自动播放">
            <span class="iconify" data-icon="ph:play-circle-bold"></span>
        </button>
        <div class="nav-dots">{{NAV_DOTS}}</div>
        <span class="slide-counter">1 / {{TOTAL}}</span>
    </div>
    <script>
        {{BASE_JS}}
        const engine = new SlideEngine();
        const autoPlay = new AutoPlayController(engine);
    </script>
</body>
</html>'''

    def generate(self, slides_data: Dict, images: Optional[Dict] = None, transition: str = "fade") -> str:
        """生成完整 HTML"""
        title = slides_data.get("title", "演示文稿")
        slides = slides_data.get("slides", [])
        images = images or {}

        # 提取图片映射 - 从 image_map 中获取（如果是 batch 模式的结果）
        image_map = images.get("image_map", images)  # 兼容两种格式

        # 生成幻灯片 HTML
        slides_html = []
        for i, slide in enumerate(slides):
            # 获取图片信息
            img_info = image_map.get(str(i), {})
            img_url = img_info.get("url") if isinstance(img_info, dict) else None
            img_attribution = img_info.get("attribution_html", "") if isinstance(img_info, dict) else ""

            slide_html = self._generate_slide(slide, i, img_url, img_attribution)
            slides_html.append(slide_html)

        # 生成导航点
        nav_dots = []
        for i in range(len(slides)):
            active = " active" if i == 0 else ""
            nav_dots.append(f'<div class="nav-dot{active}" onclick="engine.goTo({i})"></div>')

        # 构建上下文
        context = {
            "TITLE": title,
            "STYLE_CLASS": self.style_info["class"],
            "SLIDES": "\n".join(slides_html),
            "NAV_DOTS": "\n".join(nav_dots),
            "TOTAL": str(len(slides)),
            "TRANSITION": transition,
            "BASE_CSS": self.base_css,
            "ANIMATIONS_CSS": self.animations_css,
            "BASE_JS": self.base_js,
        }

        # 渲染模板
        engine = TemplateEngine(self.template)
        html = engine.render(context)

        # 后处理：确保 CSS 和 JS 被正确注入
        html = self._inject_assets(html, transition)

        return html

    def _generate_slide(self, slide: Dict, index: int, image_url: Optional[str] = None, attribution: str = "") -> str:
        """生成单个幻灯片 - 根据风格动态生成不同布局"""
        slide_type = slide.get("type", "content")
        title = slide.get("title", "")
        content = slide.get("content", "")
        bullets = slide.get("bullets", [])

        active = " slide-active" if index == 0 else ""
        style_name = self.style_info.get("name", "ted")

        # 根据风格和页面类型选择生成方法
        if slide_type == "cover":
            return self._generate_cover_slide(title, content, image_url, attribution, active, style_name)
        elif slide_type == "quote":
            return self._generate_quote_slide(content, image_url, attribution, active, style_name)
        elif slide_type == "ending":
            return self._generate_ending_slide(title, content, image_url, attribution, active, style_name)
        else:
            return self._generate_content_slide(title, content, bullets, image_url, attribution, active, style_name)

    def _generate_cover_slide(self, title: str, subtitle: str, image_url: Optional[str], attribution: str, active: str, style_name: str) -> str:
        """生成封面页 - 根据风格生成不同布局"""
        # TED/演讲风格：全屏背景图 + overlay
        if style_name in ["ted", "neo-tokyo", "dark-mode"]:
            if image_url:
                return f'''<div class="slide slide-cover{active}" style="background-image: url('{image_url}'); background-size: cover; background-position: center;">
    <div class="cover-overlay"></div>
    <div class="cover-content">
        <h1 class="slide-title">{title}</h1>
        <div class="divider"></div>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
    <div class="photo-attribution">{attribution}</div>
</div>'''
            else:
                return f'''<div class="slide slide-cover{active}">
    <div class="cover-content">
        <h1 class="slide-title">{title}</h1>
        <div class="divider"></div>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
</div>'''

        # Apple/极简风格：白色背景 + 居中标题
        elif style_name in ["apple", "muji"]:
            return f'''<div class="slide slide-cover{active}">
    <div class="cover-content">
        <h1 class="slide-title">{title}</h1>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
</div>'''

        # Kinfolk/Editorial：温暖背景 + 衬线字体
        elif style_name in ["kinfolk", "editorial", "newspaper"]:
            return f'''<div class="slide slide-cover{active}">
    <div class="cover-content">
        <p class="cover-tag">FEATURE</p>
        <h1 class="slide-title">{title}</h1>
        <div class="divider"></div>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
    {f'<div class="cover-image-wrapper"><img src="{image_url}" class="cover-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
</div>'''

        # 其他风格：默认布局
        else:
            return f'''<div class="slide slide-cover{active}">
    <div class="cover-content">
        <h1 class="slide-title">{title}</h1>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
    {f'<img src="{image_url}" class="slide-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

    def _generate_content_slide(self, title: str, content: str, bullets: List, image_url: Optional[str], attribution: str, active: str, style_name: str) -> str:
        """生成内容页 - 根据风格生成完全不同的布局"""
        bullets_html = ""
        if bullets:
            bullets_html = "<ul class='slide-bullets'>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"

        # ============ A1 TED 风格：全屏背景图 + 居中大文字 ============
        if style_name == "ted":
            if image_url:
                return f'''<div class="slide slide-content{active}" style="background-image: url('{image_url}'); background-size: cover; background-position: center;">
    <div class="ted-overlay"></div>
    <div class="ted-content">
        <h2 class="slide-title">{title}</h2>
        <div class="slide-text">{content}</div>
        {bullets_html}
    </div>
    <div class="photo-attribution photo-attribution-bottom">{attribution}</div>
</div>'''
            return f'''<div class="slide slide-content{active}">
    <div class="ted-content">
        <h2 class="slide-title">{title}</h2>
        <div class="slide-text">{content}</div>
        {bullets_html}
    </div>
</div>'''

        # ============ A2 Apple 风格：极简白底 + 超大留白 ============
        elif style_name == "apple":
            return f'''<div class="slide slide-content{active}">
    <div class="apple-wrapper">
        <h2 class="slide-title">{title}</h2>
        <p class="apple-text">{content}</p>
        {f'<div class="apple-image-wrapper"><img src="{image_url}" class="apple-image" alt=""></div>' if image_url else ''}
    </div>
</div>'''

        # ============ A3 Typical 风格：经典蓝白渐变 + 标准布局 ============
        elif style_name == "typical":
            return f'''<div class="slide slide-content{active}">
    <div class="typical-header">
        <h2 class="slide-title">{title}</h2>
        <div class="typical-line"></div>
    </div>
    <div class="typical-body">
        <div class="typical-content">
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        {f'<div class="typical-image-col"><img src="{image_url}" class="typical-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
    </div>
</div>'''

        # ============ A4 Gamma 风格：现代卡片 + 圆角阴影 ============
        elif style_name == "gamma":
            return f'''<div class="slide slide-content{active}">
    <div class="gamma-card">
        <div class="gamma-header">
            <h2 class="slide-title">{title}</h2>
        </div>
        <div class="gamma-body">
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        {f'<div class="gamma-image-wrapper"><img src="{image_url}" class="gamma-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
    </div>
</div>'''

        # ============ A5 Consulting 风格：深蓝金配色 + 数据卡片 ============
        elif style_name == "consulting":
            return f'''<div class="slide slide-content{active}">
    <div class="consulting-container">
        <div class="consulting-header">
            <h2 class="slide-title">{title}</h2>
            <div class="gold-line"></div>
        </div>
        <div class="consulting-grid">
            <div class="consulting-main">
                <p class="slide-text">{content}</p>
                {bullets_html}
            </div>
            {f'<div class="consulting-side"><img src="{image_url}" class="consulting-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="consulting-data"><div class="data-card"><span class="data-value">2026</span><span class="data-label">关键年份</span></div></div>'}
        </div>
    </div>
</div>'''

        # ============ B1 Editorial 风格：杂志分栏 + 衬线标题 ============
        elif style_name == "editorial":
            return f'''<div class="slide slide-content{active}">
    <div class="editorial-layout">
        <div class="editorial-main">
            <h2 class="slide-title">{title}</h2>
            <div class="editorial-divider"></div>
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        <div class="editorial-sidebar">
            {f'<img src="{image_url}" class="editorial-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else '<blockquote class="editorial-quote">"变革正在发生"</blockquote>'}
        </div>
    </div>
</div>'''

        # ============ B2 Swiss 风格：严格网格 + 红色色带 ============
        elif style_name == "swiss":
            return f'''<div class="slide slide-content{active}">
    <div class="swiss-red-bar"></div>
    <div class="swiss-grid">
        <div class="swiss-left">
            <h2 class="slide-title">{title}</h2>
        </div>
        <div class="swiss-right">
            <p class="slide-text">{content}</p>
            {bullets_html}
            {f'<img src="{image_url}" class="swiss-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
        </div>
    </div>
</div>'''

        # ============ B3 Newspaper 风格：报纸版式 + 多栏 ============
        elif style_name == "newspaper":
            return f'''<div class="slide slide-content{active}">
    <div class="newspaper-layout">
        <h2 class="newspaper-headline">{title}</h2>
        <div class="newspaper-columns">
            <div class="newspaper-column">
                <p class="slide-text">{content}</p>
                {bullets_html}
            </div>
            {f'<div class="newspaper-column newspaper-image-col"><img src="{image_url}" class="newspaper-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
        </div>
    </div>
</div>'''

        # ============ C1 Bauhaus 风格：几何色块 + 三原色 ============
        elif style_name == "bauhaus":
            return f'''<div class="slide slide-content{active}">
    <div class="bauhaus-container">
        <div class="bauhaus-red-block"></div>
        <div class="bauhaus-content">
            <h2 class="slide-title">{title}</h2>
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        {f'<div class="bauhaus-image-block"><img src="{image_url}" class="bauhaus-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="bauhaus-yellow-block"></div>'}
    </div>
</div>'''

        # ============ C2 Kinfolk 风格：温暖米色 + 胶片质感 ============
        elif style_name == "kinfolk":
            return f'''<div class="slide slide-content{active}">
    <div class="content-grid">
        <div class="main-column">
            <h2 class="slide-title">{title}</h2>
            <div class="slide-text">{content}</div>
            {bullets_html}
        </div>
        {f'<div class="side-column"><img src="{image_url}" class="side-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="side-column"><div class="pull-quote">"变革正在发生"</div></div>'}
    </div>
</div>'''

        # ============ C3 Muji 风格：白灰极简 + 日式简约 ============
        elif style_name == "muji":
            return f'''<div class="slide slide-content{active}">
    <div class="muji-container">
        <h2 class="slide-title">{title}</h2>
        <div class="muji-line"></div>
        <p class="slide-text">{content}</p>
        {bullets_html}
        {f'<div class="muji-image-wrapper"><img src="{image_url}" class="muji-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
    </div>
</div>'''

        # ============ C4 Brutalist 风格：粗边框 + 高对比 ============
        elif style_name == "brutalist":
            return f'''<div class="slide slide-content{active}">
    <div class="brutalist-box">
        <div class="brutalist-header-bar">
            <h2 class="slide-title">{title}</h2>
        </div>
        <div class="brutalist-content">
            <p class="slide-text">{content}</p>
            {bullets_html}
            {f'<div class="brutalist-image-wrapper"><img src="{image_url}" class="brutalist-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
        </div>
    </div>
</div>'''

        # ============ D1 Neo-Tokyo 风格：深黑底 + 霓虹色 ============
        elif style_name == "neo-tokyo":
            return f'''<div class="slide slide-content{active}">
    <div class="neo-grid">
        <div class="neo-left">
            <h2 class="slide-title">{title}</h2>
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        {f'<div class="neo-right"><img src="{image_url}" class="neo-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="neo-decorative"><div class="glitch-text">2026</div></div>'}
    </div>
</div>'''

        # ============ D2 Dark-Mode 风格：深灰底 + 蓝紫渐变 ============
        elif style_name == "dark-mode":
            return f'''<div class="slide slide-content{active}">
    <div class="dark-card">
        <div class="dark-header">
            <h2 class="slide-title">{title}</h2>
            <div class="gradient-line"></div>
        </div>
        <div class="dark-body">
            <p class="slide-text">{content}</p>
            {bullets_html}
        </div>
        {f'<div class="dark-image-wrapper"><img src="{image_url}" class="dark-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else ''}
    </div>
</div>'''

        # ============ D3 Red-Black-Tech 风格：红黑白科技 ============
        elif style_name == "red-black-tech":
            return f'''<div class="slide slide-content{active}">
    <div class="tech-layout">
        <div class="tech-red-accent"></div>
        <div class="tech-content">
            <h2 class="slide-title">{title}</h2>
            <div class="tech-underline"></div>
            <p class="slide-text">{content}</p>
            {bullets_html}
            {f'<div class="tech-image-wrapper"><img src="{image_url}" class="tech-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="tech-diagram"><div class="circuit-line"></div></div>'}
        </div>
    </div>
</div>'''

        # ============ E1 Cartoon 2.5D 风格：扁平阴影 + 多彩圆润 ============
        elif style_name == "cartoon":
            return f'''<div class="slide slide-content{active}">
    <div class="cartoon-container">
        <div class="cartoon-header">
            <h2 class="slide-title">{title}</h2>
        </div>
        <div class="cartoon-body">
            <div class="cartoon-text-box">
                <p class="slide-text">{content}</p>
                {bullets_html}
            </div>
            {f'<div class="cartoon-image-box"><img src="{image_url}" class="cartoon-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="cartoon-icon-box"><span class="iconify cartoon-icon" data-icon="ph:rocket-launch-duotone"></span></div>'}
        </div>
    </div>
</div>'''

        # ============ E2 Education 风格：色彩编码 + 互动元素 ============
        elif style_name == "education":
            return f'''<div class="slide slide-content{active}">
    <div class="edu-container">
        <div class="edu-header">
            <span class="edu-badge">知识点</span>
            <h2 class="slide-title">{title}</h2>
        </div>
        <div class="edu-content">
            <div class="edu-highlight-box">
                <p class="slide-text">{content}</p>
            </div>
            {bullets_html}
            {f'<div class="edu-image-wrapper"><img src="{image_url}" class="edu-image" alt=""><div class="photo-attribution">{attribution}</div></div>' if image_url else '<div class="edu-tip"><span class="iconify" data-icon="ph:lightbulb-duotone"></span> 记住这个概念</div>'}
        </div>
    </div>
</div>'''

        # ============ 默认布局 ============
        else:
            return f'''<div class="slide slide-content{active}">
    <h2 class="slide-title">{title}</h2>
    <div class="slide-text">{content}</div>
    {bullets_html}
    {f'<img src="{image_url}" class="slide-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

    def _generate_quote_slide(self, content: str, image_url: Optional[str], attribution: str, active: str, style_name: str) -> str:
        """生成金句页 - 根据风格生成不同布局"""
        # TED/科技风格：背景图 + 大引用
        if style_name in ["ted", "neo-tokyo", "dark-mode"]:
            return f'''<div class="slide slide-quote{active}" {f'style="background-image: url(\'{image_url}\'); background-size: cover; background-position: center;"' if image_url else ''}>
    <div class="quote-overlay"></div>
    <div class="quote-container">
        <div class="quote-mark">"</div>
        <blockquote class="quote-text">{content}</blockquote>
    </div>
    {f'<div class="photo-attribution photo-attribution-bottom">{attribution}</div>' if image_url else ''}
</div>'''

        # Editorial/Kinfolk：居中引用框
        elif style_name in ["editorial", "kinfolk", "newspaper", "swiss"]:
            return f'''<div class="slide slide-quote{active}">
    <div class="quote-box">
        <blockquote class="quote-text">{content}</blockquote>
    </div>
    {f'<img src="{image_url}" class="quote-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

        # 默认
        else:
            return f'''<div class="slide slide-quote{active}" {f'style="background-image: url(\'{image_url}\'); background-size: cover; background-position: center;"' if image_url else ''}>
    <blockquote class="quote-text">{content}</blockquote>
    {f'<div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

    def _generate_ending_slide(self, title: str, content: str, image_url: Optional[str], attribution: str, active: str, style_name: str) -> str:
        """生成结尾页"""
        # TED 风格：彩色背景
        if style_name == "ted":
            return f'''<div class="slide slide-ending{active}">
    <h1 class="slide-title">{title}</h1>
    <p class="slide-subtitle">{content}</p>
    {f'<img src="{image_url}" class="slide-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

        # Apple/极简：白色背景
        elif style_name in ["apple", "muji"]:
            return f'''<div class="slide slide-ending{active}">
    <div class="ending-content">
        <h1 class="slide-title">{title}</h1>
        <div class="thin-line"></div>
        <p class="slide-subtitle">{content}</p>
    </div>
</div>'''

        # 默认
        else:
            return f'''<div class="slide slide-ending{active}">
    <h1 class="slide-title">{title}</h1>
    <p class="slide-subtitle">{content}</p>
    {f'<img src="{image_url}" class="slide-image" alt=""><div class="photo-attribution">{attribution}</div>' if image_url else ''}
</div>'''

    def _inject_assets(self, html: str, transition: str) -> str:
        """注入 CSS 和 JS 资源"""
        # 如果模板中没有 {{BASE_CSS}} 等占位符，需要手动注入

        # 确保有基础 CSS 变量
        if "</head>" in html and "<style>" not in html:
            css_inject = f"<style>\n{self.base_css}\n{self.animations_css}\n</style>\n</head>"
            html = html.replace("</head>", css_inject)

        # 确保有基础 JS
        if "</body>" in html and "SlideEngine" not in html:
            js_inject = f'''<script>
{self.base_js}
const engine = new SlideEngine({{ defaultTransition: '{transition}' }});
const autoPlay = new AutoPlayController(engine);
</script>
</body>'''
            html = html.replace("</body>", js_inject)

        # 设置初始过渡类
        html = html.replace('class="slides-viewport"', f'class="slides-viewport transition-{transition}"')

        return html


# ============================================================================
# LLM 智能设计 HTML 生成器
# ============================================================================
class LLMHTMLGenerator:
    """使用 LLM 设计规范生成 HTML"""

    def __init__(self, design_spec: Dict):
        self.design = LLMDesignGenerator(design_spec)
        self.base_js = self._load_base_js()
        self.animations_css = self._load_animations_css()

    def _load_base_js(self) -> str:
        """加载基础 JS 引擎"""
        js_path = BASE_DIR / "_slide_engine.js"
        if js_path.exists():
            return js_path.read_text(encoding="utf-8")
        return ""

    def _load_animations_css(self) -> str:
        """加载动画 CSS"""
        css_path = BASE_DIR / "_animations.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""

    def generate(self, slides_data: Dict, images: Optional[Dict] = None) -> str:
        """生成完整 HTML"""
        title = slides_data.get("title", "演示文稿")
        slides = slides_data.get("slides", [])
        images = images or {}
        image_map = images.get("image_map", images)

        # 生成幻灯片 HTML
        slides_html = []
        for i, slide in enumerate(slides):
            img_info = image_map.get(str(i), {})
            img_url = img_info.get("url") if isinstance(img_info, dict) else None
            img_attribution = img_info.get("attribution_html", "") if isinstance(img_info, dict) else ""
            slide_html = self._generate_slide(slide, i, img_url, img_attribution)
            slides_html.append(slide_html)

        # 生成导航点
        nav_dots = []
        for i in range(len(slides)):
            active = " active" if i == 0 else ""
            nav_dots.append(f'<div class="nav-dot{active}" onclick="engine.goTo({i})"></div>')

        # 获取动画按钮
        transition = self.design.transition
        animation_buttons = self._generate_animation_buttons(transition)

        # 生成完整 HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    {self.design.get_google_fonts_link()}
    <script src="https://code.iconify.design/3/3.1.1/iconify.min.js"></script>
    <style>
        {self.design.get_font_family_style()}
        {self.design.generate_full_css(self.animations_css)}
    </style>
</head>
<body>
    <div class="slides-viewport transition-{transition}">
        {"".join(slides_html)}
    </div>

    <div class="control-panel">
        <button class="autoplay-toggle" onclick="autoPlay.toggle()" aria-label="自动播放">
            <span class="iconify" data-icon="ph:play-circle-bold"></span>
        </button>
        <div class="nav-dots">
            {"".join(nav_dots)}
        </div>
        <span class="slide-counter">1 / {len(slides)}</span>
        <div class="style-control">
            {animation_buttons}
        </div>
    </div>

    <script>
        {self.base_js}
        const engine = new SlideEngine({{ defaultTransition: '{transition}' }});
        const autoPlay = new AutoPlayController(engine, {{ interval: 7000, hideAfterStart: true }});
    </script>
</body>
</html>'''
        return html

    def _generate_slide(self, slide: Dict, index: int, image_url: Optional[str], attribution: str) -> str:
        """生成单个幻灯片"""
        slide_type = slide.get("type", "content")
        title = slide.get("title", "")
        content = slide.get("content", "")

        active = " slide-active" if index == 0 else ""

        if slide_type == "cover":
            return self._generate_cover(title, content, image_url, attribution, active)
        elif slide_type == "quote":
            return self._generate_quote(content, image_url, attribution, active)
        elif slide_type == "ending":
            return self._generate_ending(title, content, image_url, attribution, active)
        else:
            return self._generate_content(title, content, image_url, attribution, active)

    def _generate_cover(self, title: str, subtitle: str, image_url: Optional[str], attribution: str, active: str) -> str:
        """生成封面页"""
        return f'''<div class="slide slide-cover{active}">
    <div class="cover-content">
        <h1 class="slide-title">{title}</h1>
        <div class="divider"></div>
        <p class="slide-subtitle">{subtitle}</p>
    </div>
</div>'''

    def _generate_content(self, title: str, content: str, image_url: Optional[str], attribution: str, active: str) -> str:
        """生成内容页"""
        img_section = ""
        if image_url:
            img_section = f'''<div class="side-column">
        <img src="{image_url}" class="side-image" alt="">
        <div class="photo-attribution">{attribution}</div>
    </div>'''

        return f'''<div class="slide slide-content{active}">
    <div class="content-grid">
        <div class="main-column">
            <h2 class="slide-title">{title}</h2>
            <div class="slide-text">{content}</div>
        </div>
        {img_section if image_url else '<div class="side-column"><div class="pull-quote">"变革正在发生"</div></div>'}
    </div>
</div>'''

    def _generate_quote(self, content: str, image_url: Optional[str], attribution: str, active: str) -> str:
        """生成金句页"""
        img_section = ""
        if image_url:
            img_section = f'''<img src="{image_url}" class="quote-image" alt="">
    <div class="photo-attribution">{attribution}</div>'''

        return f'''<div class="slide slide-quote{active}">
    <div class="quote-box">
        <blockquote class="quote-text">{content}</blockquote>
    </div>
    {img_section}
</div>'''

    def _generate_ending(self, title: str, subtitle: str, image_url: Optional[str], attribution: str, active: str) -> str:
        """生成结尾页"""
        img_section = ""
        if image_url:
            img_section = f'''<img src="{image_url}" class="slide-image" alt="">
    <div class="photo-attribution">{attribution}</div>'''

        return f'''<div class="slide slide-ending{active}">
    <h1 class="slide-title">{title}</h1>
    <p class="slide-subtitle">{subtitle}</p>
    {img_section}
</div>'''

    def _generate_animation_buttons(self, active_transition: str) -> str:
        """生成动画切换按钮"""
        transitions = ["fade", "slide", "cinematic", "zoom"]
        buttons = []
        for t in transitions:
            active = " active" if t == active_transition else ""
            buttons.append(f'<button class="style-btn{active}" data-style="{t}" onclick="engine.setTransition(\'{t}\')">{t.capitalize()}</button>')
        return "".join(buttons)


# ============================================================================
# 命令行接口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="HTML PPT Generator - 将 slides.json 生成精美的 HTML 演示文稿",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s slides.json --style A1 --output presentation.html
  %(prog)s slides.json --style B1 --images images.json -o out.html
  %(prog)s slides.json --style D1 --transition cinematic

支持的风格:
  A1-A5: TED, Apple, Typical, Gamma, Consulting
  B1-B3: Editorial, Swiss, Newspaper
  C1-C4: Bauhaus, Kinfolk, Muji, Brutalist
  D1-D3: Neo-Tokyo, Dark-Mode, Red-Black-Tech
  E1-E2: Cartoon-2.5D, Education

动画类型:
  fade, slide, cinematic, cut, flip, zoom

LLM 设计模式:
  使用 --llm-css design.json 可以使用 LLM 生成的自定义设计
  design.json 格式见 SKILL.md
        """
    )

    parser.add_argument("slides", help="slides JSON 文件路径")
    parser.add_argument("--style", "-s", default="A1", help="风格代码 (默认: A1，使用本地模板)")
    parser.add_argument("--llm-css", "-l", help="LLM 生成的设计 JSON 文件（优先于 --style）")
    parser.add_argument("--output", "-o", help="输出 HTML 文件路径")
    parser.add_argument("--images", "-i", help="图片映射 JSON 文件")
    parser.add_argument("--transition", "-t", default="fade",
                       choices=["fade", "slide", "cinematic", "cut", "flip", "zoom"],
                       help="翻页动画类型 (默认: fade)")

    args = parser.parse_args()

    # 读取 slides JSON
    slides_path = Path(args.slides)
    if not slides_path.exists():
        print(f"错误: 文件不存在 - {slides_path}")
        return 1

    with open(slides_path, "r", encoding="utf-8") as f:
        slides_data = json.load(f)

    # 读取图片映射（如果提供）
    images = {}
    if args.images:
        images_path = Path(args.images)
        if images_path.exists():
            with open(images_path, "r", encoding="utf-8") as f:
                images = json.load(f)

    # 优先使用 LLM 设计
    if args.llm_css:
        llm_css_path = Path(args.llm_css)
        if llm_css_path.exists():
            with open(llm_css_path, "r", encoding="utf-8") as f:
                design_spec = json.load(f)

            # 使用 LLM 设计生成
            generator = LLMHTMLGenerator(design_spec)
            html = generator.generate(slides_data, images)
            print(f"✓ 使用 LLM 智能设计: {design_spec.get('concept', '自定义设计')}")
        else:
            print(f"警告: LLM 设计文件不存在 - {llm_css_path}，回退到预设模板")
            generator = HTMLGenerator(args.style)
            html = generator.generate(slides_data, images, args.transition)
    else:
        # 使用预设模板
        generator = HTMLGenerator(args.style)
        html = generator.generate(slides_data, images, args.transition)

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(html, encoding="utf-8")
        print(f"✓ 已生成: {output_path.absolute()}")
    else:
        print(html)

    return 0


if __name__ == "__main__":
    exit(main())
