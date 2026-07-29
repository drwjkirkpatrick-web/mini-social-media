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
        # Enrich with like/comment counts
        d["like_count"] = _count_likes(d["id"])
        d["comment_count"] = _count_comments(d["id"])
        posts.append(d)
    return posts


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
