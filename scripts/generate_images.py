#!/usr/bin/env python3
"""
AI 配图生成模块 v3.0
Generate images for PPT slides using ZMark API or Unsplash
Supports 16+ PPT styles with quality control
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Unsplash support
try:
    from fetch_unsplash import batch_fetch_for_slides as unsplash_batch
    HAS_UNSPLASH = True
except ImportError:
    HAS_UNSPLASH = False


# API 配置
ZENMUX_API_KEY = os.environ.get("ZENMUX_API_KEY")
BASE_URL = "https://zenmux.ai/api/vertex-ai"
MODEL = "google/gemini-3-pro-image-preview"
IMAGE_SIZE = "1024x1024"


def check_api_key():
    """检查 API Key 是否已配置"""
    if not ZENMUX_API_KEY:
        print("=" * 60, file=sys.stderr)
        print("错误: 未配置 ZENMUX_API_KEY 环境变量", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("", file=sys.stderr)
        print("申请方法:", file=sys.stderr)
        print("  1. 访问 https://zenmux.ai", file=sys.stderr)
        print("  2. 注册账号并登录", file=sys.stderr)
        print("  3. 在控制台获取 API Key", file=sys.stderr)
        print("  4. 设置环境变量:", file=sys.stderr)
        print("     export ZENMUX_API_KEY='your-api-key'", file=sys.stderr)
        print("", file=sys.stderr)
        print("提示: 也可使用 --api-key 参数直接传入", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return False
    return True

# Image source types
IMAGE_SOURCE_UNSPLASH = "unsplash"   # I2, I3
IMAGE_SOURCE_AI = "ai"               # I4, I5, I6, I7
IMAGE_SOURCE_NONE = "none"           # I1

# Image style to source mapping
IMAGE_STYLE_SOURCE = {
    "I1": IMAGE_SOURCE_NONE,
    "I2": IMAGE_SOURCE_UNSPLASH,  # Editorial Photo
    "I3": IMAGE_SOURCE_UNSPLASH,  # Kinfolk
    "I4": IMAGE_SOURCE_AI,        # 红黑白科技
    "I5": IMAGE_SOURCE_AI,        # 卡通 2.5D
    "I6": IMAGE_SOURCE_AI,        # 3D 渲染
    "I7": IMAGE_SOURCE_AI,        # 抽象艺术
}

# Image style to AI style mapping
IMAGE_STYLE_TO_AI = {
    "I4": "red_black_white",
    "I5": "cartoon_2_5d",
    "I6": "3d_render",
    "I7": "abstract_art",
}

# Image style to Unsplash style mapping
IMAGE_STYLE_TO_UNSPLASH = {
    "I2": "editorial",
    "I3": "kinfolk",
}


# ============================================================================
# 风格提示词系统 v3.0
# ============================================================================

# 基础风格提示词
STYLE_PROMPTS = {
    # 卡通 2.5D 风格
    "cartoon_2_5d": """Cartoon 2.5D isometric illustration, vibrant and friendly style.

Character design:
- Q-version characters with big heads and small bodies (1:2 ratio)
- Rounded shapes, soft edges, friendly expressions
- Simplified facial features (dot eyes, simple smiles)
- Expressive poses and body language

Visual elements:
- Isometric platforms at different heights
- Floating 3D icons and decorative elements
- Soft shadows, gentle depth
- Stars, sparkles, bubbles as decorations

Color palette (vibrant but harmonious):
- Primary: Bright Blue #4A90E2
- Secondary: Purple #9B59B6
- Accent: Orange #F39C12, Yellow #FFD93D
- Background: White to light blue gradient

Style requirements:
Isometric 2.5D perspective, friendly and approachable, rounded shapes, soft shadows, vibrant colors, professional yet playful aesthetic, optimistic and motivating mood, clean composition with good visual hierarchy.""",

    # 红黑白科技风
    "red_black_white": """Isometric illustration in red, black, and white color scheme, modern tech style, clean geometric design.

Visual elements:
- Geometric shapes (cubes, rectangles, platforms)
- Clean lines, precise angles
- Simplified silhouette figures (minimal detail)
- Circuit-like connection lines in red

Color palette (strict):
- Primary red: #E63946 (for emphasis, highlights, connections)
- Black: #000000 (for main structures, figures)
- White: #FFFFFF (for background, negative space)
- Gray: #CCCCCC (only for secondary elements, <10%)

Style requirements:
Isometric 2.5D perspective, clean lines, geometric shapes, modern tech aesthetic, circuit-like connection lines in red, subtle shadows for depth, white or light gray background, high contrast, professional grade output, sharp details, no watermarks, no text overlays.""",

    # Editorial 杂志风
    "editorial": """Black and white magazine photography, minimalist, high contrast, lots of negative space, documentary style, clean composition.

Visual style:
- High contrast black and white photography
- Editorial magazine aesthetic
- Clean lines, sophisticated composition
- Natural lighting, authentic feel
- Documentary style,纪实感

Quality requirements:
Pure black and white photography, no watermarks, no text overlays, no artifacts, magazine quality output, sharp details, clean composition.""",

    # Bauhaus 包豪斯
    "bauhaus": """Geometric abstract art in Bauhaus style, primary colors red blue yellow, grid-based composition, constructivist style.

Visual elements:
- Bold geometric shapes (squares, circles, rectangles)
- Primary colors: Red #E63B2E, Blue #2B4FA2, Yellow #F5C300
- Black #1A1A1A for contrast
- Grid-based layout, structured composition
- Minimal elements, clean lines

Style requirements:
Geometric abstraction, bold shapes, primary colors,理性与感性的平衡, clean professional output.""",

    # Muji 无印
    "muji": """Japanese minimalist aesthetic, natural textures paper and wood, soft neutral colors beige gray brown, calm and clean composition, warm lighting.

Visual elements:
- Natural textures (paper, wood, cotton)
- Soft neutral colors
- Minimal composition
- Warm, gentle lighting
- 大量留白

Color palette:
- Background: Beige #F7F5F0 (生成纸)
- Accent: Brown #8B7355 (枯叶棕)
- Text: Gray #5C5C5C
- Border: #E5E0D8 (棉麻灰)

Style requirements:
纯净、呼吸、本质, calm and warm aesthetic.""",

    # Swiss 瑞士国际
    "swiss": """Swiss international style, grid-based layout, bold typography elements, red accent color on white, structured and orderly, data visualization aesthetic.

Visual elements:
- Strict grid system
- Bold typography (Helvetica style)
- Red accent color: #D0021B
- Black #2C2C2C for text
- White background
- Data visualization elements

Style requirements:
Structured, orderly, information is beauty, precise typography, grid-based composition.""",

    # Kinfolk 生活方式
    "kinfolk": """Morandi color palette, soft pastel tones, natural window light, lifestyle photography mood, gentle and warm, film photography aesthetic, muted colors.

Color palette (Morandi tones):
- Soft pink: #D4AAA0
- Moss green: #8FA387
- Caramel brown: #9B7B5E
- Warm beige background

Style requirements:
温柔、从容、有质感的安静, gentle and warm mood, film photography aesthetic, muted colors, soft lighting.""",

    # Neo-Tokyo 新东京
    "neo_tokyo": """Cyberpunk aesthetic, neon accents on dark background, pixel art elements, futuristic Tokyo streets, digital glitch effects.

Color palette:
- Background: Black #0A0A0F (near pure black)
- Neon pink: #FF2D6B
- Matrix green: #39FF14
- Cold blue: #00B4D8
- Grid lines: rgba(255,255,255,0.04)

Style requirements:
未来、混沌的秩序、东方赛博, futuristic aesthetic, digital elements, pixel art details.""",

    # Brutalist 粗野主义
    "brutalist": """Brutalist design, raw concrete texture, bold black typography, high contrast, minimalist composition, architectural elements.

Color palette:
- Black: #000000
- White: #FFFFFF
- Accent red: #FF3D00

Style requirements:
反叛、张力、不舒服的美, bold typography, raw aesthetic, high contrast.""",

    # 3D 渲染风格
    "3d_render": """High quality 3D rendered illustration, soft studio lighting, glossy and matte materials, modern product design aesthetic.

Visual elements:
- Smooth 3D rendered objects with realistic materials
- Soft shadows and ambient occlusion
- Clean studio background with gradient
- Geometric and organic shapes combined

Color palette:
- Soft pastels or vibrant gradients
- Studio-grade lighting
- Clean white or colored backgrounds

Style requirements:
Professional 3D rendering, clean composition, modern aesthetic, no watermarks, no text overlays, sharp details, product-quality output.""",

    # 抽象艺术风格
    "abstract_art": """Abstract artistic illustration, bold expressive brushstrokes, modern art aesthetic, creative composition.

Visual elements:
- Abstract shapes and forms
- Expressive color fields
- Dynamic composition with movement
- Mixed media texture feel

Color palette:
- Bold, contrasting colors
- Rich, saturated hues
- Unexpected color combinations

Style requirements:
Gallery-quality abstract art, expressive and emotional, clean output, no watermarks, no text overlays, high resolution."""
}

# 场景关键词映射（用于提取视觉主题）
SCENE_KEYWORDS = {
    # 科技/技术类
    "科技": "technology, digital interface, circuit board, data visualization, futuristic elements",
    "技术": "technology, innovation, digital tools, technical equipment",
    "AI": "artificial intelligence, neural network, AI brain, machine learning, digital intelligence",
    "数据": "data visualization, charts, graphs, numbers, analytics dashboard",
    "算法": "algorithm flowchart, process diagram, logical structure",
    "编程": "code editor, programming interface, syntax highlighting, development tools",
    "软件": "software interface, app design, user experience, digital product",
    "互联网": "network connection, web infrastructure, cloud computing, connectivity",
    "云计算": "cloud infrastructure, server racks, data centers, network topology",
    "安全": "security shield, lock icon, protection, cybersecurity elements",

    # 教育/学习类
    "学习": "learning journey, books, notebook, student character, education scene",
    "教育": "classroom, teaching, knowledge sharing, academic environment",
    "成长": "growth chart, upward arrow, progress ladder, development stages",
    "知识": "books, library, wisdom, information architecture",
    "培训": "training workshop, seminar, skill development, professional growth",
    "课程": "course curriculum, learning modules, educational content",
    "学校": "school building, campus, academic institution, education",
    "研究": "research lab, microscope, data analysis, investigation",
    "考试": "test paper, exam preparation, study materials, assessment",
    "毕业": "graduation cap, diploma, certificate, achievement celebration",

    # 职业/工作类
    "职业": "career path, professional growth, job ladder, workplace",
    "工作": "office desk, workspace, productivity tools, professional environment",
    "团队": "team collaboration, people working together, group dynamics",
    "会议": "meeting room, presentation, discussion, professional gathering",
    "项目": "project timeline, task management, workflow, deliverables",
    "目标": "target icon, goal achievement, success metrics, KPI dashboard",
    "成果": "trophy, award, success celebration, achievement",
    "效率": "productivity tools, time management, optimization, speed",
    "创新": "lightbulb, creative idea, innovation, breakthrough thinking",
    "策略": "chess game, strategic planning, roadmap, decision making",

    # 产品/营销类
    "产品": "product design, packaging, merchandise, showcase",
    "营销": "marketing campaign, advertising, promotion, brand awareness",
    "用户": "user personas, customer journey, user experience, people",
    "服务": "service delivery, customer support, help desk, assistance",
    "品牌": "brand identity, logo, visual recognition, brand values",
    "销售": "sales chart, growth graph, revenue, business metrics",
    "客户": "customer satisfaction, testimonials, reviews, feedback",
    "市场": "market analysis, competition landscape, trends, insights",
    "推广": "promotional materials, advertising campaign, marketing channels",
    "转化": "conversion funnel, sales process, customer journey, ROI",

    # 生活方式类
    "生活": "lifestyle scene, daily life, home environment, personal space",
    "旅行": "travel destination, map, luggage, adventure, exploration",
    "美食": "food presentation, dining scene, culinary experience, ingredients",
    "健康": "wellness, fitness, medical care, health tracking",
    "运动": "sports equipment, fitness activity, exercise, gym scene",
    "休闲": "leisure activity, relaxation, entertainment, hobby",
    "家居": "home interior, furniture, living space, domestic scene",
    "时尚": "fashion, clothing style, accessories, trend",
    "社交": "social interaction, connection, networking, community",
    "娱乐": "entertainment, games, movies, music, fun activities",

    # 抽象概念类
    "时间": "clock, calendar, timeline, hourglass, temporal elements",
    "未来": "futuristic scene, horizon, sunrise, possibilities, forward-looking",
    "问题": "puzzle pieces, question mark, problem solving, challenge",
    "解决方案": "solution, key, unlock, breakthrough, answer",
    "变化": "transformation, metamorphosis, evolution, transition",
    "平衡": "balance scale, harmony, equilibrium, stability",
    "连接": "network nodes, links, bridges, connections",
    "自由": "open sky, birds flying, liberation, breaking chains",
    "欲望": "desire, aspiration, ambition, goal-seeking, motivation",
    "选择": "fork in road, decision tree, options, pathways",
}

# 抽象概念视觉映射
ABSTRACT_CONCEPTS = {
    "自由": "open landscape, birds flying, breaking chains, expansive sky",
    "欲望": "reaching hand, burning flame, upward movement, aspiration",
    "危机": "storm clouds, warning signs, tension, dramatic lighting",
    "突破": "breaking through barriers, light emerging, upward trajectory",
    "协作": "interconnected figures, joining hands, network, unity",
    "成长": "growing plant, upward stairs, evolution, progression",
    "创新": "lightbulb, spark, creative explosion, new horizons",
    "效率": "clock, gears turning, streamlined flow, optimization",
    "安全": "shield, protection, fortress, secure boundary",
    "连接": "bridge, network nodes, linking lines, unity"
}


def extract_visual_subject(slide_title: str, slide_content: str, slide_type: str) -> str:
    """
    从幻灯片内容中提取视觉主题
    """
    content = slide_title + " " + slide_content

    # 首先检查抽象概念
    for concept, visual in ABSTRACT_CONCEPTS.items():
        if concept in content:
            return visual

    # 然后检查场景关键词
    for keyword, visual in SCENE_KEYWORDS.items():
        if keyword in content:
            return visual

    # 根据页面类型返回默认主题
    type_defaults = {
        "cover": "hero scene, main theme visualization, establishing shot",
        "quote": "atmospheric scene, emotional mood, contemplative moment",
        "ending": "conclusion scene, forward-looking, hopeful mood",
        "content": "informational scene, knowledge sharing, explanation",
    }

    return type_defaults.get(slide_type, "abstract geometric composition, clean and minimal")


def generate_image_prompt(slide_data: Dict, style: str) -> str:
    """
    根据幻灯片内容和风格生成配图提示词
    """
    base_style = STYLE_PROMPTS.get(style, STYLE_PROMPTS["editorial"])
    title = slide_data.get("title", "")
    content = slide_data.get("content", "")
    slide_type = slide_data.get("type", "content")

    # 提取视觉主题
    subject = extract_visual_subject(title, content, slide_type)

    # 根据页面类型调整提示词
    type_prompts = {
        "cover": f"Cover page design for: {title}\nVisual theme: {subject}\nMain title should be the focal point.",
        "quote": f"Inspirational quote page\nTheme: {subject}\nAtmospheric mood, emotional resonance.\nQuote text (not in image): {content[:50]}...",
        "ending": f"Closing page design\nTheme: {subject}\nForward-looking, hopeful, conclusion mood.",
        "content": f"Informational content page\nTopic: {title}\nVisual elements: {subject}"
    }

    type_instruction = type_prompts.get(slide_type, f"Content page about: {title}")

    # 组合完整提示词
    full_prompt = f"""{base_style}

{type_instruction}

Visual subject to depict: {subject}

Quality requirements:
- Pure illustration/photography output
- No watermarks, no text overlays on image
- Clean background appropriate to style
- High quality, sharp details
- No artifacts or noise
- Professional grade output"""

    return full_prompt


def needs_image(slide_type: str, content_length: int = 0, page_position: int = 0, total_pages: int = 1) -> bool:
    """
    判断幻灯片是否需要配图（v2.4 更严格规则）

    封面、金句、结尾必须配图
    内容页根据长度决定
    数据页、图表页不配图
    """
    # 必须配图的页面类型
    must_have_images = ['cover', 'quote', 'ending']

    # 不配图的页面类型
    no_image_types = ['data', 'chart', 'timeline']

    if slide_type in must_have_images:
        return True  # 封面、金句、结尾必须有配图

    if slide_type in no_image_types:
        return False  # 数据页、图表页不配图

    # 内容页根据长度决定
    if slide_type == 'content':
        if content_length > 300:
            return True  # 长内容需要配图
        if page_position in [0, 1] or page_position >= total_pages - 2:
            return True  # 前两页和最后两页内容页建议配图
        return False  # 短内容可以不配图

    return False


def generate_image(prompt: str, output_path: str, client) -> bool:
    """
    调用 ZMark API 生成图片
    """
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                image.save(output_path)
                print(f"✓ Image saved: {output_path}", file=sys.stderr)
                return True

        print(f"✗ No image generated", file=sys.stderr)
        return False

    except Exception as e:
        print(f"✗ Error generating image: {e}", file=sys.stderr)
        return False


def batch_generate(
    slides: List[Dict],
    style: str,
    output_dir: str,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    批量生成配图

    Returns:
        Dict mapping slide index to image path
    """
    # 检查 API Key
    effective_key = api_key or ZENMUX_API_KEY
    if not effective_key:
        if not check_api_key():
            return {}

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 初始化客户端
    client = genai.Client(
        api_key=effective_key,
        vertexai=True,
        http_options=types.HttpOptions(api_version='v1', base_url=BASE_URL)
    )

    image_map = {}
    total_pages = len(slides)

    print(f"\n=== 配图生成开始 ===", file=sys.stderr)
    print(f"风格: {style}", file=sys.stderr)
    print(f"幻灯片数量: {total_pages}", file=sys.stderr)

    for i, slide in enumerate(slides):
        slide_type = slide.get("type", "content")
        content_length = len(slide.get("content", ""))
        title = slide.get("title", "Untitled")

        # 判断是否需要配图
        if not needs_image(slide_type, content_length, i, total_pages):
            print(f"  [{i+1}/{total_pages}] Skip: {title}", file=sys.stderr)
            continue

        # 生成提示词
        prompt = generate_image_prompt(slide, style)

        # 输出路径
        image_file = output_path / f"slide_{i+1:03d}.png"

        # 生成图片
        print(f"  [{i+1}/{total_pages}] Generate: {title}", file=sys.stderr)
        print(f"    Style: {style}", file=sys.stderr)

        if generate_image(prompt, str(image_file), client):
            image_map[str(i)] = str(image_file)

    print(f"\n=== 配图生成完成 ===", file=sys.stderr)
    print(f"共生成 {len(image_map)} 张图片", file=sys.stderr)

    return image_map


def main():
    parser = argparse.ArgumentParser(description='配图生成工具 v3.0 (AI + Unsplash)')
    parser.add_argument('input', help='输入 JSON 文件（slides 数据）')
    parser.add_argument('--style', default='editorial',
                       choices=list(STYLE_PROMPTS.keys()),
                       help='AI 插图风格 (默认: editorial)')
    parser.add_argument('--image-style', default=None,
                       choices=['I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7'],
                       help='配图来源风格 (I1=无 I2=Unsplash Editorial I3=Unsplash Kinfolk I4-I7=AI)')
    parser.add_argument('--output-dir', default='./images', help='输出目录')
    parser.add_argument('--api-key', help='ZMark API Key（默认使用环境变量）')
    parser.add_argument('--output', '-o', help='输出映射 JSON 文件')

    args = parser.parse_args()

    # 读取输入
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = data.get('slides', [])

    if not slides:
        print("Error: No slides found in input file", file=sys.stderr)
        sys.exit(1)

    # Determine image source
    image_style = args.image_style
    if image_style:
        source = IMAGE_STYLE_SOURCE.get(image_style, IMAGE_SOURCE_AI)
    else:
        source = IMAGE_SOURCE_AI  # Default to AI

    if source == IMAGE_SOURCE_NONE:
        print("I1 模式：无配图", file=sys.stderr)
        result = {'style': 'none', 'total_slides': len(slides), 'generated_images': 0, 'image_map': {}}

    elif source == IMAGE_SOURCE_UNSPLASH:
        if not HAS_UNSPLASH:
            print("Unsplash module not available, falling back to AI", file=sys.stderr)
            source = IMAGE_SOURCE_AI
        else:
            unsplash_style = IMAGE_STYLE_TO_UNSPLASH.get(image_style, "editorial")
            image_map = unsplash_batch(slides, style=unsplash_style)
            result = {
                'source': 'unsplash',
                'style': unsplash_style,
                'total_slides': len(slides),
                'generated_images': len(image_map),
                'image_map': image_map
            }

    if source == IMAGE_SOURCE_AI:
        if not HAS_GENAI:
            print("Error: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
            sys.exit(1)
        ai_style = IMAGE_STYLE_TO_AI.get(image_style, args.style)
        image_map = batch_generate(
            slides=slides,
            style=ai_style,
            output_dir=args.output_dir,
            api_key=args.api_key
        )
        result = {
            'source': 'ai',
            'style': ai_style,
            'total_slides': len(slides),
            'generated_images': len(image_map),
            'image_map': image_map
        }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n映射文件已保存: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
