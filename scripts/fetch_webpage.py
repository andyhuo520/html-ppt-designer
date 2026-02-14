#!/usr/bin/env python3
"""
网页内容抓取与智能解析模块 v2.0
Fetch and parse web content for PPT generation

新功能：
- 自动提取页面中的图片
- 下载图片到本地目录
- 智能过滤装饰性图片（图标、广告等）
- 生成图片与内容的映射关系
"""

import re
import os
import sys
import json
import hashlib
import argparse
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests


# 图片过滤配置
MIN_IMAGE_WIDTH = 200  # 最小宽度（像素）
MIN_IMAGE_HEIGHT = 150  # 最小高度（像素）
MIN_IMAGE_SIZE = 10000  # 最小文件大小（字节），约10KB
MAX_IMAGES = 10  # 最多下载图片数量


def fetch_webpage(url: str, timeout: int = 15) -> dict:
    """
    抓取网页内容

    Args:
        url: 网页URL
        timeout: 请求超时时间

    Returns:
        dict: {html, url, title, status}
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # 尝试获取页面标题
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        # 尝试 og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']

        # 尝试 h1 作为备选
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
        if not title:
            title = urlparse(url).netloc

        return {
            'html': response.text,
            'url': url,
            'title': title,
            'status': 'success'
        }

    except requests.RequestException as e:
        return {
            'html': None,
            'url': url,
            'title': None,
            'status': f'error: {str(e)}'
        }


def extract_images_from_html(html: str, base_url: str) -> list:
    """
    从HTML中提取图片信息

    过滤规则：
    1. 排除过小的图片（图标、装饰图）
    2. 排除广告图片
    3. 排除 data URI（内嵌小图）
    4. 优先选择 article 区域内的图片
    5. 优先选择带有 alt 属性的图片

    Returns:
        list: [{url, alt, context, priority}]
    """
    soup = BeautifulSoup(html, 'html.parser')
    images = []

    # 排除的广告/装饰图片选择器
    exclude_selectors = [
        '[class*="ad-"]', '[class*="ads"]', '[class*="icon"]',
        '[class*="logo"]', '[class*="avatar"]', '[class*="thumb"]',
        '[class*="sprite"]', '[class*="emoji"]', '[class*="smiley"]',
        'header img', 'footer img', 'nav img', 'aside img',
        '.sidebar img', '.comment img', '.widget img'
    ]

    # 高优先级区域
    priority_selectors = [
        'article img', '.article img', '.post img', '.content img',
        '.article-content img', '.post-content img', 'main img'
    ]

    # 收集高优先级图片
    priority_images = set()
    for selector in priority_selectors:
        for img in soup.select(selector):
            priority_images.add(id(img))

    # 处理所有图片
    for img in soup.find_all('img'):
        # 获取图片URL
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if not src:
            continue

        # 跳过 data URI
        if src.startswith('data:'):
            continue

        # 转换为绝对URL
        img_url = urljoin(base_url, src)

        # 检查是否在排除区域
        is_excluded = False
        for selector in exclude_selectors:
            if img.select_one(selector) or img in soup.select(selector):
                is_excluded = True
                break

        if is_excluded:
            continue

        # 获取图片属性
        alt = img.get('alt', '')
        width = img.get('width', '0')
        height = img.get('height', '0')

        # 尝试解析宽高
        try:
            width = int(width) if width else 0
        except:
            width = 0
        try:
            height = int(height) if height else 0
        except:
            height = 0

        # 过滤小图片（如果有尺寸信息）
        if width > 0 and height > 0:
            if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                continue

        # 获取上下文（周围的标题或段落）
        context = ''
        parent = img.find_parent(['figure', 'section', 'div'])
        if parent:
            caption = parent.find(['figcaption', 'caption'])
            if caption:
                context = caption.get_text().strip()
        if not context and alt:
            context = alt

        # 计算优先级
        priority = 0
        if id(img) in priority_images:
            priority += 10
        if alt:
            priority += 5
        if width >= 600 or height >= 400:
            priority += 3
        if context:
            priority += 2

        images.append({
            'url': img_url,
            'alt': alt,
            'context': context,
            'width': width,
            'height': height,
            'priority': priority
        })

    # 按优先级排序并去重
    seen_urls = set()
    unique_images = []
    for img in sorted(images, key=lambda x: x['priority'], reverse=True):
        if img['url'] not in seen_urls:
            seen_urls.add(img['url'])
            unique_images.append(img)

    return unique_images[:MAX_IMAGES]


def download_image(url: str, output_dir: str, timeout: int = 15) -> dict:
    """
    下载单张图片

    Returns:
        dict: {success, local_path, filename, error, size, dimensions}
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': url
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # 获取文件大小
        content_length = int(response.headers.get('content-length', 0))

        # 过滤太小的文件
        if content_length > 0 and content_length < MIN_IMAGE_SIZE:
            return {'success': False, 'error': 'file_too_small', 'url': url}

        # 确定文件扩展名
        content_type = response.headers.get('content-type', '')
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg'
        }
        ext = ext_map.get(content_type, '')

        # 从URL获取扩展名
        if not ext:
            parsed = urlparse(url)
            path_ext = os.path.splitext(parsed.path)[1].lower()
            if path_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                ext = path_ext

        if not ext:
            ext = '.jpg'  # 默认

        # 生成文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"image_{url_hash}{ext}"
        local_path = os.path.join(output_dir, filename)

        # 下载文件
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 获取实际文件大小
        actual_size = os.path.getsize(local_path)

        # 过滤太小的文件（下载后验证）
        if actual_size < MIN_IMAGE_SIZE:
            os.remove(local_path)
            return {'success': False, 'error': 'file_too_small', 'url': url}

        return {
            'success': True,
            'url': url,
            'local_path': local_path,
            'filename': filename,
            'size': actual_size
        }

    except Exception as e:
        return {'success': False, 'error': str(e), 'url': url}


def download_images_from_page(url: str, html: str, output_dir: str = None) -> dict:
    """
    从页面提取并下载图片

    Args:
        url: 页面URL
        html: 页面HTML
        output_dir: 图片保存目录，默认为 ~/Desktop/ppt_images/

    Returns:
        dict: {images: [{local_path, url, alt, context}], total, downloaded}
    """
    # 设置默认输出目录
    if not output_dir:
        output_dir = os.path.expanduser('~/Desktop/ppt_images/')

    # 创建目录
    os.makedirs(output_dir, exist_ok=True)

    # 提取图片信息
    image_infos = extract_images_from_html(html, url)

    print(f"\n=== 图片提取 ===", file=sys.stderr)
    print(f"发现 {len(image_infos)} 张候选图片", file=sys.stderr)

    # 下载图片
    downloaded = []
    for i, img_info in enumerate(image_infos):
        print(f"  [{i+1}/{len(image_infos)}] 下载: {img_info['url'][:60]}...", file=sys.stderr)

        result = download_image(img_info['url'], output_dir)

        if result['success']:
            downloaded.append({
                'local_path': result['local_path'],
                'filename': result['filename'],
                'url': img_info['url'],
                'alt': img_info['alt'],
                'context': img_info['context'],
                'priority': img_info['priority'],
                'size': result['size']
            })
            print(f"      成功: {result['filename']} ({result['size']} bytes)", file=sys.stderr)
        else:
            print(f"      跳过: {result['error']}", file=sys.stderr)

    print(f"\n共下载 {len(downloaded)} 张图片到 {output_dir}", file=sys.stderr)

    return {
        'images': downloaded,
        'total_found': len(image_infos),
        'total_downloaded': len(downloaded),
        'output_dir': output_dir
    }


def extract_main_content(html: str) -> dict:
    """
    智能提取正文内容

    策略：
    1. 优先查找 <article> 标签
    2. 查找常见内容区域的 class/id
    3. 降级到 body，但移除导航/广告/页脚等

    Returns:
        dict: {title, sections, content_type}
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 移除不需要的标签
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
        tag.decompose()

    # 移除常见的广告/导航元素
    ad_selectors = [
        '[class*="ad-"]', '[class*="ads"]', '[id*="ad-"]', '[id*="ads"]',
        '[class*="sidebar"]', '[class*="comment"]', '[class*="related"]',
        '[class*="navigation"]', '[class*="breadcrumb"]',
        'iframe', '.advertisement', '.social-share'
    ]
    for selector in ad_selectors:
        for elem in soup.select(selector):
            elem.decompose()

    # 策略1: 查找 article 标签
    article = soup.find('article')
    if article:
        main_content = article
    else:
        # 策略2: 查找常见内容区域
        content_selectors = [
            'main', '[role="main"]',
            '.content', '.article', '.post', '.entry',
            '#content', '#article', '#main',
            '.article-content', '.post-content',
            '[class*="article-body"]', '[class*="post-body"]'
        ]
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        if not main_content:
            # 策略3: 降级到 body
            main_content = soup.find('body')

    if not main_content:
        return {'title': '', 'sections': [], 'content_type': 'empty'}

    # 提取标题层级结构
    title = None
    h1 = main_content.find('h1')
    if h1:
        title = h1.get_text().strip()
        h1.decompose()  # 移除，避免重复
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()

    # 按标题层级分割内容
    sections = []
    current_section = {'heading': None, 'content': []}

    # 获取所有标题和段落
    elements = []
    for tag in ['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote']:
        for elem in main_content.find_all(tag, recursive=False):
            elements.append((tag, elem))

    for tag, elem in elements:
        text = elem.get_text().strip()
        if not text or len(text) < 5:
            continue

        if tag in ['h2', 'h3', 'h4']:
            # 保存上一个 section
            if current_section['content']:
                sections.append(current_section)
            # 开始新 section
            current_section = {
                'heading': text,
                'level': int(tag[1]),  # 2, 3, or 4
                'content': []
            }
        else:
            if tag in ['ul', 'ol']:
                items = [li.get_text().strip() for li in elem.find_all('li', recursive=False)]
                items = [i for i in items if i and len(i) > 2]
                if items:
                    current_section['content'].append({
                        'type': 'list',
                        'items': items
                    })
            elif tag == 'blockquote':
                current_section['content'].append({
                    'type': 'quote',
                    'text': text
                })
            else:  # p
                # 清理文本
                text = re.sub(r'\s+', ' ', text)
                current_section['content'].append({
                    'type': 'paragraph',
                    'text': text
                })

    # 保存最后一个 section
    if current_section['content']:
        sections.append(current_section)

    # 如果没有找到任何 section，尝试提取所有段落
    if not sections:
        for p in main_content.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 10:
                sections.append({
                    'heading': None,
                    'content': [{'type': 'paragraph', 'text': text}]
                })

    return {
        'title': title or 'Untitled',
        'sections': sections,
        'content_type': 'structured' if sections else 'raw'
    }


def extract_data_points(sections: list) -> list:
    """
    从内容中提取数据点（数字、百分比等）

    Returns:
        list: [{value, context, type}]
    """
    data_points = []

    # 匹配模式
    patterns = [
        (r'\d+\.?\d*%', 'percentage'),
        (r'\d{4,}', 'number'),
        (r'\$\d+[,.\d]*', 'currency'),
        (r'¥\d+[,.\d]*', 'currency'),
    ]

    for section in sections:
        for item in section.get('content', []):
            if item['type'] == 'paragraph':
                text = item['text']
                for pattern, dtype in patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        data_points.append({
                            'value': match,
                            'type': dtype,
                            'context': text[:50] + '...' if len(text) > 50 else text
                        })

    return data_points[:10]  # 最多返回10个


def generate_outline(content: dict, max_slides: int = 12) -> dict:
    """
    根据内容生成 PPT 大纲

    Args:
        content: 解析后的内容
        max_slides: 最大幻灯片数量

    Returns:
        dict: PPT 大纲
    """
    title = content.get('title', 'Untitled')
    sections = content.get('sections', [])

    slides = []
    slides.append({
        'type': 'title',
        'content': {'title': title, 'subtitle': ''}
    })

    # 估算每个 section 对应的页数
    for section in sections[:max_slides - 2]:  # 留出封面和结尾页
        heading = section.get('heading', '')
        content_items = section.get('content', [])

        # 判断 section 类型
        total_text = sum(
            len(item.get('text', '') + ''.join(item.get('items', [])))
            for item in content_items
        )

        if total_text > 500:
            # 内容较长，拆分多页
            slides.append({
                'type': 'content',
                'content': {'title': heading, 'points': content_items[:3]}
            })
            if len(content_items) > 3:
                slides.append({
                    'type': 'content',
                    'content': {'title': heading + '（续）', 'points': content_items[3:6]}
                })
        elif total_text > 200:
            # 中等长度，一页
            slides.append({
                'type': 'content',
                'content': {'title': heading, 'points': content_items}
            })
        else:
            # 内容较短，可能可以合并
            if slides and slides[-1]['type'] == 'content' and len(slides[-1]['content']['points']) < 3:
                # 合并到上一页
                slides[-1]['content']['points'].extend(content_items)
            else:
                slides.append({
                    'type': 'content',
                    'content': {'title': heading, 'points': content_items}
                })

    # 提取数据页
    data_points = extract_data_points(sections)
    if data_points and len(slides) < max_slides - 1:
        slides.append({
            'type': 'data',
            'content': {'title': '关键数据', 'data': data_points[:6]}
        })

    # 结尾页
    slides.append({
        'type': 'ending',
        'content': {'title': '谢谢', 'subtitle': ''}
    })

    return {
        'title': title,
        'total_slides': len(slides),
        'slides': slides
    }


def main():
    parser = argparse.ArgumentParser(description='抓取网页内容并生成PPT大纲 v2.0')
    parser.add_argument('url', help='网页URL')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('--pretty', action='store_true', help='美化输出')
    parser.add_argument('--download-images', action='store_true', help='下载页面图片')
    parser.add_argument('--image-dir', help='图片保存目录（默认 ~/Desktop/ppt_images/）')

    args = parser.parse_args()

    # 抓取网页
    print(f"正在抓取: {args.url}", file=sys.stderr)
    fetch_result = fetch_webpage(args.url)

    if fetch_result['status'] != 'success':
        print(json.dumps({'error': fetch_result['status']}))
        sys.exit(1)

    print(f"页面标题: {fetch_result['title']}", file=sys.stderr)

    # 解析内容
    print("正在解析内容...", file=sys.stderr)
    content = extract_main_content(fetch_result['html'])
    content['url'] = fetch_result['url']
    content['source_title'] = fetch_result['title']

    # 下载图片（如果请求）
    images_result = None
    if args.download_images:
        images_result = download_images_from_page(
            args.url,
            fetch_result['html'],
            args.image_dir
        )

    # 生成大纲
    print("正在生成大纲...", file=sys.stderr)
    outline = generate_outline(content)
    outline['source'] = {'url': fetch_result['url'], 'title': fetch_result['title']}

    # 添加图片信息到大纲
    if images_result:
        outline['images'] = images_result

    # 输出
    indent = 2 if args.pretty else None
    output_json = json.dumps(outline, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"已保存到: {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 打印摘要
    print(f"\n=== PPT 大纲摘要 ===", file=sys.stderr)
    print(f"标题: {outline['title']}", file=sys.stderr)
    print(f"预计页数: {outline['total_slides']}", file=sys.stderr)
    print(f"内容分区: {len(content['sections'])}", file=sys.stderr)
    if images_result:
        print(f"下载图片: {images_result['total_downloaded']}/{images_result['total_found']}", file=sys.stderr)


if __name__ == '__main__':
    main()
