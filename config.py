"""
mini-social-media configuration module.
NOTE: All settings load from environment variables with sensible defaults.
WHY: Keeps secrets out of source code and allows per-environment tuning.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Config:
    """Application configuration. Load once at startup."""
    # Database
    database_path: str = "data/social.db"

    # Security
    secret_key: str = field(default_factory=lambda: os.urandom(32).hex())
    hermes_webhook_secret: str = "change-me-in-production"

    # Uploads
    max_file_size_mb: int = 10
    allowed_photo_extensions: tuple = (
        "jpg", "jpeg", "png", "gif", "webp", "heic",
    )
    upload_folder: str = "static/uploads"

    # Rate limiting (login)
    rate_limit_login_attempts: int = 10
    rate_limit_window_seconds: int = 300  # 5 minutes

    # Moderation
    moderation_keywords: List[str] = field(default_factory=lambda: [
        "spam", "scam", "hate", "kill", "attack", "threat",
    ])
    moderation_regex_patterns: List[str] = field(default_factory=lambda: [
        r"(https?://)?(bit\.ly|tinyurl|t\.co)/\S+",  # URL shorteners
    ])

    # Feed
    feed_default_limit: int = 50
    feed_max_limit: int = 200

    @classmethod
    def from_env(cls) -> "Config":
        """Build config from environment variables with defaults."""
        def _int(name: str, default: int) -> int:
            val = os.environ.get(name)
            return int(val) if val is not None else default

        def _list(name: str, default: List[str]) -> List[str]:
            val = os.environ.get(name)
            return [x.strip() for x in val.split(",") if x.strip()] if val else default

        return cls(
            database_path=os.environ.get("MINI_SOCIAL_DB", "data/social.db"),
            secret_key=os.environ.get("MINI_SOCIAL_SECRET", os.urandom(32).hex()),
            hermes_webhook_secret=os.environ.get("MINI_SOCIAL_HERMES_SECRET", "change-me-in-production"),
            max_file_size_mb=_int("MINI_SOCIAL_MAX_FILE_MB", 10),
            rate_limit_login_attempts=_int("MINI_SOCIAL_LOGIN_ATTEMPTS", 10),
            rate_limit_window_seconds=_int("MINI_SOCIAL_LOGIN_WINDOW", 300),
            moderation_keywords=_list("MINI_SOCIAL_MOD_KEYWORDS", [
                "spam", "scam", "hate", "kill", "attack", "threat",
            ]),
            moderation_regex_patterns=_list("MINI_SOCIAL_MOD_PATTERNS", [
                r"(https?://)?(bit\.ly|tinyurl|t\.co)/\S+",
            ]),
            feed_default_limit=_int("MINI_SOCIAL_FEED_LIMIT", 50),
        )


def get_config() -> Config:
    """Singleton accessor. Returns the same config instance per process."""
    if not hasattr(get_config, "_instance"):
        get_config._instance = Config.from_env()
    return get_config._instance
