#!/usr/bin/env python3
"""
Excalidraw to SVG Converter
将 .excalidraw JSON 文件转换为 SVG 格式，用于 HTML PPT 嵌入

用法:
    python3 excalidraw_to_svg.py input.excalidraw -o output.svg
    python3 excalidraw_to_svg.py input.excalidraw --base64  # 输出 data URI
"""

import json
import sys
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# Excalidraw 颜色名到 CSS 颜色的映射
COLOR_MAP = {
    # 默认调色板
    None: "#1e1e1e",  # 默认黑色
    "#1e1e1e": "#1e1e1e",
    "#2f9e44": "#2f9e44",  # 绿色
    "#1971c2": "#1971c2",  # 蓝色
    "#e03131": "#e03131",  # 红色
    "#9c36b5": "#9c36b5",  # 紫色
    "#f08c00": "#f08c00",  # 橙色
    "#c92a2a": "#c92a2a",  # 深红
    "#7048e8": "#7048e8",  # 紫蓝
    "#fab005": "#fab005",  # 黄色
    "#fd7e14": "#fd7e14",  # 橙
    "#12b886": "#12b886",  # 青
    "#228be6": "#228be6",  # 天蓝
    "#7950f2": "#7950f2",  # 紫
    "#be4bdb": "#be4bdb",  # 粉紫
    "#e64980": "#e64980",  # 粉
    "#fa5252": "#fa5252",  # 浅红
    "#82c91e": "#82c91e",  # 草绿
    "#15aabf": "#15aabf",  # 青蓝
    "#fd7e14": "#fd7e14",
    # 背景色
    "#a5d8ff": "#a5d8ff",  # 浅蓝
    "#d0bfff": "#d0bfff",  # 浅紫
    "#b2f2bb": "#b2f2bb",  # 浅绿
    "#ffec99": "#ffec99",  # 浅黄
    "#ffc9c9": "#ffc9c9",  # 浅红
    "#ffa8a8": "#ffa8a8",  # 浅珊瑚
    "#fff3bf": "#fff3bf",  # 浅黄2
    "#ffe8cc": "#ffe8cc",  # 浅橙
    "#e7f5ff": "#e7f5ff",  # 极浅蓝
    "#e599f7": "#e599f7",  # 浅粉紫
}


def get_color(color: Optional[str], default: str = "#1e1e1e") -> str:
    """获取颜色值，处理 None 和颜色名"""
    if color is None:
        return default
    if color.startswith("#"):
        return color
    return COLOR_MAP.get(color, default)


def get_stroke_width(element: Dict) -> float:
    """获取线条宽度"""
    return element.get("strokeWidth", 2)


def get_opacity(element: Dict) -> float:
    """获取透明度"""
    return element.get("opacity", 100) / 100


def get_roundness(element: Dict) -> Optional[float]:
    """获取圆角"""
    roundness = element.get("roundness")
    if roundness is None:
        return None
    if isinstance(roundness, dict):
        return roundness.get("value", 0)
    return roundness


def render_rectangle(element: Dict) -> str:
    """渲染矩形"""
    x = element.get("x", 0)
    y = element.get("y", 0)
    width = element.get("width", 100)
    height = element.get("height", 100)
    stroke = get_color(element.get("strokeColor"))
    fill = get_color(element.get("backgroundColor"), "transparent")
    stroke_width = get_stroke_width(element)
    opacity = get_opacity(element)
    roundness = get_roundness(element)

    style = f"fill:{fill};stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"

    if roundness:
        rx = min(roundness, width / 2, height / 2)
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{rx}" style="{style}"/>'
    else:
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" style="{style}"/>'


def render_ellipse(element: Dict) -> str:
    """渲染椭圆"""
    x = element.get("x", 0)
    y = element.get("y", 0)
    width = element.get("width", 100)
    height = element.get("height", 100)
    stroke = get_color(element.get("strokeColor"))
    fill = get_color(element.get("backgroundColor"), "transparent")
    stroke_width = get_stroke_width(element)
    opacity = get_opacity(element)

    cx = x + width / 2
    cy = y + height / 2
    rx = width / 2
    ry = height / 2

    style = f"fill:{fill};stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" style="{style}"/>'


def render_diamond(element: Dict) -> str:
    """渲染菱形"""
    x = element.get("x", 0)
    y = element.get("y", 0)
    width = element.get("width", 100)
    height = element.get("height", 100)
    stroke = get_color(element.get("strokeColor"))
    fill = get_color(element.get("backgroundColor"), "transparent")
    stroke_width = get_stroke_width(element)
    opacity = get_opacity(element)

    # 菱形的四个顶点
    cx = x + width / 2
    cy = y + height / 2
    points = f"{cx},{y} {x+width},{cy} {cx},{y+height} {x},{cy}"

    style = f"fill:{fill};stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"
    return f'<polygon points="{points}" style="{style}"/>'


def render_line(element: Dict) -> str:
    """渲染线条"""
    points = element.get("points", [[0, 0]])
    x = element.get("x", 0)
    y = element.get("y", 0)
    stroke = get_color(element.get("strokeColor"))
    stroke_width = get_stroke_width(element)
    opacity = get_opacity(element)

    if len(points) < 2:
        return ""

    # 构建 path
    path_d = f"M {x + points[0][0]} {y + points[0][1]}"
    for px, py in points[1:]:
        path_d += f" L {x + px} {y + py}"

    style = f"fill:none;stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"
    return f'<path d="{path_d}" style="{style}"/>'


def render_arrow(element: Dict, defs_id: str) -> str:
    """渲染箭头"""
    points = element.get("points", [[0, 0]])
    x = element.get("x", 0)
    y = element.get("y", 0)
    stroke = get_color(element.get("strokeColor"))
    stroke_width = get_stroke_width(element)
    opacity = get_opacity(element)

    if len(points) < 2:
        return ""

    # 构建 path
    path_d = f"M {x + points[0][0]} {y + points[0][1]}"
    for px, py in points[1:]:
        path_d += f" L {x + px} {y + py}"

    style = f"fill:none;stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"
    return f'<path d="{path_d}" style="{style}" marker-end="url(#{defs_id})"/>'


def render_text(element: Dict) -> str:
    """渲染文本"""
    x = element.get("x", 0)
    y = element.get("y", 0)
    text = element.get("text", "")
    stroke = get_color(element.get("strokeColor"), "#1e1e1e")
    font_size = element.get("fontSize", 16)
    font_family = element.get("fontFamily", 1)
    opacity = get_opacity(element)
    text_align = element.get("textAlign", "left")

    # 字体映射
    font_map = {
        1: "Virgil, Segoe UI Emoji",  # 手写体
        2: "Helvetica, Arial",  # 无衬线
        3: "Cascadia, monospace",  # 等宽
    }
    font = font_map.get(font_family, font_map[1])

    # 对齐映射
    align_map = {
        "left": "start",
        "center": "middle",
        "right": "end",
    }
    anchor = align_map.get(text_align, "start")

    style = f"fill:{stroke};font-size:{font_size}px;font-family:{font};opacity:{opacity};text-anchor:{anchor};"

    # 处理多行文本
    lines = text.split("\n")
    if len(lines) == 1:
        return f'<text x="{x}" y="{y + font_size}" style="{style}">{text}</text>'
    else:
        tspans = []
        for i, line in enumerate(lines):
            dy = font_size * 1.2 if i > 0 else font_size
            tspans.append(f'<tspan x="{x}" dy="{dy if i > 0 else 0}">{line}</tspan>')
        return f'<text x="{x}" y="{y}" style="{style}">{"".join(tspans)}</text>'


def calculate_bounds(elements: List[Dict]) -> Tuple[float, float, float, float]:
    """计算元素边界"""
    if not elements:
        return (0, 0, 800, 600)

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for el in elements:
        x = el.get("x", 0)
        y = el.get("y", 0)
        width = el.get("width", 0) or 0
        height = el.get("height", 0) or 0

        # 处理线/箭头的 points
        points = el.get("points", [])
        if points:
            for px, py in points:
                min_x = min(min_x, x + px)
                min_y = min(min_y, y + py)
                max_x = max(max_x, x + px)
                max_y = max(max_y, y + py)
        else:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + width)
            max_y = max(max_y, y + height)

    # 添加边距
    padding = 20
    return (min_x - padding, min_y - padding, max_x - min_x + padding * 2, max_y - min_y + padding * 2)


def convert_to_svg(excalidraw_data: Dict, theme: str = "light") -> str:
    """将 Excalidraw JSON 转换为 SVG"""
    elements = excalidraw_data.get("elements", [])
    app_state = excalidraw_data.get("appState", {})

    if not elements:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"></svg>'

    # 计算边界
    min_x, min_y, width, height = calculate_bounds(elements)

    # 背景色
    bg_color = "#ffffff" if theme == "light" else "#1e1e1e"
    view_bg = app_state.get("viewBackgroundColor")
    if view_bg:
        bg_color = get_color(view_bg, bg_color)

    # SVG 头部
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="{min_x:.1f} {min_y:.1f} {width:.1f} {height:.1f}">',
        f'<rect x="{min_x:.1f}" y="{min_y:.1f}" width="{width:.1f}" height="{height:.1f}" fill="{bg_color}"/>',
    ]

    # 添加箭头 marker 定义
    arrow_id = "arrowhead"
    svg_parts.append(f'''
  <defs>
    <marker id="{arrow_id}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="currentColor"/>
    </marker>
  </defs>
''')

    # 构建元素 ID 映射（用于处理文本绑定）
    element_map = {el.get("id"): el for el in elements}

    # 渲染元素（按 z-index 排序）
    sorted_elements = sorted(elements, key=lambda e: e.get("index", 0))

    for element in sorted_elements:
        el_type = element.get("type", "")

        if el_type == "rectangle":
            svg_parts.append("  " + render_rectangle(element))
        elif el_type == "ellipse":
            svg_parts.append("  " + render_ellipse(element))
        elif el_type == "diamond":
            svg_parts.append("  " + render_diamond(element))
        elif el_type == "line":
            svg_parts.append("  " + render_line(element))
        elif el_type == "arrow":
            svg_parts.append("  " + render_arrow(element, arrow_id))
        elif el_type == "text":
            svg_parts.append("  " + render_text(element))
        elif el_type == "draw":
            # 自由绘制，作为 path 处理
            points = element.get("points", [])
            if len(points) >= 2:
                x = element.get("x", 0)
                y = element.get("y", 0)
                stroke = get_color(element.get("strokeColor"))
                stroke_width = get_stroke_width(element)
                opacity = get_opacity(element)

                path_d = f"M {x + points[0][0]} {y + points[0][1]}"
                for px, py in points[1:]:
                    path_d += f" L {x + px} {y + py}"

                style = f"fill:none;stroke:{stroke};stroke-width:{stroke_width};opacity:{opacity};"
                svg_parts.append(f'  <path d="{path_d}" style="{style}"/>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main():
    parser = argparse.ArgumentParser(description="Convert Excalidraw JSON to SVG")
    parser.add_argument("input", help="Input .excalidraw file path")
    parser.add_argument("-o", "--output", help="Output .svg file path (default: stdout)")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Theme (light/dark)")
    parser.add_argument("--base64", action="store_true", help="Output as data URI (base64)")
    parser.add_argument("--embed", action="store_true", help="Output as HTML img tag with embedded SVG")

    args = parser.parse_args()

    # 读取输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        excalidraw_data = json.load(f)

    # 转换
    svg_content = convert_to_svg(excalidraw_data, args.theme)

    # 输出
    if args.base64:
        svg_bytes = svg_content.encode("utf-8")
        b64 = base64.b64encode(svg_bytes).decode("utf-8")
        output = f"data:image/svg+xml;base64,{b64}"
    elif args.embed:
        svg_escaped = svg_content.replace('"', '&quot;').replace("'", "&#39;")
        output = f'<img src="data:image/svg+xml,{svg_escaped}" alt="Excalidraw diagram">'
    else:
        output = svg_content

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"SVG written to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
