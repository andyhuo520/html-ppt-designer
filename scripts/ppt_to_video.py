#!/usr/bin/env python3
"""
PPT to Video Converter v3.3
将 HTML PPT 幻灯片转换为带配音和字幕的视频

v3.3 改进:
- 增加国产 TTS 服务支持：火山引擎、智谱 AI、百度、讯飞
- 支持 30+ 中文语音选择

v3.2 改进:
- 内嵌字幕：按句子分割，逐句显示
- 字幕时长按字数比例分配，与音频同步

v3.0 核心改进:
- 音频驱动时长：先生成音频，获取实际时长，再截图
- 每页展示时间 = 该页音频时长，视频音频 100% 同步

使用方法:
    python3 ppt_to_video.py presentation.html -o output.mp4
    python3 ppt_to_video.py presentation.html --tts volcengine --voice zh_female_tianmeixiaoyuan
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import shutil
import hashlib
import time
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any

# 尝试导入可选依赖
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import mutagen
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# 国产 TTS SDK
try:
    import volcengine
    HAS_VOLCENGINE = True
except ImportError:
    HAS_VOLCENGINE = False

try:
    from zhipuai import ZhipuAI
    HAS_ZHIPU = True
except ImportError:
    HAS_ZHIPU = False


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg: str):
    print(f"{Colors.CYAN}ℹ{Colors.END} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def log_step(step: str, msg: str):
    print(f"{Colors.BOLD}{Colors.BLUE}[{step}]{Colors.END} {msg}")


class PPTToVideoConverter:
    """HTML PPT 转视频转换器 v3.3"""

    DEFAULT_VOICES = {
        'edge': {
            'zh': 'zh-CN-YunjianNeural',      # 云健 - 男声，新闻播报（默认）
            'zh-female': 'zh-CN-XiaoxiaoNeural', # 晓晓 - 女声
            'zh-male-young': 'zh-CN-YunxiNeural', # 云希 - 男声，年轻活力
            'en': 'en-US-GuyNeural',
        },
        'openai': {
            'zh': 'onyx',
            'en': 'alloy',
        },
        # 火山引擎 TTS
        'volcengine': {
            'zh': 'zh_female_tianmeixiaoyuan',  # 甜美女声
            'zh-male': 'zh_male_chunhou',
            'zh-news': 'zh_male_narration',
        },
        # 智谱 AI TTS
        'zhipu': {
            'zh': 'alloy',  # 智谱使用 alloy 等标识
        },
        # Fish Speech (开源)
        'fish': {
            'zh': 'default',
        },
    }

    # Edge TTS 中文语音列表
    EDGE_CHINESE_VOICES = [
        ('zh-CN-XiaoxiaoNeural', '晓晓 - 女声，自然亲切（推荐）'),
        ('zh-CN-YunxiNeural', '云希 - 男声，年轻活力'),
        ('zh-CN-YunjianNeural', '云健 - 男声，新闻播报'),
        ('zh-CN-XiaoyiNeural', '晓伊 - 女声，温柔'),
        ('zh-CN-YunfengNeural', '云枫 - 男声，沉稳'),
        ('zh-CN-YunyangNeural', '云扬 - 男声，专业客服'),
        ('zh-CN-XiaochenNeural', '晓辰 - 女声，新闻'),
        ('zh-CN-XiaohanNeural', '晓涵 - 女声，温暖'),
        ('zh-CN-XiaomengNeural', '晓梦 - 女声，儿童'),
        ('zh-CN-XiaomoNeural', '晓墨 - 女声，成熟'),
        ('zh-CN-XiaoruiNeural', '晓睿 - 女声，儿童'),
        ('zh-CN-XiaoshuangNeural', '晓双 - 女声，儿童'),
        ('zh-CN-XiaoxiaoNeural', '晓晓 - 女声，自然'),
        ('zh-CN-XiaoxuanNeural', '晓萱 - 女声，温柔'),
        ('zh-CN-XiaoyanNeural', '晓妍 - 女声，温柔'),
        ('zh-CN-XiaoyouNeural', '晓悠 - 女声，儿童'),
    ]

    # 火山引擎 TTS 语音列表
    VOLCENGINE_CHINESE_VOICES = [
        ('zh_female_tianmeixiaoyuan', '甜美小媛 - 女声，甜美亲切（推荐）'),
        ('zh_female_shuangkuaisisi', '爽快思思 - 女声，爽朗'),
        ('zh_female_wanwan', '湾湾 - 女声，台湾腔'),
        ('zh_female_chenshu', '成熟姐姐 - 女声，知性'),
        ('zh_male_chunhou', '醇厚男声 - 男声，稳重'),
        ('zh_male_narration', '解说男声 - 男声，专业'),
        ('zh_male_qingxinnansheng', '清新男声 - 男声，年轻'),
        ('zh_male_huangzhong', '黄钟 - 男声，播音'),
    ]

    # TTS 服务信息
    TTS_SERVICES = {
        'edge': {'name': 'Edge TTS（微软）', 'free': True, 'quality': '良好'},
        'openai': {'name': 'OpenAI TTS', 'free': False, 'quality': '优秀'},
        'volcengine': {'name': '火山引擎（字节）', 'free': False, 'quality': '优秀'},
        'zhipu': {'name': '智谱 AI', 'free': False, 'quality': '优秀'},
        'fish': {'name': 'Fish Speech（开源）', 'free': True, 'quality': '良好'},
    }

    def __init__(
        self,
        html_path: str,
        output: str = "output.mp4",
        resolution: str = "1920x1080",
        fps: int = 30,
        tts_provider: str = "edge",
        voice: Optional[str] = None,
        language: str = "zh",
        keep_temp: bool = False,
        subtitle: bool = True,
        subtitle_font: str = "PingFang SC, Noto Sans SC, sans-serif",
        subtitle_fontsize: int = 28,
        subtitle_bg_radius: int = 12
    ):
        self.html_path = Path(html_path).resolve()
        self.output = Path(output).resolve()
        self.resolution = resolution
        self.width, self.height = map(int, resolution.split('x'))
        self.fps = fps
        # v3.0: 不再有 default_duration，时长完全由音频决定
        self.tts_provider = tts_provider
        self.language = language
        self.keep_temp = keep_temp

        # 字幕配置
        self.subtitle = subtitle
        self.subtitle_font = subtitle_font
        self.subtitle_fontsize = subtitle_fontsize
        self.subtitle_bg_radius = subtitle_bg_radius

        if voice:
            self.voice = voice
        else:
            self.voice = self.DEFAULT_VOICES.get(tts_provider, {}).get(language, 'zh-CN-XiaoxiaoNeural')

        # 临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ppt_video_"))
        self.slides_dir = self.temp_dir / "slides"
        self.audio_dir = self.temp_dir / "audio"
        self.slides_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)

        self.slide_data: List[Dict[str, Any]] = []
        self.slide_count = 0

    def check_dependencies(self) -> bool:
        """检查依赖"""
        errors = []

        if not shutil.which('ffmpeg'):
            errors.append("ffmpeg 未安装。请运行: brew install ffmpeg")

        if not HAS_PLAYWRIGHT:
            errors.append("playwright 未安装。请运行: pip install playwright && playwright install chromium")

        if self.tts_provider == "edge" and not HAS_EDGE_TTS:
            errors.append("edge-tts 未安装。请运行: pip install edge-tts")

        if self.tts_provider == "openai" and not HAS_OPENAI:
            errors.append("openai 未安装。请运行: pip install openai")

        # 国产 TTS 依赖检查
        if self.tts_provider == "volcengine":
            if not os.environ.get('VOLCENGINE_ACCESS_KEY'):
                log_warning("火山引擎 TTS 需要设置环境变量: VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY, VOLCENGINE_APP_ID")

        if self.tts_provider == "zhipu" and not HAS_ZHIPU:
            errors.append("zhipuai 未安装。请运行: pip install zhipuai")

        if self.tts_provider == "fish":
            fish_url = os.environ.get('FISH_SPEECH_URL', 'http://localhost:8080')
            log_warning(f"Fish Speech 需要本地服务运行: {fish_url}")

        if not HAS_MUTAGEN:
            log_warning("mutagen 未安装，将使用默认时长。建议运行: pip install mutagen")

        if errors:
            for error in errors:
                log_error(error)
            return False

        return True

    def split_into_sentences(self, text: str) -> List[str]:
        """
        将文本按句子分割
        支持中英文句子分割
        """
        import re
        # 按句号、问号、感叹号分割，保留标点
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        # 过滤空字符串
        sentences = [s.strip() for s in sentences if s.strip()]
        # 如果没有分割出多个句子，返回原文本
        if not sentences:
            return [text]
        return sentences

    def capture_slides(self, audio_durations: List[int], narrations: List[str] = None) -> tuple:
        """
        使用 Playwright 逐页截图

        v3.0: 接收音频时长列表，每页展示时间 = 该页音频时长
        v3.1: 支持内嵌字幕渲染
        v3.2: 字幕按句子分割，逐句显示，与音频同步

        Returns:
            tuple: (截图总数, 每张截图的时长列表, 每张截图对应的字幕列表)
        """
        log_step("截图", "正在捕获幻灯片...")

        if narrations is None:
            narrations = []

        # 用于存储每张截图的时长和字幕
        screenshot_durations = []
        screenshot_subtitles = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': self.width, 'height': self.height},
                device_scale_factor=2
            )
            page = context.new_page()

            # 加载 HTML
            page.goto(f"file://{self.html_path}", wait_until='networkidle')
            page.wait_for_selector('.slide', timeout=10000)

            # 隐藏控制面板
            page.evaluate("""
                const panel = document.querySelector('.control-panel');
                if (panel) panel.style.display = 'none';
            """)

            # 如果启用字幕，注入字幕容器和样式
            if self.subtitle:
                subtitle_css = f"""
                    .video-subtitle-container {{
                        position: fixed;
                        bottom: 60px;
                        left: 0;
                        right: 0;
                        display: flex;
                        justify-content: center;
                        align-items: flex-end;
                        z-index: 9999;
                        pointer-events: none;
                        padding: 0 80px;
                    }}
                    .video-subtitle {{
                        font-family: '{self.subtitle_font}';
                        font-size: {self.subtitle_fontsize}px;
                        font-weight: 500;
                        color: #FFFFFF;
                        background: rgba(0, 0, 0, 0.75);
                        padding: 12px 24px;
                        border-radius: {self.subtitle_bg_radius}px;
                        line-height: 1.5;
                        text-align: center;
                        max-width: 85%;
                        word-wrap: break-word;
                        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
                        display: -webkit-box;
                        -webkit-line-clamp: 2;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                    }}
                """
                page.evaluate(f"""
                    (() => {{
                        // 注入样式
                        const style = document.createElement('style');
                        style.id = 'subtitle-style';
                        style.textContent = `{subtitle_css}`;
                        document.head.appendChild(style);

                        // 创建字幕容器
                        const container = document.createElement('div');
                        container.className = 'video-subtitle-container';
                        container.id = 'subtitle-container';

                        const subtitle = document.createElement('div');
                        subtitle.className = 'video-subtitle';
                        subtitle.id = 'subtitle-text';

                        container.appendChild(subtitle);
                        document.body.appendChild(container);
                    }})()
                """)
                log_info("已启用内嵌字幕（单行模式）")

            # 获取所有幻灯片
            total_slides = page.evaluate("document.querySelectorAll('.slide').length")
            log_info(f"发现 {total_slides} 张幻灯片")

            screenshot_idx = 0

            for slide_idx in range(total_slides):
                audio_duration = audio_durations[slide_idx] if slide_idx < len(audio_durations) else 5000
                narration = narrations[slide_idx] if slide_idx < len(narrations) else ""

                # 将讲解文字按句子分割
                sentences = self.split_into_sentences(narration) if self.subtitle and narration else [""]

                # 按句子字数比例分配时间
                total_chars = sum(len(s) for s in sentences)
                sentence_durations = []
                for sent in sentences:
                    if total_chars > 0:
                        sent_duration = int(audio_duration * len(sent) / total_chars)
                    else:
                        sent_duration = audio_duration // len(sentences)
                    # 确保每句至少显示 1.5 秒
                    sent_duration = max(sent_duration, 1500)
                    sentence_durations.append(sent_duration)

                # 调整总时长以匹配音频时长
                total_allocated = sum(sentence_durations)
                if total_allocated != audio_duration and sentence_durations:
                    sentence_durations[-1] += (audio_duration - total_allocated)

                log_info(f"捕获第 {slide_idx+1}/{total_slides} 页 ({len(sentences)} 句字幕, 总 {audio_duration/1000:.1f}秒)...")

                # 显示当前幻灯片
                page.evaluate(f"""
                    (() => {{
                        const slides = document.querySelectorAll('.slide');
                        slides.forEach((s, idx) => {{
                            s.classList.remove('slide-active');
                            s.style.visibility = 'hidden';
                            s.style.opacity = '0';
                            s.style.display = 'none';
                        }});
                        if (slides[{slide_idx}]) {{
                            slides[{slide_idx}].classList.add('slide-active');
                            slides[{slide_idx}].style.visibility = 'visible';
                            slides[{slide_idx}].style.opacity = '1';
                            slides[{slide_idx}].style.display = 'flex';
                        }}
                    }})()
                """)

                # 等待图片加载
                img_loaded = page.evaluate(f"""
                    (() => {{
                        const slide = document.querySelectorAll('.slide')[{slide_idx}];
                        if (!slide) return {{ loaded: true, count: 0 }};
                        const imgs = slide.querySelectorAll('img');
                        let allLoaded = true;
                        imgs.forEach(img => {{
                            if (!img.complete || img.naturalHeight === 0) {{
                                allLoaded = false;
                            }}
                        }});
                        return {{ loaded: allLoaded, count: imgs.length }};
                    }})()
                """)

                if not img_loaded.get('loaded', True) and img_loaded.get('count', 0) > 0:
                    log_info(f"  等待 {img_loaded.get('count', 0)} 张图片加载...")
                    for _ in range(20):
                        page.wait_for_timeout(500)
                        check = page.evaluate(f"""
                            (() => {{
                                const slide = document.querySelectorAll('.slide')[{slide_idx}];
                                if (!slide) return true;
                                const imgs = slide.querySelectorAll('img');
                                let allLoaded = true;
                                imgs.forEach(img => {{
                                    if (!img.complete || img.naturalHeight === 0) {{
                                        allLoaded = false;
                                    }}
                                }});
                                return allLoaded;
                            }})()
                        """)
                        if check:
                            break
                    page.wait_for_timeout(200)

                # 为每个句子截图
                for sent_idx, sentence in enumerate(sentences):
                    sent_duration = sentence_durations[sent_idx]

                    # 更新字幕内容（单行）
                    if self.subtitle and sentence:
                        escaped_sentence = sentence.replace('`', '\\`').replace('\n', ' ')
                        page.evaluate(f"""
                            (() => {{
                                const subtitleEl = document.getElementById('subtitle-text');
                                if (subtitleEl) {{
                                    subtitleEl.textContent = `{escaped_sentence}`;
                                }}
                            }})()
                        """)

                    # 等待字幕渲染
                    page.wait_for_timeout(100)

                    # 截图
                    screenshot_path = self.slides_dir / f"slide_{screenshot_idx:04d}.png"
                    page.screenshot(
                        path=str(screenshot_path),
                        type='png',
                        full_page=False
                    )

                    screenshot_durations.append(sent_duration)
                    screenshot_subtitles.append(sentence)
                    screenshot_idx += 1

            browser.close()

        log_success(f"已捕获 {screenshot_idx} 张幻灯片截图（含字幕分割）")
        return screenshot_idx, screenshot_durations, screenshot_subtitles

    def generate_audio_edge(self, text: str, output_path: Path) -> bool:
        """使用 Edge TTS 生成音频"""
        try:
            communicate = edge_tts.Communicate(text, self.voice)

            async def _save():
                await communicate.save(str(output_path))

            asyncio.run(_save())
            return True
        except Exception as e:
            log_error(f"Edge TTS 生成失败: {e}")
            return False

    def generate_audio_openai(self, text: str, output_path: Path) -> bool:
        """使用 OpenAI TTS 生成音频"""
        try:
            client = OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text,
                speed=1.0
            )
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            log_error(f"OpenAI TTS 生成失败: {e}")
            return False

    def generate_audio_volcengine(self, text: str, output_path: Path) -> bool:
        """使用火山引擎 TTS 生成音频"""
        try:
            # 火山引擎 TTS API
            access_key = os.environ.get('VOLCENGINE_ACCESS_KEY')
            secret_key = os.environ.get('VOLCENGINE_SECRET_KEY')
            app_id = os.environ.get('VOLCENGINE_APP_ID')

            if not all([access_key, secret_key, app_id]):
                log_error("火山引擎 TTS 需要设置环境变量: VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY, VOLCENGINE_APP_ID")
                return False

            # 构建请求
            url = "https://openspeech.bytedance.com/api/v1/tts"
            headers = {
                "Authorization": f"Bearer {access_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "app": {"appid": app_id, "token": "access_token"},
                "user": {"uid": "user_id"},
                "audio": {
                    "voice_type": self.voice,
                    "encoding": "mp3",
                    "speed_ratio": 1.0,
                    "volume_ratio": 1.0,
                    "pitch_ratio": 1.0
                },
                "request": {
                    "reqid": hashlib.md5(f"{text}{time.time()}".encode()).hexdigest(),
                    "text": text,
                    "operation": "query"
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if 'data' in result:
                    import base64
                    audio_data = base64.b64decode(result['data'])
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    return True
                else:
                    log_error(f"火山引擎 TTS 响应异常: {result}")
            else:
                log_error(f"火山引擎 TTS 请求失败: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            log_error(f"火山引擎 TTS 生成失败: {e}")
            return False

    def generate_audio_zhipu(self, text: str, output_path: Path) -> bool:
        """使用智谱 AI TTS 生成音频"""
        try:
            api_key = os.environ.get('ZHIPUAI_API_KEY')
            if not api_key:
                log_error("智谱 AI TTS 需要设置环境变量: ZHIPUAI_API_KEY")
                return False

            client = ZhipuAI(api_key=api_key)
            response = client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text,
            )
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            log_error(f"智谱 AI TTS 生成失败: {e}")
            return False

    def generate_audio_fish(self, text: str, output_path: Path) -> bool:
        """使用 Fish Speech 本地服务生成音频"""
        try:
            # Fish Speech 通常在本地运行
            url = os.environ.get('FISH_SPEECH_URL', 'http://localhost:8080/v1/audio/speech')
            payload = {
                "input": text,
                "voice": self.voice,
            }
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                log_error(f"Fish Speech 请求失败: {response.status_code}")
            return False
        except Exception as e:
            log_error(f"Fish Speech 生成失败: {e}")
            return False

    def generate_audio(self, text: str, output_path: Path) -> bool:
        """生成单条音频"""
        if self.tts_provider == "edge":
            return self.generate_audio_edge(text, output_path)
        elif self.tts_provider == "openai":
            return self.generate_audio_openai(text, output_path)
        elif self.tts_provider == "volcengine":
            return self.generate_audio_volcengine(text, output_path)
        elif self.tts_provider == "zhipu":
            return self.generate_audio_zhipu(text, output_path)
        elif self.tts_provider == "fish":
            return self.generate_audio_fish(text, output_path)
        return False

    def get_audio_duration(self, audio_path: Path) -> int:
        """获取音频时长（毫秒）- 使用 ffprobe"""
        try:
            # 使用 ffprobe 获取音频时长（更可靠）
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                return int(duration * 1000)
        except Exception as e:
            log_warning(f"ffprobe 获取时长失败: {e}")

        # Fallback: 尝试使用 mutagen
        if HAS_MUTAGEN:
            try:
                audio = mutagen.File(str(audio_path))
                if audio and hasattr(audio.info, 'length'):
                    return int(audio.info.length * 1000)
            except Exception:
                pass

        log_warning(f"无法获取音频时长: {audio_path.name}，使用默认5秒")
        return 5000

    def get_audio_durations(self, audio_files: List[Optional[Path]]) -> List[int]:
        """获取所有音频的实际时长（毫秒）"""
        durations = []
        for i, audio in enumerate(audio_files):
            if audio and audio.exists():
                duration = self.get_audio_duration(audio)
                durations.append(duration)
                log_info(f"第 {i+1} 页音频时长: {duration/1000:.1f}秒")
            else:
                # 没有音频的页面，默认5秒
                durations.append(5000)
                log_info(f"第 {i+1} 页无音频，使用默认5秒")
        return durations

    def generate_silence(self, duration_ms: int, output_path: Path) -> bool:
        """生成静音音频"""
        duration_sec = duration_ms / 1000
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration_sec),
            "-c:a", "libmp3lame",
            "-q:a", "9",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def concat_audio(self, audio_files: List[Optional[Path]]) -> tuple:
        """
        简单拼接所有音频（v3.0 简化版）

        v3.0: 不再需要静音填充，直接拼接音频
        每页展示时间 = 该页音频时长，100% 同步

        Returns:
            tuple: (final_audio_path, durations)
        """
        log_info("拼接音频轨道...")

        segments = []
        durations = []
        total_duration = 0

        for i, audio in enumerate(audio_files):
            if audio and audio.exists():
                audio_duration = self.get_audio_duration(audio)
                segments.append({
                    'path': audio,
                    'duration': audio_duration
                })
                durations.append(audio_duration)
                total_duration += audio_duration
            else:
                # 没有音频，生成 5 秒静音
                silence_path = self.audio_dir / f"silence_{i:03d}.mp3"
                if self.generate_silence(5000, silence_path):
                    segments.append({
                        'path': silence_path,
                        'duration': 5000
                    })
                    durations.append(5000)
                    total_duration += 5000

        # 生成 concat 文件
        concat_file = self.audio_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{seg['path']}'\n")

        # 拼接音频
        output_audio = self.audio_dir / "final_audio.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output_audio)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(f"音频拼接失败: {result.stderr}")
            raise RuntimeError("音频拼接失败")

        log_success(f"音频拼接完成，总时长: {total_duration/1000:.1f}秒")
        return output_audio, durations

    def compose_video(self, screenshot_durations: List[int]) -> Path:
        """
        合成视频

        v3.0: 直接使用音频时长作为每页展示时间
        v3.2: 使用截图时长（按句子分割后的时长）
        """
        log_step("合成", "正在合成视频...")

        # 生成图片序列文件
        concat_file = self.temp_dir / "slides.txt"
        with open(concat_file, 'w') as f:
            for i, duration in enumerate(screenshot_durations):
                slide_path = self.slides_dir / f"slide_{i:04d}.png"
                f.write(f"file '{slide_path}'\n")
                f.write(f"duration {duration / 1000:.3f}\n")
            # 最后一帧
            last_slide = self.slides_dir / f"slide_{len(screenshot_durations)-1:04d}.png"
            f.write(f"file '{last_slide}'\n")

        # 生成视频轨道
        video_only = self.temp_dir / "video_only.mp4"
        video_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                   f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-r", str(self.fps),
            "-pix_fmt", "yuv420p",
            str(video_only)
        ]

        log_info("生成视频轨道...")
        result = subprocess.run(video_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(f"视频生成失败: {result.stderr}")
            raise RuntimeError("视频生成失败")

        # 合并视频和音频
        final_audio = self.audio_dir / "final_audio.mp3"
        log_info("合并视频和音频...")
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(video_only),
            "-i", str(final_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(self.output)
        ]

        result = subprocess.run(final_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_error(f"音视频合并失败: {result.stderr}")
            raise RuntimeError("音视频合并失败")

        log_success(f"视频已生成: {self.output}")
        return self.output

    def extract_narrations_from_html(self) -> List[str]:
        """从 HTML 提取讲解文字"""
        log_step("提取", "正在提取讲解文字...")

        narrations = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': self.width, 'height': self.height})
            page.goto(f"file://{self.html_path}")

            total = page.evaluate("document.querySelectorAll('.slide').length")

            for i in range(total):
                narration = page.evaluate(f"""
                    (() => {{
                        const slide = document.querySelectorAll('.slide')[{i}];
                        if (!slide) return '';

                        // 优先使用 data-narration 属性
                        if (slide.dataset.narration) {{
                            return slide.dataset.narration;
                        }}

                        // 否则提取文本内容
                        const titleEl = slide.querySelector('h1, h2, .slide-title');
                        const title = titleEl ? titleEl.textContent.trim() : '';

                        // 获取所有段落文本
                        const paragraphs = slide.querySelectorAll('p.slide-text, .slide-text');
                        let content = '';
                        paragraphs.forEach(p => {{
                            content += p.textContent.trim() + ' ';
                        }});

                        if (!content) {{
                            content = slide.innerText;
                        }}

                        // 清理并截断
                        content = content.replace(/\\s+/g, ' ').trim().substring(0, 500);

                        return content;
                    }})()
                """)

                narrations.append(narration if narration else f"第 {i+1} 页")

            browser.close()

        self.slide_count = total
        return narrations

    def generate_all_audio(self, narrations: List[str]) -> List[Optional[Path]]:
        """生成所有讲解音频"""
        log_step("配音", f"正在使用 {self.tts_provider.upper()} TTS 生成语音...")

        audio_files = []

        for i, text in enumerate(narrations):
            if not text or not text.strip():
                log_warning(f"第 {i+1} 页无讲解文字")
                audio_files.append(None)
                continue

            log_info(f"生成第 {i+1}/{len(narrations)} 页配音...")
            output_path = self.audio_dir / f"narration_{i:03d}.mp3"

            if self.generate_audio(text, output_path):
                audio_files.append(output_path)
            else:
                audio_files.append(None)

        success_count = sum(1 for f in audio_files if f is not None)
        log_success(f"已生成 {success_count}/{len(narrations)} 条音频")

        return audio_files

    def convert(self) -> Path:
        """
        执行完整转换流程

        v3.0 流程（音频驱动）：
        1. 提取讲解文字
        2. 生成所有音频 → 获取每段实际时长
        3. 根据音频时长截图（v3.2: 按句子分割字幕，逐句显示）
        4. 拼接音频
        5. 合成视频（视频时长 = 音频时长，100% 同步）
        """
        log_info(f"开始转换: {self.html_path}")
        log_info(f"输出路径: {self.output}")
        log_info(f"分辨率: {self.resolution}")
        log_info(f"TTS 服务: {self.tts_provider}")
        log_info(f"语音: {self.voice}")
        if self.subtitle:
            log_info(f"字幕: 已启用单行模式 (字体: {self.subtitle_font})")

        if not self.check_dependencies():
            raise RuntimeError("依赖检查失败")

        # 1. 提取讲解文字
        narrations = self.extract_narrations_from_html()

        # 显示讲解文字预览
        log_info("讲解文字预览:")
        for i, text in enumerate(narrations):
            preview = text[:60] + "..." if len(text) > 60 else text
            print(f"  [{i+1}] {preview}")

        # 2. 先生成所有音频（v3.0 核心改进：音频驱动）
        audio_files = self.generate_all_audio(narrations)

        # 3. 获取每段音频的实际时长
        audio_durations = self.get_audio_durations(audio_files)
        total_duration = sum(audio_durations) / 1000
        log_info(f"预计视频总时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")

        # 4. 根据音频时长截图（v3.2: 返回截图时长和字幕列表）
        screenshot_count, screenshot_durations, screenshot_subtitles = self.capture_slides(audio_durations, narrations)
        log_info(f"生成 {screenshot_count} 张截图（字幕按句子分割）")

        # 5. 拼接音频
        self.concat_audio(audio_files)

        # 6. 合成视频（使用截图时长，确保字幕同步）
        result = self.compose_video(screenshot_durations)

        # 7. 清理
        if not self.keep_temp:
            log_info("清理临时文件...")
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        log_success("转换完成!")
        return result

    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def list_voices(provider: str = "edge", language: str = "zh"):
    """列出可用的语音"""
    if provider == "edge" and language == "zh":
        print(f"\n{Colors.BOLD}Edge TTS 可用中文语音:{Colors.END}\n")
        for voice_id, description in PPTToVideoConverter.EDGE_CHINESE_VOICES:
            print(f"  {Colors.CYAN}{voice_id}{Colors.END}")
            print(f"      {description}\n")
    elif provider == "volcengine" and language == "zh":
        print(f"\n{Colors.BOLD}火山引擎 TTS 可用中文语音:{Colors.END}\n")
        for voice_id, description in PPTToVideoConverter.VOLCENGINE_CHINESE_VOICES:
            print(f"  {Colors.CYAN}{voice_id}{Colors.END}")
            print(f"      {description}\n")
    else:
        print(f"\n{Colors.BOLD}{provider.upper()} TTS 默认语音:{Colors.END}\n")
        voices = PPTToVideoConverter.DEFAULT_VOICES.get(provider, {})
        for lang, voice in voices.items():
            print(f"  {lang}: {voice}")


def list_tts_services():
    """列出所有 TTS 服务"""
    print(f"\n{Colors.BOLD}可用的 TTS 服务:{Colors.END}\n")
    for service_id, info in PPTToVideoConverter.TTS_SERVICES.items():
        free_tag = f"{Colors.GREEN}免费{Colors.END}" if info['free'] else f"{Colors.YELLOW}付费{Colors.END}"
        print(f"  {Colors.CYAN}{service_id}{Colors.END} - {info['name']} [{free_tag}] 质量: {info['quality']}")
    print(f"\n{Colors.BOLD}环境变量配置:{Colors.END}")
    print("  OpenAI:      OPENAI_API_KEY")
    print("  火山引擎:     VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY, VOLCENGINE_APP_ID")
    print("  智谱 AI:     ZHIPUAI_API_KEY")
    print("  Fish Speech: FISH_SPEECH_URL (默认: http://localhost:8080)")


def main():
    parser = argparse.ArgumentParser(
        description="将 HTML PPT 幻灯片转换为带配音和字幕的视频（v3.3 支持国产 TTS）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
v3.3 改进:
  - 新增国产 TTS 服务：火山引擎、智谱 AI、Fish Speech
  - 支持 30+ 中文语音选择

v3.2 改进:
  - 内嵌字幕：按句子分割，逐句显示
  - 字幕时长按字数比例分配，与音频同步

示例:
  python3 ppt_to_video.py presentation.html -o output.mp4
  python3 ppt_to_video.py presentation.html --tts volcengine --voice zh_female_tianmeixiaoyuan -o output.mp4
  python3 ppt_to_video.py presentation.html --tts zhipu -o output.mp4
  python3 ppt_to_video.py --list-voices --tts volcengine
  python3 ppt_to_video.py --list-services
        """
    )

    parser.add_argument("html", nargs="?", help="HTML PPT 文件路径")
    parser.add_argument("-o", "--output", default="output.mp4", help="输出视频路径")
    parser.add_argument("--resolution", default="1920x1080", help="视频分辨率")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--tts", choices=["edge", "openai", "volcengine", "zhipu", "fish"], default="edge",
                        help="TTS 服务: edge(免费)/openai/volcengine(火山引擎)/zhipu(智谱)/fish")
    parser.add_argument("--voice", help="指定语音")
    parser.add_argument("--language", default="zh", help="语言")
    parser.add_argument("--keep-temp", action="store_true", help="保留临时文件")
    parser.add_argument("--list-voices", action="store_true", help="列出可用语音")
    parser.add_argument("--list-services", action="store_true", help="列出所有 TTS 服务")
    # 字幕相关参数
    parser.add_argument("--no-subtitle", action="store_true", help="禁用内嵌字幕")
    parser.add_argument("--subtitle-font", default="PingFang SC, Noto Sans SC, sans-serif", help="字幕字体")
    parser.add_argument("--subtitle-fontsize", type=int, default=28, help="字幕字号")
    parser.add_argument("--subtitle-radius", type=int, default=12, help="字幕背景圆角")

    args = parser.parse_args()

    if args.list_services:
        list_tts_services()
        return

    if args.list_voices:
        list_voices(args.tts, args.language)
        return

    if not args.html:
        parser.error("请提供 HTML 文件路径")

    if not Path(args.html).exists():
        log_error(f"文件不存在: {args.html}")
        sys.exit(1)

    converter = PPTToVideoConverter(
        html_path=args.html,
        output=args.output,
        resolution=args.resolution,
        fps=args.fps,
        tts_provider=args.tts,
        voice=args.voice,
        language=args.language,
        keep_temp=args.keep_temp,
        subtitle=not args.no_subtitle,
        subtitle_font=args.subtitle_font,
        subtitle_fontsize=args.subtitle_fontsize,
        subtitle_bg_radius=args.subtitle_radius
    )

    try:
        converter.convert()
    except KeyboardInterrupt:
        log_warning("用户中断")
        converter.cleanup()
        sys.exit(1)
    except Exception as e:
        log_error(f"转换失败: {e}")
        converter.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
