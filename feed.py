"""
Feed engine.
NOTE: Returns posts from friends + self, excluding blocked users.
WHY: Privacy-first — no public posts.
NOTE v0.7.0: Eliminated N+1 queries by computing like/comment counts inline and
fetching reactions for the returned page in one batch query.
WHY: Reduces feed generation from 3N+2 queries to 2 queries for N posts.
"""

from typing import List, Dict, Any
from database import get_connection


def get_feed(user_id: int, sort: str = "newest", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    order = "DESC" if sort == "newest" else "ASC"
    sql = f"""
        SELECT
            p.*,
            u.username,
            u.display_name,
            u.avatar_url,
            (SELECT COUNT(*) FROM post_likes l WHERE l.post_id = p.id) AS like_count,
            (SELECT COUNT(*) FROM post_comments c WHERE c.post_id = p.id) AS comment_count
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
          AND NOT EXISTS (
              SELECT 1 FROM blocks b
              WHERE b.user_id = ? AND b.target_id = p.user_id
          )
        ORDER BY p.created_at {order}
        LIMIT ? OFFSET ?
    """
    params = [user_id, user_id, user_id, user_id, user_id, limit, offset]
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()

    post_ids = [r["id"] for r in rows]
    reactions_by_post: Dict[int, Dict[str, int]] = {pid: {} for pid in post_ids}
    if post_ids:
        placeholders = ",".join("?" for _ in post_ids)
        reaction_rows = conn.execute(
            f"""SELECT post_id, reaction_type, COUNT(*) as c
                FROM reactions
                WHERE post_id IN ({placeholders})
                GROUP BY post_id, reaction_type""",
            post_ids,
        ).fetchall()
        for r in reaction_rows:
            reactions_by_post.setdefault(r["post_id"], {})[r["reaction_type"]] = r["c"]
    conn.close()

    posts = []
    for r in rows:
        d = dict(r)
        d["reactions"] = reactions_by_post.get(d["id"], {})
        d["engagement_score"] = d["like_count"] * 2 + d["comment_count"] * 3 + sum(d["reactions"].values())
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
    """Legacy helper kept for callers that only need one post's reactions."""
    conn = get_connection()
    rows = conn.execute("SELECT reaction_type, COUNT(*) as c FROM reactions WHERE post_id=? GROUP BY reaction_type", (post_id,)).fetchall()
    conn.close()
    return {r["reaction_type"]: r["c"] for r in rows}


def _count_likes(post_id: int) -> int:
    """Legacy helper kept for callers that only need one post's like count."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_likes WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0


def _count_comments(post_id: int) -> int:
    """Legacy helper kept for callers that only need one post's comment count."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_comments WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0
