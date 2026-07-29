"""
Feed engine.
NOTE: Returns posts from friends + self, excluding blocked users.
WHY: Privacy-first — no public posts.
"""

from typing import List, Dict, Any
from database import get_connection


def get_feed(user_id: int, sort: str = "newest", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    # Get blocked user IDs
    blocked_rows = conn.execute("SELECT target_id FROM blocks WHERE user_id=?", (user_id,)).fetchall()
    blocked = [r["target_id"] for r in blocked_rows]
    blocked_placeholders = ",".join("?" for _ in blocked) if blocked else ""

    order = "DESC" if sort == "newest" else "ASC"
    sql = f"""
        SELECT p.*, u.username, u.display_name, u.avatar_url
        FROM posts p
        JOIN users u ON u.id = p.user_id
        WHERE p.moderation_status = 'approved'
          AND p.is_draft = 0
          AND p.is_scheduled = 0
          AND p.expires_at IS NULL
          AND (
              p.user_id = ?
              OR (
                  p.visibility = 'friends'
                  AND EXISTS (
                      SELECT 1 FROM friendships f
                      WHERE f.status = 'accepted'
                        AND ((f.requester_id = ? AND f.addressee_id = p.user_id)
                             OR (f.addressee_id = ? AND f.requester_id = p.user_id))
                  )
              )
              OR (
                  p.visibility = 'only_me' AND p.user_id = ?
              )
          )
          {"AND p.user_id NOT IN ({blocked_placeholders})" if blocked else ""}
        ORDER BY p.created_at {order}
        LIMIT ? OFFSET ?
    """
    params = [user_id, user_id, user_id, user_id] + blocked + [limit, offset]
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    posts = []
    for r in rows:
        d = dict(r)
        d["like_count"] = _count_likes(d["id"])
        d["comment_count"] = _count_comments(d["id"])
        d["reactions"] = _get_reactions(d["id"])
        d["engagement_score"] = d["like_count"]*2 + d["comment_count"]*3 + sum(d["reactions"].values())
        posts.append(d)

    if sort == "engaged":
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        def _score(post):
            hours = 1
            try:
                created = datetime.fromisoformat(post["created_at"].replace("Z", "+00:00"))
                hours = max(1, (now - created).total_seconds() / 3600)
            except:
                pass
            recency = hours ** (-0.5)
            return post["engagement_score"] + recency * 10
        posts.sort(key=_score, reverse=True)

    elif sort == "chronological_with_highlights":
        # Find one highlight per friend (most engaged post in last 48h)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        cutoff = datetime.fromtimestamp(now.timestamp() - 48*3600, tz=timezone.utc).isoformat()
        
        # Get top post per friend
        conn = get_connection()
        friend_ids = [p["user_id"] for p in posts if p["user_id"] != user_id]
        highlights = []
        seen_friends = set()
        for p in sorted(posts, key=lambda x: x["engagement_score"], reverse=True):
            if p["user_id"] != user_id and p["user_id"] not in seen_friends and p["created_at"] > cutoff:
                highlights.append(p)
                seen_friends.add(p["user_id"])
        
        # Re-sort: highlights first, then chronological
        highlight_ids = {p["id"] for p in highlights}
        result = highlights + [p for p in posts if p["id"] not in highlight_ids]
        posts = result

    elif sort == "photos":
        # Photo/video posts first, then text/link, each group sorted newest
        def _is_visual(post):
            return post.get("photo_url") or post.get("video_url") or post.get("photo_urls")
        visual = [p for p in posts if _is_visual(p)]
        other = [p for p in posts if not _is_visual(p)]
        posts = visual + other

    return posts


def _get_reactions(post_id: int) -> Dict[str, int]:
    conn = get_connection()
    rows = conn.execute("SELECT reaction_type, COUNT(*) as c FROM reactions WHERE post_id=? GROUP BY reaction_type", (post_id,)).fetchall()
    conn.close()
    return {r["reaction_type"]: r["c"] for r in rows}


def _count_likes(post_id: int) -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_likes WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0


def _count_comments(post_id: int) -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_comments WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0
