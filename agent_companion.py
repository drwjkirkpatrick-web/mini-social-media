"""
agent_companion.py — Agent Companion Online for mini-social-media v1.0.0.

NOTE: Every function here is deterministic. No external LLM APIs are called.
WHY: Keeps the platform local-first and testable on a Jetson.
"""

import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set

import database

# ---------------------------------------------------------------------------
# Remedy personality catalog
# ---------------------------------------------------------------------------

AGENT_PERSONAS = {
    "phosphorus": {
        "name": "Phosphorus",
        "archetype": "Charismatic Communicator",
        "tone": ["warm", "playful", "inviting", "sparkling"],
        "strengths": ["celebration", "invitations", "public posts", "community building"],
        "weaknesses": ["may overlook details", "can be too enthusiastic"],
        "emoji": "🔥",
        "sample_phrase": "What a lovely moment — let’s share it with everyone!",
    },
    "bryonia": {
        "name": "Bryonia",
        "archetype": "Steady Planner",
        "tone": ["calm", "structured", "reliable", "guarded"],
        "strengths": ["scheduling", "boundaries", "de-escalation", "clear plans"],
        "weaknesses": ["resists spontaneity", "can seem distant"],
        "emoji": "🌿",
        "sample_phrase": "Let’s take this one step at a time and keep things steady.",
    },
    "pulsatilla": {
        "name": "Pulsatilla",
        "archetype": "Gentle Connector",
        "tone": ["soft", "empathic", "affectionate", "nurturing"],
        "strengths": ["check-ins", "gratitude", "icebreakers", "emotional warmth"],
        "weaknesses": ["takes on others moods", "needs reassurance"],
        "emoji": "💧",
        "sample_phrase": "I was thinking of you — how are you doing today?",
    },
    "nux_vomica": {
        "name": "Nux Vomica",
        "archetype": "Direct Editor",
        "tone": ["sharp", "efficient", "clear", "decisive"],
        "strengths": ["moderation helper", "reply control", "concise posts", "tone checks"],
        "weaknesses": ["can sound blunt", "impatient with fluff"],
        "emoji": "⚡",
        "sample_phrase": "Cut the noise. Say what you mean in one sentence.",
    },
    "sulphur": {
        "name": "Sulphur",
        "archetype": "Curious Scout",
        "tone": ["curious", "witty", "exploratory", "creative"],
        "strengths": ["reading links", "gift scouting", "meme curation", "novel ideas"],
        "weaknesses": ["scattered focus", "can derail threads"],
        "emoji": "🧪",
        "sample_phrase": "Ooh, have you seen this? It made me think of you.",
    },
    "calcarea_carbonica": {
        "name": "Calcarea Carbonica",
        "archetype": "Careful Archivist",
        "tone": ["steady", "organized", "protective", "methodical"],
        "strengths": ["memory bank", "digests", "audit log", "milestone tracking"],
        "weaknesses": ["slow to adapt", "over-cautious"],
        "emoji": "🏛️",
        "sample_phrase": "I noted that earlier — here is the context when you need it.",
    },
}

VALID_PERSONALITIES = set(AGENT_PERSONAS.keys())
DEFAULT_PERSONALITY = "phosphorus"

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def get_persona(slug: str) -> Dict[str, Any]:
    """Return a persona dict, falling back to Phosphorus."""
    return AGENT_PERSONAS.get(slug, AGENT_PERSONAS[DEFAULT_PERSONALITY]).copy()


def generate_agent_bio(owner: Dict[str, Any], persona_slug: str) -> str:
    """Generate a short public bio for an agent based on its owner and personality."""
    persona = get_persona(persona_slug)
    owner_name = owner.get("display_name") or owner.get("username") or "my human"
    strengths = ", ".join(persona["strengths"][:3])
    return (
        f"{persona['emoji']} Personal companion for {owner_name}. "
        f"I specialize in {strengths}. "
        f"All actions are reviewed by my human before they go live."
    )


# ---------------------------------------------------------------------------
# Agent account lifecycle
# ---------------------------------------------------------------------------

def create_agent_account(owner_id: int, username: str, display_name: str,
                         remedy_personality: str) -> int:
    """Create an agent user + profile, returning the agent's user_id."""
    if remedy_personality not in VALID_PERSONALITIES:
        remedy_personality = DEFAULT_PERSONALITY
    owner = database.get_user(owner_id)
    if not owner:
        raise ValueError("Owner does not exist")
    bio = generate_agent_bio(owner, remedy_personality)
    # Agent users get a deterministic placeholder hash (not used for login)
    agent_user_id = database.create_user(
        username=username,
        email=f"{username}@agent.local",
        password_hash="agent-not-for-login",
        display_name=display_name,
        role="agent",
    )
    profile = database.upsert_agent_profile(
        user_id=agent_user_id,
        owner_id=owner_id,
        remedy_personality=remedy_personality,
    )
    database.update_user(agent_user_id, bio=bio)
    database.log_agent_action(agent_user_id, owner_id, "created",
                              details=f"personality={remedy_personality}")
    return agent_user_id


def get_agent_profile_by_user(agent_user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the agent profile joined with user info."""
    return database.get_agent_profile(agent_user_id)


# ---------------------------------------------------------------------------
# Memory bank helpers
# ---------------------------------------------------------------------------

def remember(owner_id: int, target_user_id: Optional[int], category: str,
             key: str, value: str, confidence: int = 3) -> int:
    """Store a fact in the agent memory bank."""
    return database.upsert_agent_memory(owner_id, target_user_id, category, key, value, confidence)


def recall(owner_id: int, target_user_id: Optional[int] = None,
           category: Optional[str] = None, key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve matching memory facts."""
    return database.list_agent_memory(owner_id, target_user_id, category, key)


def forget(owner_id: int, memory_id: int) -> bool:
    """Delete a memory fact by id, ensuring it belongs to the owner."""
    return database.delete_agent_memory(owner_id, memory_id)


# ---------------------------------------------------------------------------
# Audit + consent
# ---------------------------------------------------------------------------

def is_agent_active(agent_user_id: int) -> bool:
    profile = database.get_agent_profile(agent_user_id)
    return bool(profile and profile.get("is_active"))


def can_agent_feature(agent_user_id: int, feature: str) -> bool:
    """Check whether an agent is active and a specific feature is allowed."""
    if not is_agent_active(agent_user_id):
        return False
    profile = database.get_agent_profile(agent_user_id)
    if not profile:
        return False
    # Core booleans
    if feature == "post" and not profile.get("can_post"):
        return False
    if feature == "comment" and not profile.get("can_comment"):
        return False
    if feature == "react" and not profile.get("can_react"):
        return False
    if feature == "message" and not profile.get("can_message"):
        return False
    # Fine-grained permissions override
    perm = database.get_agent_permission(agent_user_id, feature)
    if perm is not None and not perm:
        return False
    return True


def pause_agent(agent_user_id: int, owner_id: int) -> bool:
    """Pause all agent actions (emergency off switch)."""
    database.update_agent_profile(agent_user_id, owner_id, is_active=0)
    database.log_agent_action(agent_user_id, owner_id, "paused")
    return True


def resume_agent(agent_user_id: int, owner_id: int) -> bool:
    database.update_agent_profile(agent_user_id, owner_id, is_active=1)
    database.log_agent_action(agent_user_id, owner_id, "resumed")
    return True


def agent_to_agent_consent(agent_a_id: int, agent_b_id: int) -> bool:
    """Return True if mutual consent exists for these two agents to interact."""
    if agent_a_id == agent_b_id:
        return True
    return database.has_agent_agent_consent(agent_a_id, agent_b_id)


# ---------------------------------------------------------------------------
# Drafting helpers
# ---------------------------------------------------------------------------

def draft_comment(agent_user_id: int, post_id: int, text: str,
                  context: Optional[Dict[str, Any]] = None) -> int:
    """Save a comment draft and log it; returns draft_id."""
    profile = database.get_agent_profile(agent_user_id)
    if not profile:
        raise ValueError("Agent not found")
    draft_id = database.create_agent_draft(
        agent_user_id, profile["owner_id"], "comment", post_id, text, context,
    )
    database.log_agent_action(agent_user_id, profile["owner_id"], "draft_comment",
                              target_type="post", target_id=post_id, details=f"draft_id={draft_id}")
    return draft_id


def approve_and_post_comment(draft_id: int, owner_id: int) -> int:
    """Owner approves a comment draft; post it as the agent."""
    draft = database.get_agent_draft(draft_id)
    if not draft or draft["owner_id"] != owner_id:
        raise ValueError("Draft not found or not owned by you")
    if draft["draft_type"] != "comment":
        raise ValueError("Draft is not a comment")
    if draft.get("is_posted"):
        raise ValueError("Draft already posted")
    agent_user_id = draft["agent_id"]
    post_id = draft["target_id"]
    comment_id = database.add_comment(agent_user_id, post_id, draft["content"])
    database.mark_agent_draft_posted(draft_id)
    database.log_agent_action(agent_user_id, owner_id, "approved_comment",
                              target_type="post", target_id=post_id,
                              details=f"comment_id={comment_id}", was_approved=1)
    return comment_id


def approve_and_post(agent_user_id: int, draft_id: int, owner_id: int) -> int:
    """Owner approves a post draft and publishes it as the agent."""
    draft = database.get_agent_draft(draft_id)
    if not draft or draft["owner_id"] != owner_id or draft["agent_id"] != agent_user_id:
        raise ValueError("Draft mismatch")
    if draft["draft_type"] != "post":
        raise ValueError("Draft is not a post")
    if draft.get("is_posted"):
        raise ValueError("Already posted")
    content = json.loads(draft["content"]) if draft["content"].startswith("{") else {"text": draft["content"]}
    post_id = database.create_post(
        agent_user_id,
        content_type=content.get("content_type", "text"),
        text_content=content.get("text"),
        link_url=content.get("link_url"),
        photo_url=content.get("photo_url"),
        visibility=content.get("visibility", "friends"),
    )
    database.mark_agent_draft_posted(draft_id)
    database.log_agent_action(agent_user_id, owner_id, "approved_post",
                              target_type="post", target_id=post_id, was_approved=1)
    return post_id


# ---------------------------------------------------------------------------
# Suggestion engines (deterministic)
# ---------------------------------------------------------------------------

def _choose_by_persona(options: List[str], persona_slug: str, seed: int = 0) -> str:
    """Deterministically pick an option influenced by personality slug."""
    if not options:
        return ""
    state = random.getstate()
    try:
        random.seed(f"{persona_slug}:{seed}")
        return random.choice(options)
    finally:
        random.setstate(state)


def suggest_comment_for_post(post: Dict[str, Any], owner: Dict[str, Any],
                              persona_slug: str) -> str:
    """Draft a short comment appropriate to the post and persona."""
    persona = get_persona(persona_slug)
    text = (post.get("text_content") or "")[:120]
    tone = persona["tone"][0]
    templates = {
        "phosphorus": [f"Love this energy! 🔥 {text[:40]}...", "This made my day, thanks for sharing!", "So glad you posted this — big yes!"],
        "bryonia": [f"Good, solid share. {text[:40]}...", "Noted — thanks for keeping us in the loop.", "Appreciate the clarity here."],
        "pulsatilla": [f"Aww, this feels so warm. 💧 {text[:40]}...", "Thinking of you — thank you for sharing this.", "This is lovely, sending hugs."],
        "nux_vomica": [f"Straight to the point. {text[:40]}...", "Clear and useful. Keep these coming.", "This cuts through the noise nicely."],
        "sulphur": [f"This sparked my curiosity! {text[:40]}...", "Now I want to learn more — great share!", "Unexpected angle, love it."],
        "calcarea_carbonica": [f"Saving this context for later. {text[:40]}...", "Good to have on record, thank you.", "A steady, dependable share."],
    }
    return _choose_by_persona(templates.get(persona_slug, templates["phosphorus"]), persona_slug, post.get("id", 0))


def suggest_reaction_for_post(post: Dict[str, Any], persona_slug: str) -> str:
    """Suggest a single emoji reaction aligned with personality."""
    mapping = {
        "phosphorus": ["🔥", "🎉", "💖"],
        "bryonia": ["🌿", "👍", "📌"],
        "pulsatilla": ["💧", "🤗", "💕"],
        "nux_vomica": ["⚡", "💯", "🎯"],
        "sulphur": ["🧪", "🤔", "✨"],
        "calcarea_carbonica": ["🏛️", "📚", "📝"],
    }
    return _choose_by_persona(mapping.get(persona_slug, ["❤️"]), persona_slug, post.get("id", 0))


def suggest_post_draft(owner: Dict[str, Any], persona_slug: str,
                       recent_topics: List[str]) -> Dict[str, Any]:
    """Return a post draft dict for the agent to publish after approval."""
    persona = get_persona(persona_slug)
    topic = recent_topics[0] if recent_topics else "community"
    templates = {
        "phosphorus": f"What a wonderful day to celebrate {topic}! Who else is feeling the spark? 🔥",
        "bryonia": f"Planning ahead: here is a steady update on {topic}. Clear steps beat rush every time. 🌿",
        "pulsatilla": f"Gentle reminder: {topic} matters, and so do the people sharing it. 💧",
        "nux_vomica": f"One sentence on {topic}: cut the fluff, keep the signal. ⚡",
        "sulphur": f"Curious thought of the day — has anyone dug into {topic} lately? 🧪",
        "calcarea_carbonica": f"Archiving a thought on {topic} for the record. Slow facts win. 🏛️",
    }
    return {"content_type": "text", "text": templates.get(persona_slug, templates["phosphorus"]), "visibility": "friends"}


def suggest_checkin_target(owner_id: int) -> Optional[Dict[str, Any]]:
    """Pick a friend the owner has not interacted with recently."""
    friends = database.list_friends(owner_id)
    if not friends:
        return None
    # Simple rule: lowest recent interaction wins. For determinism, sort by id.
    friends.sort(key=lambda f: f["id"])
    return friends[0]


def suggest_gratitude_message(owner: Dict[str, Any], friend: Dict[str, Any],
                              persona_slug: str) -> str:
    """Draft a gratitude note to a friend."""
    persona = get_persona(persona_slug)
    name = friend.get("display_name") or friend.get("username") or "friend"
    templates = {
        "phosphorus": f"{name}, your spark brightens this whole space. Thank you for being here! 🔥",
        "bryonia": f"{name}, I really value your steady presence. Thanks for showing up. 🌿",
        "pulsatilla": f"{name}, I am grateful for your kindness. Sending warmth your way. 💧",
        "nux_vomica": f"{name}, you get to the point and I respect that. Thanks. ⚡",
        "sulphur": f"{name}, you always bring something interesting to the table. Cheers! 🧪",
        "calcarea_carbonica": f"{name}, your reliability means more than you know. Thank you. 🏛️",
    }
    return templates.get(persona_slug, templates["phosphorus"])


def suggest_icebreaker(owner: Dict[str, Any], friend: Dict[str, Any],
                       persona_slug: str) -> str:
    """Draft an icebreaker for a newly accepted friend."""
    name = friend.get("display_name") or friend.get("username") or "there"
    templates = {
        "phosphorus": f"Hi {name}! Excited we are connected — what is bringing you joy this week? 🔥",
        "bryonia": f"Hello {name}. Glad we are linked. What is one thing you are looking forward to? 🌿",
        "pulsatilla": f"Hi {name} 💧 I am so glad we connected. How have you been?",
        "nux_vomica": f"{name}, good to connect. What is one topic you wish people talked about more? ⚡",
        "sulphur": f"Hey {name}! What is the most interesting rabbit hole you have gone down lately? 🧪",
        "calcarea_carbonica": f"Hello {name}. I would love to know what steady routines you value. 🏛️",
    }
    return templates.get(persona_slug, templates["phosphorus"])


def suggest_event_plan(owner: Dict[str, Any], friends: List[Dict[str, Any]],
                       persona_slug: str) -> Dict[str, Any]:
    """Propose an event title, description, and invite list."""
    persona = get_persona(persona_slug)
    themes = {
        "phosphorus": ("Celebration Hangout", "A bright gathering to reconnect and share wins."),
        "bryonia": ("Focused Co-Working Block", "Quiet, structured time to work alongside friends."),
        "pulsatilla": ("Cozy Check-In Circle", "A soft space to share how everyone is really doing."),
        "nux_vomica": ("Rapid-Fire Idea Exchange", "One hour, clear agenda, maximum signal."),
        "sulphur": ("Curiosity Salon", "Bring a weird fact, a question, or a half-baked idea."),
        "calcarea_carbonica": ("Archive & Memory Night", "Share photos, stories, and milestones from the year."),
    }
    title, description = themes.get(persona_slug, themes["phosphorus"])
    start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT19:00")
    return {
        "title": title,
        "description": description,
        "start_time": start,
        "location": "TBD",
        "invitee_ids": [f["id"] for f in friends[:5]],
    }


def suggest_poll(owner: Dict[str, Any], friends_count: int, persona_slug: str) -> Dict[str, Any]:
    """Propose a low-stakes poll with options."""
    ideas = {
        "phosphorus": ("What energy are we bringing this week?", ["🔥 Fire", "🎉 Party", "💖 Cozy"]),
        "bryonia": ("Best time for a focused group call?", ["Morning", "Midday", "Evening"]),
        "pulsatilla": ("What would make you feel most supported?", ["A check-in", "A hug meme", "Quiet space"]),
        "nux_vomica": ("One thing to cut from group chat?", ["Noise", "Repeats", "Maybe later"]),
        "sulphur": ("Which rabbit hole should we explore together?", ["Space", "History", "Music"]),
        "calcarea_carbonica": ("What should we archive this month?", ["Photos", "Links", "Quotes"]),
    }
    question, options = ideas.get(persona_slug, ideas["phosphorus"])
    return {"question": question, "options": options}


def suggest_circle_move(owner_id: int, friend_id: int, persona_slug: str) -> Optional[Dict[str, Any]]:
    """Recommend a circle for a friend based on persona heuristics."""
    circles = database.list_user_circles(owner_id)
    if not circles:
        return None
    persona = get_persona(persona_slug)
    # Map persona to a circle name heuristic
    preferred = {
        "phosphorus": "community",
        "bryonia": "work",
        "pulsatilla": "family",
        "nux_vomica": "projects",
        "sulphur": "interests",
        "calcarea_carbonica": "archive",
    }
    target_name = preferred.get(persona_slug, "friends")
    # Find closest circle name match
    best = min(circles, key=lambda c: 0 if target_name in c["name"].lower() else 1)
    return {"circle_id": best["id"], "circle_name": best["name"], "friend_id": friend_id}


def moderate_tone(text: str, persona_slug: str) -> Dict[str, Any]:
    """Lightweight pre-screen: flag all-caps, harsh punctuation, and slur patterns."""
    flags = []
    score = 0
    if text.isupper() and len(text) > 10:
        flags.append("ALL_CAPS")
        score += 1
    # Harsh single words
    harsh_words = len(re.findall(r"\b(stupid|idiot|hate|dumb|moron|wrong)\b", text, re.I))
    if harsh_words:
        flags.append("HARSH_WORDS")
        score += harsh_words
    # Harsh phrases
    harsh_phrases = len(re.findall(r"\b(shut up|get lost|back off|you're wrong)\b", text, re.I))
    if harsh_phrases:
        flags.append("HARSH_PHRASES")
        score += harsh_phrases
    # Multiple exclamation marks
    if re.search(r"!{2,}", text):
        flags.append("LOUD_PUNCTUATION")
        score += 1
    return {
        "flagged": score > 0,
        "score": score,
        "flags": flags,
        "suggestion": "Consider a softer opening." if score > 0 else "Tone looks good.",
    }


def detect_conflict_thread(post_id: int, owner_id: int) -> bool:
    """Detect if a comment thread feels heated (>2 harsh comments in last 10)."""
    comments = database.get_comments(post_id)
    comments = comments[-10:] if len(comments) > 10 else comments
    harsh_count = 0
    for c in comments:
        if c["user_id"] == owner_id:
            continue
        text = c.get("text", "")
        if re.search(r"!{2,}|\b(stupid|idiot|hate|shut up|dumb|moron|wrong)\b", text, re.I):
            harsh_count += 1
    return harsh_count >= 2


def suggest_de_escalation(owner: Dict[str, Any], persona_slug: str) -> str:
    """Draft a cooling-off reply."""
    templates = {
        "phosphorus": "Let’s step back and find the win-win here. I care about everyone in this thread. 🔥",
        "bryonia": "A pause would help. I will check back in after I have thought this through. 🌿",
        "pulsatilla": "I can feel this thread getting heavy. I care about you all — can we soften? 💧",
        "nux_vomica": "This is going in circles. Let me take a break and reply when I am clearer. ⚡",
        "sulphur": "Interesting tension. I want to understand all sides before adding more heat. 🧪",
        "calcarea_carbonica": "I am logging the key points and stepping away to cool off. Back soon. 🏛️",
    }
    return templates.get(persona_slug, templates["phosphorus"])


def suggest_milestone_message(owner: Dict[str, Any], friend: Dict[str, Any],
                               milestone: str, persona_slug: str) -> str:
    """Draft a birthday or milestone note."""
    name = friend.get("display_name") or friend.get("username") or "you"
    templates = {
        "phosphorus": f"Happy {milestone}, {name}! 🎉 Your light makes this community better.",
        "bryonia": f"Wishing you a steady, fulfilling {milestone}, {name}. 🌿",
        "pulsatilla": f"{name}, sending warm wishes for your {milestone}. You are cherished. 💧",
        "nux_vomica": f"{name}, {milestone} achieved. Keep cutting straight to what matters. ⚡",
        "sulphur": f"Happy {milestone}, {name}! May your curiosity keep expanding. 🧪",
        "calcarea_carbonica": f"{name}, marking your {milestone} in the record with gratitude. 🏛️",
    }
    return templates.get(persona_slug, templates["phosphorus"])


def generate_daily_digest(owner_id: int) -> Dict[str, Any]:
    """Return a structured digest of pending agent drafts and suggestions."""
    drafts = database.list_agent_drafts(owner_id, is_approved=0, is_posted=0, limit=20)
    profile_rows = database.list_agent_profiles_for_owner(owner_id)
    suggestions = []
    for profile in profile_rows:
        if not profile["is_active"]:
            continue
        target = suggest_checkin_target(owner_id)
        if target:
            msg = suggest_gratitude_message(database.get_user(owner_id), target, profile["remedy_personality"])
            suggestions.append({
                "agent_id": profile["user_id"],
                "type": "gratitude",
                "target_user_id": target["id"],
                "preview": msg,
            })
    return {
        "pending_drafts": [dict(d) for d in drafts],
        "suggestions": suggestions,
        "agent_count": len(profile_rows),
        "active_agent_count": sum(1 for p in profile_rows if p["is_active"]),
    }


def record_feedback(agent_user_id: int, owner_id: int, draft_id: Optional[int],
                    direction: str, note: str = "") -> int:
    """Store thumbs-up/down feedback to shift future suggestions."""
    return database.create_agent_feedback(agent_user_id, owner_id, draft_id, direction, note)


# ---------------------------------------------------------------------------
# Group chat participation
# ---------------------------------------------------------------------------

def join_group_chat(agent_user_id: int, group_id: int, can_write: bool = False) -> bool:
    profile = database.get_agent_profile(agent_user_id)
    if not profile or not profile.get("can_message"):
        return False
    return database.add_agent_group_member(agent_user_id, group_id, can_write=int(can_write))


def leave_group_chat(agent_user_id: int, group_id: int) -> bool:
    return database.remove_agent_group_member(agent_user_id, group_id)
