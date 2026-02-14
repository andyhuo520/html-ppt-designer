#!/usr/bin/env python3
"""
音频/视频语音转录模块
Transcribe audio from YouTube, 小宇宙 podcasts, or direct audio URLs.

Supports three transcription modes:
  - local:  MLX-Whisper on Apple Silicon (free, ~25min/1hr audio)
  - api:    OpenAI Whisper API ($0.006/min, ~3min/1hr audio)
  - gemini: Gemini Flash API (~$0.001/min, ~2min/1hr audio)

Usage:
  python3 transcribe_audio.py "https://youtu.be/xxx"
  python3 transcribe_audio.py "https://www.xiaoyuzhoufm.com/episode/xxx" --mode local
  python3 transcribe_audio.py "https://example.com/audio.mp3" --mode api --language en
  python3 transcribe_audio.py "/path/to/local/file.mp3" --mode local

Dependencies:
  Required: ffmpeg
  For download: yt-dlp (brew install yt-dlp)
  For local mode: pip install mlx-whisper
  For api mode: OPENAI_API_KEY env var
  For gemini mode: GEMINI_API_KEY env var
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORK_DIR = Path(tempfile.gettempdir()) / "audio-transcribe"
WORK_DIR.mkdir(exist_ok=True)

MLX_MODELS = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large": "mlx-community/whisper-large-v3-mlx",
    "small": "mlx-community/whisper-small-mlx",
}

SUPPORTED_AUDIO_EXT = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac", ".wma", ".opus", ".webm"}

# ---------------------------------------------------------------------------
# URL classification
# ---------------------------------------------------------------------------

def classify_url(url: str) -> str:
    """Classify input as youtube / xiaoyuzhou / audio_url / local_file."""
    if os.path.isfile(url):
        return "local_file"
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "xiaoyuzhoufm.com" in host:
        return "xiaoyuzhou"
    # Check if URL ends with audio extension
    path_ext = Path(parsed.path).suffix.lower()
    if path_ext in SUPPORTED_AUDIO_EXT:
        return "audio_url"
    # Default: try yt-dlp (it supports many sites)
    return "generic"


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

def check_dependency(cmd: str, install_hint: str) -> bool:
    """Check if a command is available, print install hint if not."""
    if shutil.which(cmd):
        return True
    print(f"[ERROR] '{cmd}' not found. Install with: {install_hint}", file=sys.stderr)
    return False


def ensure_yt_dlp():
    if not check_dependency("yt-dlp", "brew install yt-dlp"):
        print("[INFO] Attempting auto-install via brew...", file=sys.stderr)
        r = subprocess.run(["brew", "install", "yt-dlp"], capture_output=True, text=True)
        if r.returncode != 0:
            print("[ERROR] Auto-install failed. Please install manually.", file=sys.stderr)
            sys.exit(1)
        print("[OK] yt-dlp installed.", file=sys.stderr)


def ensure_ffmpeg():
    if not check_dependency("ffmpeg", "brew install ffmpeg"):
        sys.exit(1)


def ensure_mlx_whisper():
    try:
        import mlx_whisper  # noqa: F401
        return True
    except ImportError:
        print("[INFO] mlx-whisper not installed. Installing...", file=sys.stderr)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "mlx-whisper"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"[ERROR] Failed to install mlx-whisper:\n{r.stderr}", file=sys.stderr)
            return False
        print("[OK] mlx-whisper installed.", file=sys.stderr)
        return True


# ---------------------------------------------------------------------------
# Audio download
# ---------------------------------------------------------------------------

def download_youtube(url: str) -> Path:
    """Download audio from YouTube using yt-dlp."""
    ensure_yt_dlp()
    out_template = str(WORK_DIR / "%(title).80s.%(ext)s")
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "--no-playlist", "--no-overwrites",
        "-o", out_template,
        url,
    ]
    print(f"[DOWNLOAD] YouTube audio...", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[ERROR] yt-dlp failed:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)

    # Find the downloaded file
    for line in r.stdout.splitlines():
        # yt-dlp prints: [ExtractAudio] Destination: /path/to/file.mp3
        if "Destination:" in line:
            path = line.split("Destination:")[-1].strip()
            if os.path.isfile(path):
                return Path(path)
    # Fallback: find most recent mp3 in work dir
    mp3s = sorted(WORK_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if mp3s:
        return mp3s[0]
    print("[ERROR] Could not find downloaded audio file.", file=sys.stderr)
    sys.exit(1)


def download_xiaoyuzhou(url: str) -> Path:
    """Download audio from 小宇宙 podcast."""
    # Try yt-dlp first (it may support xiaoyuzhou)
    ensure_yt_dlp()
    out_template = str(WORK_DIR / "%(title).80s.%(ext)s")
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", out_template,
        url,
    ]
    print(f"[DOWNLOAD] Trying yt-dlp for 小宇宙...", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        mp3s = sorted(WORK_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp3s:
            return mp3s[0]

    # Fallback: extract audio URL from page HTML
    print("[INFO] yt-dlp failed for 小宇宙, trying HTML parsing...", file=sys.stderr)
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Try to extract audio URL from various patterns
        audio_url = None

        # Pattern 1: JSON-LD or inline JSON with enclosure/media URL
        m4a_matches = re.findall(r'https?://[^"\'<>\s]+\.m4a[^"\'<>\s]*', html)
        mp3_matches = re.findall(r'https?://[^"\'<>\s]+\.mp3[^"\'<>\s]*', html)

        for candidates in [mp3_matches, m4a_matches]:
            if candidates:
                audio_url = candidates[0]
                break

        # Pattern 2: Look in JSON data for "mediaUrl" or "enclosure"
        if not audio_url:
            json_patterns = re.findall(r'"(?:mediaUrl|enclosure|url)":\s*"(https?://[^"]+)"', html)
            for candidate in json_patterns:
                ext = Path(urlparse(candidate).path).suffix.lower()
                if ext in SUPPORTED_AUDIO_EXT:
                    audio_url = candidate
                    break

        if not audio_url:
            print("[ERROR] Could not extract audio URL from 小宇宙 page.", file=sys.stderr)
            print("[HINT] Try copying the audio URL directly and passing it as input.", file=sys.stderr)
            sys.exit(1)

        # Download the audio file
        print(f"[DOWNLOAD] Found audio URL, downloading...", file=sys.stderr)
        ext = Path(urlparse(audio_url).path).suffix or ".m4a"
        out_path = WORK_DIR / f"xiaoyuzhou_episode{ext}"
        audio_resp = requests.get(audio_url, headers=headers, timeout=120, stream=True)
        audio_resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in audio_resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[OK] Downloaded to {out_path}", file=sys.stderr)
        return out_path

    except ImportError:
        print("[ERROR] 'requests' module required. Install: pip install requests", file=sys.stderr)
        sys.exit(1)


def download_audio_url(url: str) -> Path:
    """Download audio from a direct URL."""
    ext = Path(urlparse(url).path).suffix or ".mp3"
    out_path = WORK_DIR / f"direct_audio{ext}"
    print(f"[DOWNLOAD] Direct audio URL...", file=sys.stderr)
    try:
        import requests
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return out_path
    except ImportError:
        # Fallback to curl
        r = subprocess.run(["curl", "-L", "-o", str(out_path), url], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[ERROR] Download failed:\n{r.stderr}", file=sys.stderr)
            sys.exit(1)
        return out_path


def download_generic(url: str) -> Path:
    """Try yt-dlp for generic URLs."""
    ensure_yt_dlp()
    out_template = str(WORK_DIR / "%(title).80s.%(ext)s")
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", out_template, url,
    ]
    print(f"[DOWNLOAD] Trying yt-dlp for generic URL...", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        mp3s = sorted(WORK_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp3s:
            return mp3s[0]
    print("[ERROR] Could not download audio from this URL.", file=sys.stderr)
    sys.exit(1)


def get_audio_file(url: str) -> Path:
    """Route to the correct download method based on URL type."""
    source_type = classify_url(url)
    print(f"[INFO] Source type: {source_type}", file=sys.stderr)

    if source_type == "local_file":
        return Path(url)
    elif source_type == "youtube":
        return download_youtube(url)
    elif source_type == "xiaoyuzhou":
        return download_xiaoyuzhou(url)
    elif source_type == "audio_url":
        return download_audio_url(url)
    else:
        return download_generic(url)


# ---------------------------------------------------------------------------
# Audio preprocessing
# ---------------------------------------------------------------------------

def preprocess_audio(audio_path: Path, target_format: str = "wav") -> Path:
    """Convert audio to Whisper-optimal format: 16kHz mono WAV."""
    ensure_ffmpeg()
    out_path = WORK_DIR / f"preprocessed.{target_format}"

    if target_format == "wav":
        cmd = [
            "ffmpeg", "-i", str(audio_path),
            "-ac", "1", "-ar", "16000",
            "-y", str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-i", str(audio_path),
            "-y", str(out_path),
        ]

    print(f"[PREPROCESS] Converting to {target_format}...", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[WARN] ffmpeg conversion failed, using original file.", file=sys.stderr)
        return audio_path
    return out_path


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def split_audio(audio_path: Path, chunk_seconds: int = 600) -> list:
    """Split audio into chunks for API upload limits."""
    ensure_ffmpeg()
    chunk_dir = WORK_DIR / "chunks"
    chunk_dir.mkdir(exist_ok=True)

    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-f", "segment", "-segment_time", str(chunk_seconds),
        "-c", "copy",
        str(chunk_dir / "chunk_%03d.wav"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return [audio_path]  # Fallback: use whole file

    chunks = sorted(chunk_dir.glob("chunk_*.wav"))
    return chunks if chunks else [audio_path]


# ---------------------------------------------------------------------------
# Transcription modes
# ---------------------------------------------------------------------------

def transcribe_local(audio_path: Path, language: str = "zh",
                     model_size: str = "turbo") -> dict:
    """Transcribe using MLX-Whisper locally on Apple Silicon."""
    if not ensure_mlx_whisper():
        print("[ERROR] Cannot use local mode without mlx-whisper.", file=sys.stderr)
        sys.exit(1)

    import mlx_whisper

    model_path = MLX_MODELS.get(model_size, MLX_MODELS["turbo"])
    lang = None if language == "auto" else language

    print(f"[TRANSCRIBE] Local mode with {model_size} model...", file=sys.stderr)
    print(f"[INFO] Model: {model_path}", file=sys.stderr)
    print(f"[INFO] This may take a while for long audio.", file=sys.stderr)

    start_time = time.time()

    try:
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_path,
            language=lang,
            verbose=False,
        )
    except Exception as e:
        if "memory" in str(e).lower() or "oom" in str(e).lower():
            print(f"[WARN] OOM with {model_size}, falling back to small model...", file=sys.stderr)
            result = mlx_whisper.transcribe(
                str(audio_path),
                path_or_hf_repo=MLX_MODELS["small"],
                language=lang,
                verbose=False,
            )
        else:
            raise

    elapsed = time.time() - start_time
    print(f"[OK] Transcription completed in {elapsed:.1f}s", file=sys.stderr)

    return {
        "text": result.get("text", ""),
        "segments": result.get("segments", []),
        "language": result.get("language", language),
        "mode": "local",
        "model": model_path,
        "processing_time": f"{elapsed:.1f}s",
    }


def transcribe_api(audio_path: Path, language: str = "zh") -> dict:
    """Transcribe using OpenAI Whisper API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set. Set it or use --mode local.", file=sys.stderr)
        sys.exit(1)

    # Check file size - API limit is 25MB
    file_size = audio_path.stat().st_size
    if file_size > 25 * 1024 * 1024:
        print(f"[INFO] File too large ({file_size/1024/1024:.1f}MB), splitting...", file=sys.stderr)
        chunks = split_audio(audio_path)
    else:
        chunks = [audio_path]

    print(f"[TRANSCRIBE] API mode ({len(chunks)} chunk(s))...", file=sys.stderr)
    start_time = time.time()

    all_segments = []
    all_text = []
    time_offset = 0.0

    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  Processing chunk {i+1}/{len(chunks)}...", file=sys.stderr)

        cmd = [
            "curl", "-s",
            "https://api.openai.com/v1/audio/transcriptions",
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{chunk}",
            "-F", "model=whisper-1",
            "-F", f"language={language}" if language != "auto" else "",
            "-F", "response_format=verbose_json",
            "-F", "timestamp_granularities[]=segment",
        ]
        cmd = [c for c in cmd if c]  # Remove empty strings

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[ERROR] API call failed:\n{r.stderr}", file=sys.stderr)
            sys.exit(1)

        try:
            result = json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid API response:\n{r.stdout[:500]}", file=sys.stderr)
            sys.exit(1)

        if "error" in result:
            print(f"[ERROR] API error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        all_text.append(result.get("text", ""))
        for seg in result.get("segments", []):
            seg["start"] += time_offset
            seg["end"] += time_offset
            all_segments.append(seg)

        # Update time offset for next chunk
        if all_segments:
            time_offset = all_segments[-1]["end"]

    elapsed = time.time() - start_time
    print(f"[OK] Transcription completed in {elapsed:.1f}s", file=sys.stderr)

    return {
        "text": " ".join(all_text),
        "segments": all_segments,
        "language": language,
        "mode": "api",
        "model": "whisper-1",
        "processing_time": f"{elapsed:.1f}s",
    }


def transcribe_gemini(audio_path: Path, language: str = "zh",
                      generate_summary: bool = False) -> dict:
    """Transcribe using Gemini Flash API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set. Set it or use --mode local.", file=sys.stderr)
        sys.exit(1)

    # Determine mime type
    ext = audio_path.suffix.lower()
    mime_map = {
        ".mp3": "audio/mp3", ".m4a": "audio/mp4", ".wav": "audio/wav",
        ".flac": "audio/flac", ".ogg": "audio/ogg", ".aac": "audio/aac",
        ".opus": "audio/opus", ".webm": "audio/webm",
    }
    mime_type = mime_map.get(ext, "audio/mp3")

    print(f"[TRANSCRIBE] Gemini mode...", file=sys.stderr)
    start_time = time.time()

    # Step 1: Upload file
    print(f"  Uploading audio file...", file=sys.stderr)
    upload_cmd = [
        "curl", "-s", "-X", "POST",
        f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}",
        "-H", f"Content-Type: {mime_type}",
        "--data-binary", f"@{audio_path}",
    ]
    r = subprocess.run(upload_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[ERROR] Upload failed:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        upload_result = json.loads(r.stdout)
        file_uri = upload_result.get("file", {}).get("uri")
    except (json.JSONDecodeError, KeyError):
        print(f"[ERROR] Invalid upload response:\n{r.stdout[:500]}", file=sys.stderr)
        sys.exit(1)

    if not file_uri:
        print(f"[ERROR] No file URI in response:\n{r.stdout[:500]}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Request transcription
    lang_name = {"zh": "中文", "en": "English", "auto": "原始语言"}.get(language, language)

    prompt = f"请将这段音频完整转录为{lang_name}文字。要求：\n1. 保留自然段落划分\n2. 如果能识别出多个说话人，标注说话人（如 A:、B:）\n3. 不要遗漏任何内容"

    if generate_summary:
        prompt += "\n\n转录完成后，请在末尾添加：\n---\n## 摘要\n### 核心观点\n- ...\n### 关键信息\n- ..."

    request_body = json.dumps({
        "contents": [{
            "parts": [
                {"file_data": {"file_uri": file_uri, "mime_type": mime_type}},
                {"text": prompt},
            ]
        }]
    })

    print(f"  Requesting transcription...", file=sys.stderr)
    gen_cmd = [
        "curl", "-s",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
        "-H", "Content-Type: application/json",
        "-d", request_body,
    ]
    r = subprocess.run(gen_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[ERROR] Gemini API failed:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        gen_result = json.loads(r.stdout)
        text = gen_result["candidates"][0]["content"]["parts"][0]["text"]
    except (json.JSONDecodeError, KeyError, IndexError):
        print(f"[ERROR] Invalid Gemini response:\n{r.stdout[:500]}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"[OK] Transcription completed in {elapsed:.1f}s", file=sys.stderr)

    return {
        "text": text,
        "segments": [],  # Gemini doesn't return timestamps
        "language": language,
        "mode": "gemini",
        "model": "gemini-2.0-flash",
        "processing_time": f"{elapsed:.1f}s",
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_markdown(result: dict, source_url: str, duration: float) -> str:
    """Format transcription result as Markdown."""
    lines = []
    lines.append(f"# 转录文本\n")
    lines.append(f"> 来源: {source_url}")
    lines.append(f"> 时长: {format_timestamp(duration)}")
    lines.append(f"> 转录模式: {result['mode']} ({result['model']})")
    lines.append(f"> 处理时间: {result['processing_time']}")
    lines.append(f"\n---\n")
    lines.append(f"## 内容\n")
    lines.append(result["text"])

    # Add timeline if segments available
    if result["segments"]:
        lines.append(f"\n---\n")
        lines.append(f"## 时间轴\n")
        # Group into ~5min sections for overview
        prev_time = -300  # Force first entry
        for seg in result["segments"]:
            if seg["start"] - prev_time >= 300:  # Every 5 minutes
                text_preview = seg["text"].strip()[:60]
                lines.append(f"- [{format_timestamp(seg['start'])}] {text_preview}...")
                prev_time = seg["start"]

    return "\n".join(lines)


def format_srt(result: dict) -> str:
    """Format transcription result as SRT subtitles."""
    if not result["segments"]:
        return result["text"]

    lines = []
    for i, seg in enumerate(result["segments"], 1):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        if not text:
            continue
        sh, sm, ss, sms = int(start//3600), int(start%3600//60), int(start%60), int((start%1)*1000)
        eh, em, es, ems = int(end//3600), int(end%3600//60), int(end%60), int((end%1)*1000)
        lines.append(str(i))
        lines.append(f"{sh:02d}:{sm:02d}:{ss:02d},{sms:03d} --> {eh:02d}:{em:02d}:{es:02d},{ems:03d}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def format_output(result: dict, fmt: str, source_url: str, duration: float) -> str:
    """Format transcription result based on requested format."""
    if fmt == "markdown":
        return format_markdown(result, source_url, duration)
    elif fmt == "srt":
        return format_srt(result)
    elif fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:  # txt
        return result["text"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="音频/视频语音转录 - 支持 YouTube、小宇宙播客、直接音频链接和本地文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://youtu.be/dQw4w9WgXcQ"
  %(prog)s "https://www.xiaoyuzhoufm.com/episode/xxx" --mode local
  %(prog)s "https://example.com/podcast.mp3" --mode api --language en
  %(prog)s "/path/to/audio.mp3" --mode local --output transcript.md
  %(prog)s "https://youtu.be/xxx" --mode gemini --summary
        """,
    )
    parser.add_argument("url", help="音频/视频 URL 或本地文件路径")
    parser.add_argument("--mode", choices=["local", "api", "gemini"], default="local",
                        help="转录模式 (default: local)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", choices=["markdown", "srt", "txt", "json"], default="markdown",
                        help="输出格式 (default: markdown)")
    parser.add_argument("--language", default="zh",
                        help="音频语言: zh/en/auto (default: zh)")
    parser.add_argument("--model-size", choices=["turbo", "large", "small"], default="turbo",
                        help="本地模型大小 (default: turbo)")
    parser.add_argument("--summary", action="store_true",
                        help="生成内容摘要 (gemini 模式自带)")
    parser.add_argument("--no-preprocess", action="store_true",
                        help="跳过音频预处理")

    args = parser.parse_args()

    # Step 1: Download/locate audio
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"  Audio Transcription Tool", file=sys.stderr)
    print(f"  Mode: {args.mode} | Language: {args.language}", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)

    audio_path = get_audio_file(args.url)
    print(f"[OK] Audio file: {audio_path} ({audio_path.stat().st_size/1024/1024:.1f}MB)", file=sys.stderr)

    # Step 2: Get duration
    duration = get_audio_duration(audio_path)
    if duration > 0:
        print(f"[INFO] Duration: {format_timestamp(duration)}", file=sys.stderr)

    # Step 3: Preprocess
    if not args.no_preprocess and args.mode == "local":
        audio_path = preprocess_audio(audio_path, "wav")
    elif not args.no_preprocess and args.mode == "api":
        # API accepts mp3, but check size
        if audio_path.stat().st_size > 25 * 1024 * 1024:
            audio_path = preprocess_audio(audio_path, "wav")

    # Step 4: Transcribe
    if args.mode == "local":
        result = transcribe_local(audio_path, args.language, args.model_size)
    elif args.mode == "api":
        result = transcribe_api(audio_path, args.language)
    elif args.mode == "gemini":
        result = transcribe_gemini(audio_path, args.language, args.summary)

    # Step 5: Format output
    output = format_output(result, args.format, args.url, duration)

    # Step 6: Write or print
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n[OK] Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)

    # Print summary
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"  Transcription Complete", file=sys.stderr)
    print(f"  Mode: {result['mode']} | Model: {result['model']}", file=sys.stderr)
    print(f"  Processing time: {result['processing_time']}", file=sys.stderr)
    print(f"  Text length: {len(result['text'])} chars", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)

    return result


if __name__ == "__main__":
    main()
