"""
agent_routes.py — Flask blueprint for Agent Companion Online v1.0.0.

NOTE: All routes use the existing login_required decorator and database helpers.
WHY: Keeps agent features consistent with the rest of mini-social-media.
"""

import json
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort,
)
from auth import login_required
import database
import agent_companion

agent_bp = Blueprint("agent", __name__, url_prefix="/agents")


def _current_user() -> dict:
    uid = session.get("user_id")
    return database.get_user(uid) if uid else None


@agent_bp.route("/")
@login_required
def agents_dashboard():
    """Show linked agents and pending drafts for the current human."""
    me = _current_user()
    profiles = database.list_agent_profiles_for_owner(me["id"])
    pending = database.list_agent_drafts(me["id"], is_approved=0, is_posted=0, limit=20)
    return render_template("agents_dashboard.html",
                           profiles=profiles, pending_drafts=pending,
                           personas=agent_companion.AGENT_PERSONAS)


@agent_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_agent():
    """Register a new personal agent."""
    me = _current_user()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        display_name = request.form.get("display_name", "").strip()
        personality = request.form.get("remedy_personality", "phosphorus").strip()
        if not username:
            flash("Username is required.", "error")
            return render_template("create_agent.html", personas=agent_companion.AGENT_PERSONAS), 400
        if database.get_user_by_username(username):
            flash("That username is already taken.", "error")
            return render_template("create_agent.html", personas=agent_companion.AGENT_PERSONAS), 400
        try:
            agent_companion.create_agent_account(me["id"], username,
                                                 display_name or username,
                                                 personality)
            flash("Agent companion created!", "success")
            return redirect(url_for("agent.agents_dashboard"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("create_agent.html", personas=agent_companion.AGENT_PERSONAS), 400
    return render_template("create_agent.html", personas=agent_companion.AGENT_PERSONAS)


@agent_bp.route("/<int:agent_user_id>")
@login_required
def agent_detail(agent_user_id):
    """Public-ish agent profile page with transparency log."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile:
        abort(404)
    # Allow owner or friends of owner to view
    if profile["owner_id"] != me["id"]:
        friendship = database.get_friendship(me["id"], profile["owner_id"])
        if not (friendship and friendship["status"] == "accepted"):
            abort(403)
    log = database.list_agent_audit_log(profile["owner_id"], agent_user_id, limit=20)
    persona = agent_companion.get_persona(profile["remedy_personality"])
    return render_template("agent_detail.html", profile=profile, log=log, persona=persona)


@agent_bp.route("/<int:agent_user_id>/edit", methods=["POST"])
@login_required
def edit_agent(agent_user_id):
    """Update agent permissions and personality."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    fields = {}
    for key in ("remedy_personality", "can_post", "can_comment", "can_react", "can_message"):
        val = request.form.get(key)
        if val is None:
            continue
        if key == "remedy_personality":
            if val in agent_companion.VALID_PERSONALITIES:
                fields[key] = val
        else:
            fields[key] = int(val)
    moderation = request.form.get("moderation_mode")
    if moderation in ("warn", "block", "silent"):
        fields["moderation_mode"] = moderation
    if fields:
        database.update_agent_profile(agent_user_id, me["id"], **fields)
        new_persona = fields.get("remedy_personality", profile["remedy_personality"])
        bio = agent_companion.generate_agent_bio(me, new_persona)
        database.update_user(agent_user_id, bio=bio)
        flash("Agent updated.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/pause", methods=["POST"])
@login_required
def pause_agent(agent_user_id):
    """Emergency pause all agent actions."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    agent_companion.pause_agent(agent_user_id, me["id"])
    flash("Agent paused. All actions are now read-only.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/resume", methods=["POST"])
@login_required
def resume_agent(agent_user_id):
    """Resume a paused agent."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    agent_companion.resume_agent(agent_user_id, me["id"])
    flash("Agent resumed.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/memory")
@login_required
def agent_memory(agent_user_id):
    """View the agent's memory bank."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    memories = agent_companion.recall(me["id"])
    return render_template("agent_memory.html", profile=profile, memories=memories)


@agent_bp.route("/<int:agent_user_id>/memory/new", methods=["POST"])
@login_required
def new_agent_memory(agent_user_id):
    """Add a fact to the agent memory bank."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    target_id = request.form.get("target_user_id", type=int)
    category = request.form.get("category", "").strip()
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "").strip()
    confidence = request.form.get("confidence", 3, type=int)
    if not category or not key or not value:
        flash("Category, key, and value are required.", "error")
        return redirect(url_for("agent.agent_memory", agent_user_id=agent_user_id))
    agent_companion.remember(me["id"], target_id, category, key, value, confidence)
    flash("Memory saved.", "success")
    return redirect(url_for("agent.agent_memory", agent_user_id=agent_user_id))


@agent_bp.route("/memory/<int:memory_id>/delete", methods=["POST"])
@login_required
def delete_memory(memory_id):
    """Delete a memory fact."""
    me = _current_user()
    if agent_companion.forget(me["id"], memory_id):
        flash("Memory deleted.", "success")
    else:
        flash("Memory not found.", "error")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/draft-comment/<int:post_id>", methods=["POST"])
@login_required
def draft_comment(agent_user_id, post_id):
    """Draft a comment on a post."""
    me = _current_user()
    if not agent_companion.can_agent_feature(agent_user_id, "comment"):
        flash("Agent cannot comment right now.", "error")
        return redirect(url_for("feed"))
    post = database.get_post(post_id)
    if not post:
        abort(404)
    profile = database.get_agent_profile(agent_user_id)
    text = agent_companion.suggest_comment_for_post(post, me, profile["remedy_personality"])
    draft_id = agent_companion.draft_comment(agent_user_id, post_id, text,
                                              context={"post_text": post.get("text_content")})
    flash("Comment drafted. Approve it from the agent dashboard.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/draft-post", methods=["POST"])
@login_required
def draft_post(agent_user_id):
    """Draft a post for the agent."""
    me = _current_user()
    if not agent_companion.can_agent_feature(agent_user_id, "post"):
        flash("Agent cannot post right now.", "error")
        return redirect(url_for("agent.agents_dashboard"))
    profile = database.get_agent_profile(agent_user_id)
    recent = database.list_posts_by_user(me["id"], limit=5)
    topics = [p.get("text_content", "") for p in recent if p.get("text_content")]
    draft = agent_companion.suggest_post_draft(me, profile["remedy_personality"], topics)
    content = json.dumps(draft)
    draft_id = database.create_agent_draft(agent_user_id, me["id"], "post", 0, content,
                                            context={"topics": topics})
    database.log_agent_action(agent_user_id, me["id"], "draft_post",
                              target_type="draft", target_id=draft_id)
    flash("Post drafted.", "success")
    return redirect(url_for("agent.agents_dashboard"))
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/draft/<int:draft_id>/approve", methods=["POST"])
@login_required
def approve_draft(draft_id):
    """Approve and publish an agent draft."""
    me = _current_user()
    draft = database.get_agent_draft(draft_id)
    if not draft or draft["owner_id"] != me["id"]:
        abort(403)
    if draft["draft_type"] == "comment":
        agent_companion.approve_and_post_comment(draft_id, me["id"])
        flash("Comment posted by your agent.", "success")
    elif draft["draft_type"] == "post":
        agent_companion.approve_and_post(draft["agent_id"], draft_id, me["id"])
        flash("Post published by your agent.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/draft/<int:draft_id>/feedback", methods=["POST"])
@login_required
def feedback_draft(draft_id):
    """Provide thumbs-up/down feedback on an agent draft."""
    me = _current_user()
    draft = database.get_agent_draft(draft_id)
    if not draft or draft["owner_id"] != me["id"]:
        abort(403)
    direction = request.form.get("direction", "up")
    note = request.form.get("note", "").strip()
    agent_companion.record_feedback(draft["agent_id"], me["id"], draft_id, direction, note)
    flash("Feedback recorded.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/suggest-reaction/<int:post_id>")
@login_required
def suggest_reaction(agent_user_id, post_id):
    """Return a JSON suggestion for an emoji reaction."""
    me = _current_user()
    if not agent_companion.can_agent_feature(agent_user_id, "react"):
        return jsonify({"error": "Agent cannot react"}), 403
    post = database.get_post(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    profile = database.get_agent_profile(agent_user_id)
    emoji = agent_companion.suggest_reaction_for_post(post, profile["remedy_personality"])
    return jsonify({"suggestion": emoji})


@agent_bp.route("/<int:agent_user_id>/checkin")
@login_required
def checkin_suggestion(agent_user_id):
    """Suggest a friend to check in with and a drafted message."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    target = agent_companion.suggest_checkin_target(me["id"])
    if not target:
        flash("No friends to check in with yet.", "info")
        return redirect(url_for("agent.agents_dashboard"))
    msg = agent_companion.suggest_gratitude_message(me, target, profile["remedy_personality"])
    return render_template("agent_suggestion.html",
                           agent=profile, target=target, preview=msg,
                           action_type="gratitude")


@agent_bp.route("/<int:agent_user_id>/event-plan")
@login_required
def event_plan_suggestion(agent_user_id):
    """Suggest an event plan for the owner."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    friends = database.list_friends(me["id"])
    plan = agent_companion.suggest_event_plan(me, friends, profile["remedy_personality"])
    return render_template("agent_suggestion.html",
                           agent=profile, plan=plan, preview=json.dumps(plan, indent=2),
                           action_type="event_plan")


@agent_bp.route("/<int:agent_user_id>/poll-suggest")
@login_required
def poll_suggestion(agent_user_id):
    """Suggest a poll for the owner to post."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    friends = database.list_friends(me["id"])
    poll = agent_companion.suggest_poll(me, len(friends), profile["remedy_personality"])
    return render_template("agent_suggestion.html",
                           agent=profile, poll=poll, preview=poll["question"],
                           action_type="poll")


@agent_bp.route("/<int:agent_user_id>/icebreaker/<int:friend_id>")
@login_required
def icebreaker_suggestion(agent_user_id, friend_id):
    """Suggest an icebreaker for a new friend."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    friend = database.get_user(friend_id)
    if not friend:
        abort(404)
    msg = agent_companion.suggest_icebreaker(me, friend, profile["remedy_personality"])
    return render_template("agent_suggestion.html",
                           agent=profile, target=friend, preview=msg,
                           action_type="icebreaker")


@agent_bp.route("/<int:agent_user_id>/tone-check", methods=["POST"])
@login_required
def tone_check(agent_user_id):
    """Pre-screen a text before the human posts it."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    text = request.form.get("text", "").strip()
    result = agent_companion.moderate_tone(text, profile["remedy_personality"])
    return jsonify(result)


@agent_bp.route("/<int:agent_user_id>/de-escalate/<int:post_id>")
@login_required
def de_escalate_suggestion(agent_user_id, post_id):
    """Suggest a cooling-off reply if a thread is heated."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    is_heated = agent_companion.detect_conflict_thread(post_id, me["id"])
    if not is_heated:
        return jsonify({"heated": False, "suggestion": "Thread looks calm."})
    suggestion = agent_companion.suggest_de_escalation(me, profile["remedy_personality"])
    return jsonify({"heated": True, "suggestion": suggestion})


@agent_bp.route("/<int:agent_user_id>/digest")
@login_required
def daily_digest(agent_user_id):
    """Show daily digest of agent drafts and suggestions."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    digest = agent_companion.generate_daily_digest(me["id"])
    return render_template("agent_digest.html", agent=profile, digest=digest)


@agent_bp.route("/<int:agent_user_id>/consent/<int:other_agent_id>", methods=["POST"])
@login_required
def set_agent_consent(agent_user_id, other_agent_id):
    """Allow the owner to permit agent-to-agent interaction."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    other = database.get_agent_profile(other_agent_id)
    if not profile or not other:
        abort(404)
    if profile["owner_id"] != me["id"] or other["owner_id"] != me["id"]:
        abort(403)
    allowed = bool(request.form.get("allowed", 0, type=int))
    database.set_agent_agent_consent(agent_user_id, other_agent_id, allowed)
    flash("Agent-to-agent consent updated.", "success")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/<int:agent_user_id>/group/<int:group_id>/join", methods=["POST"])
@login_required
def join_agent_group(agent_user_id, group_id):
    """Add an agent to a message group."""
    me = _current_user()
    profile = database.get_agent_profile(agent_user_id)
    if not profile or profile["owner_id"] != me["id"]:
        abort(403)
    can_write = bool(request.form.get("can_write", 0, type=int))
    if agent_companion.join_group_chat(agent_user_id, group_id, can_write=can_write):
        flash("Agent joined group chat.", "success")
    else:
        flash("Agent could not join group chat.", "error")
    return redirect(url_for("agent.agents_dashboard"))


@agent_bp.route("/onboarding")
@login_required
def onboarding():
    """First-time agent companion setup wizard."""
    me = _current_user()
    return render_template("agent_onboarding.html", personas=agent_companion.AGENT_PERSONAS, me=me)
