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
