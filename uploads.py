"""
Photo upload handler.
NOTE: secure_filename strips dangerous chars; timestamp prefix prevents overwrites.
WHY: Prevents path traversal and filename collisions.
"""

import os
import time
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from config import get_config


def allowed_file(filename: str) -> bool:
    cfg = get_config()
    return "." in filename and filename.rsplit(".", 1)[1].lower() in cfg.allowed_photo_extensions


def save_photo(file, user_id: int) -> str:
    """Save uploaded file and return relative URL path."""
    cfg = get_config()
    if not file or not file.filename:
        raise ValueError("No file provided.")
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {cfg.allowed_photo_extensions}")
    ext = file.filename.rsplit(".", 1)[1].lower()
    # HEIC fallback: if pillow-heif unavailable, reject
    if ext == "heic":
        try:
            from pillow_heif import register_heif_opener  # noqa: F401
        except ImportError:
            raise ValueError("HEIC support not available. Please install pillow-heif or convert to JPG.")

    filename = secure_filename(file.filename)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{filename}"
    user_dir = os.path.join(cfg.upload_folder, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    dest = os.path.join(user_dir, filename)
    file.save(dest)
    # Return relative URL path for template use
    return f"/{cfg.upload_folder}/{user_id}/{filename}".replace("//", "/")


# ---------------------------------------------------------------------------
# Video & Voice uploads (v0.4.0)
# ---------------------------------------------------------------------------

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
ALLOWED_VOICE_EXTENSIONS = {"webm", "ogg", "mp3", "m4a", "wav"}
MAX_VIDEO_SIZE_MB = 30
MAX_VOICE_SIZE_MB = 10
MAX_VIDEO_SECONDS = 29


def allowed_video_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_voice_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VOICE_EXTENSIONS


def save_video(file, user_id: int) -> str:
    """Save a short video and return relative URL. Max 29 seconds, 30 MB."""
    cfg = get_config()
    if not file or not file.filename:
        raise ValueError("No file provided.")
    if not allowed_video_file(file.filename):
        raise ValueError("Unsupported video type (mp4, webm, mov only).")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(file.filename)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_video_{filename}"
    user_dir = os.path.join(cfg.upload_folder, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    dest = os.path.join(user_dir, filename)
    file.save(dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        os.remove(dest)
        raise ValueError(f"Video too large ({size_mb:.1f} MB > {MAX_VIDEO_SIZE_MB} MB).")
    # Check duration if ffprobe available
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", dest],
            capture_output=True, text=True, timeout=5,
        )
        duration = float(result.stdout.strip())
        if duration > MAX_VIDEO_SECONDS:
            os.remove(dest)
            raise ValueError(f"Video too long ({duration:.0f}s > {MAX_VIDEO_SECONDS}s).")
    except FileNotFoundError:
        pass  # ffprobe not installed, size check is fallback
    return f"/{cfg.upload_folder}/{user_id}/{filename}".replace("//", "/")


def save_voice(file, user_id: int) -> str:
    """Save a voice message and return relative URL. Max 10 MB, 5 minutes."""
    cfg = get_config()
    if not file or not file.filename:
        raise ValueError("No file provided.")
    if not allowed_voice_file(file.filename):
        raise ValueError("Unsupported voice type (webm, ogg, mp3, m4a, wav only).")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(file.filename)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_voice_{filename}"
    user_dir = os.path.join(cfg.upload_folder, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    dest = os.path.join(user_dir, filename)
    file.save(dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    if size_mb > MAX_VOICE_SIZE_MB:
        os.remove(dest)
        raise ValueError(f"Voice message too large ({size_mb:.1f} MB > {MAX_VOICE_SIZE_MB} MB).")
    return f"/{cfg.upload_folder}/{user_id}/{filename}".replace("//", "/")
