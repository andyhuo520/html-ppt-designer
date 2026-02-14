#!/usr/bin/env python3
"""
Unsplash API 图片获取模块 v3.1
Fetch high-quality photos from Unsplash for PPT slides

环境变量配置:
  UNSPLASH_ACCESS_KEY - Unsplash API Access Key（必需）

申请方法:
  1. 访问 https://unsplash.com/developers
  2. 注册/登录 Unsplash 账号
  3. 创建新应用（New Application）
  4. 填写应用信息（用途：PPT 配图）
  5. 获取 Access Key
  6. 设置环境变量: export UNSPLASH_ACCESS_KEY="your-access-key"

免费额度:
  - 50 次/小时 请求限制
  - 适合个人使用和小型项目
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Optional


# Unsplash API 配置
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_BASE = "https://api.unsplash.com"


def check_api_key():
    """检查 API Key 是否已配置"""
    if not UNSPLASH_ACCESS_KEY:
        print("=" * 60, file=sys.stderr)
        print("错误: 未配置 UNSPLASH_ACCESS_KEY 环境变量", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("", file=sys.stderr)
        print("申请方法:", file=sys.stderr)
        print("  1. 访问 https://unsplash.com/developers", file=sys.stderr)
        print("  2. 注册/登录 Unsplash 账号", file=sys.stderr)
        print("  3. 创建新应用（New Application）", file=sys.stderr)
        print("  4. 获取 Access Key", file=sys.stderr)
        print("  5. 设置环境变量:", file=sys.stderr)
        print("     export UNSPLASH_ACCESS_KEY='your-access-key'", file=sys.stderr)
        print("", file=sys.stderr)
        print("免费额度: 50 次/小时", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return False
    return True


def search_photos(
    query: str,
    per_page: int = 5,
    orientation: Optional[str] = "landscape",
    color: Optional[str] = None,
    order_by: str = "relevant",
    content_filter: str = "high",
) -> List[Dict]:
    """
    Search Unsplash for photos matching a query.

    Args:
        query: Search keywords (English recommended)
        per_page: Number of results (1-30)
        orientation: landscape, portrait, squarish, or None
        color: Color filter (black_and_white, black, white, yellow, orange,
               red, purple, magenta, green, teal, blue)
        order_by: Sort order (relevant, latest)
        content_filter: Safety filter (low, high)

    Returns:
        List of photo dicts with id, urls, description, photographer info
    """
    if not check_api_key():
        return []

    params = {
        "query": query,
        "per_page": str(per_page),
        "order_by": order_by,
        "content_filter": content_filter,
    }
    if orientation:
        params["orientation"] = orientation
    if color:
        params["color"] = color

    url = f"{UNSPLASH_API_BASE}/search/photos?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Client-ID {UNSPLASH_ACCESS_KEY}")
    req.add_header("Accept-Version", "v1")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Unsplash API error: {e.code} {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unsplash request failed: {e}", file=sys.stderr)
        return []

    results = []
    for photo in data.get("results", []):
        results.append({
            "id": photo["id"],
            "description": photo.get("description") or photo.get("alt_description") or "",
            "urls": {
                "raw": photo["urls"]["raw"],
                "full": photo["urls"]["full"],
                "regular": photo["urls"]["regular"],  # 1080px wide
                "small": photo["urls"]["small"],       # 400px wide
                "thumb": photo["urls"]["thumb"],       # 200px wide
            },
            "photographer": {
                "name": photo["user"]["name"],
                "username": photo["user"]["username"],
                "link": photo["user"]["links"]["html"],
            },
            "color": photo.get("color", "#000000"),
            "width": photo["width"],
            "height": photo["height"],
            "blur_hash": photo.get("blur_hash", ""),
        })

    return results


def get_photo_url(
    query: str,
    size: str = "regular",
    orientation: str = "landscape",
    color: Optional[str] = None,
) -> Optional[Dict]:
    """
    Get a single best-match photo URL for a query.

    Args:
        query: Search keywords
        size: Image size (raw, full, regular, small, thumb)
        orientation: landscape, portrait, squarish
        color: Optional color filter

    Returns:
        Dict with url, photographer info, and attribution HTML
    """
    photos = search_photos(query, per_page=1, orientation=orientation, color=color)
    if not photos:
        return None

    photo = photos[0]
    url = photo["urls"].get(size, photo["urls"]["regular"])

    # Unsplash requires attribution
    attribution = (
        f'Photo by <a href="{photo["photographer"]["link"]}?utm_source=ppt_designer'
        f'&utm_medium=referral">{photo["photographer"]["name"]}</a> on '
        f'<a href="https://unsplash.com/?utm_source=ppt_designer'
        f'&utm_medium=referral">Unsplash</a>'
    )

    return {
        "url": url,
        "photographer": photo["photographer"]["name"],
        "attribution_html": attribution,
        "color": photo["color"],
        "blur_hash": photo["blur_hash"],
        "description": photo["description"],
    }


def batch_fetch_for_slides(
    slides: List[Dict],
    style: str = "editorial",
    orientation: str = "landscape",
) -> Dict[str, Dict]:
    """
    Batch fetch Unsplash images for a set of slides.

    Args:
        slides: List of slide dicts with title, content, type
        style: PPT style (affects search query refinement)
        orientation: Image orientation preference

    Returns:
        Dict mapping slide index to image info
    """
    # Style-specific search modifiers
    style_modifiers = {
        "ted": "dramatic dark cinematic",
        "apple_keynote": "minimal clean white product",
        "consulting": "corporate business professional",
        "editorial": "editorial magazine black white artistic",
        "newspaper": "documentary journalism photojournalism",
        "kinfolk": "lifestyle warm film grain cozy",
        "muji": "minimal japanese zen natural texture",
        "dark_mode": "dark moody dramatic contrast",
        "neo_tokyo": "neon cyberpunk night city futuristic",
        "brutalist": "concrete architecture raw urban",
    }

    modifier = style_modifiers.get(style, "")

    # Slide type to search refinement
    type_refinements = {
        "cover": "hero wide establishing shot",
        "quote": "atmospheric mood inspirational",
        "ending": "horizon sunset forward looking",
        "content": "",
    }

    image_map = {}
    print(f"\n=== Unsplash 配图获取开始 ===", file=sys.stderr)
    print(f"风格修饰词: {modifier}", file=sys.stderr)

    for i, slide in enumerate(slides):
        slide_type = slide.get("type", "content")

        # Skip data/chart pages
        if slide_type in ("data", "chart", "timeline"):
            print(f"  [{i+1}] Skip (no image needed): {slide.get('title', '')}", file=sys.stderr)
            continue

        # Build search query
        title = slide.get("title", "")
        content = slide.get("content", "")[:100]
        type_ref = type_refinements.get(slide_type, "")

        # Combine into search query (prefer English keywords)
        query_parts = [title, type_ref, modifier]
        query = " ".join(p for p in query_parts if p).strip()

        if not query:
            query = "abstract minimal background"

        print(f"  [{i+1}] Searching: {query[:60]}...", file=sys.stderr)

        result = get_photo_url(query, size="regular", orientation=orientation)
        if result:
            image_map[str(i)] = result
            print(f"    Found: {result['photographer']}", file=sys.stderr)
        else:
            print(f"    No results found", file=sys.stderr)

    print(f"\n=== Unsplash 配图获取完成 ===", file=sys.stderr)
    print(f"共获取 {len(image_map)} 张图片", file=sys.stderr)

    return image_map


def main():
    parser = argparse.ArgumentParser(description="Unsplash 配图获取工具 v3.0")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # search command
    search_parser = subparsers.add_parser("search", help="Search photos")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--count", type=int, default=5, help="Number of results")
    search_parser.add_argument("--orientation", default="landscape",
                               choices=["landscape", "portrait", "squarish"])
    search_parser.add_argument("--color", help="Color filter")

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Batch fetch for slides JSON")
    batch_parser.add_argument("input", help="Slides JSON file")
    batch_parser.add_argument("--style", default="editorial", help="PPT style")
    batch_parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    if args.command == "search":
        photos = search_photos(args.query, per_page=args.count,
                               orientation=args.orientation, color=args.color)
        print(json.dumps(photos, ensure_ascii=False, indent=2))

    elif args.command == "batch":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        slides = data.get("slides", [])
        style = args.style

        image_map = batch_fetch_for_slides(slides, style=style)

        result = {
            "source": "unsplash",
            "style": style,
            "total_slides": len(slides),
            "fetched_images": len(image_map),
            "image_map": image_map,
        }

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nSaved to: {args.output}", file=sys.stderr)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
