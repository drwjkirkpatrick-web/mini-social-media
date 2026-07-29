"""
Agent automated moderation.
NOTE: Scores posts 0-100. <30 clean, 30-70 flagged, >70 rejected.
WHY: Catches obvious spam/hate before human review.
"""

import re
from typing import Tuple
from config import get_config


def moderate_text(text: str) -> Tuple[int, str]:
    """Return (score, reason). Lower is better."""
    if not text:
        return 0, ""
    cfg = get_config()
    score = 0
    reasons = []
    lower = text.lower()

    # Keyword scoring
    for keyword in cfg.moderation_keywords:
        count = lower.count(keyword.lower())
        if count > 0:
            score += count * 25
            reasons.append(f"keyword '{keyword}' ({count}x)")

    # Regex pattern scoring
    for pattern in cfg.moderation_regex_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            score += len(matches) * 15
            reasons.append(f"pattern match ({len(matches)}x)")

    # Caps lock penalty
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.7:
        score += 10
        reasons.append("excessive caps")

    reason = "; ".join(reasons) if reasons else ""
    return min(score, 100), reason


def status_from_score(score: int) -> str:
    if score < 30:
        return "approved"
    if score <= 70:
        return "pending"
    return "rejected"
