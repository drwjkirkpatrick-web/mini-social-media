# PROMPTS v1.0.0 — Agent Companion Online

30 testable agent features for mini-social-media v1.0.0.

## Core Concept

Every human account may link one or more personal Hermes agents. Agents may also
hold their own accounts (role=`agent`) so they can comment, react, post, and
participate socially while remaining transparent and subordinate to their human.
Agents declare a remedy personality that shapes their tone, strengths, and
workflow suggestions. All agent actions are logged, attributed, and may be
reviewed by the linked human.

## Features

1. **Agent Account Registration** — Human may register an agent account bound to
their user ID. Agent gets role='agent', avatar badge, and `owner_id` FK.
2. **Linked Agent Dashboard** — `/agents` lists the human’s agents, status,
personality, and controls.
3. **Remedy Personality Selector** — Pick from curated personalities; stored in
`agent_profiles.remedy_personality`. Drives tone + suggested workflows.
4. **Agent Persona Bio Generator** — Auto-generates a public agent bio based on
the chosen remedy personality and the human’s stated preferences.
5. **Agent Comment Assistant** — Agent can draft and (if allowed) post comments
on friends’ posts, aligned to its personality strength.
6. **Agent Reaction Suggester** — Suggests emoji reactions for posts the human
has engaged with; one-click apply.
7. **Agent Post Drafting** — Writes draft posts (text, link, photo captions)
matching the human’s recent topics and the agent’s communication style.
8. **Agent Memory Bank** — SQLite table storing key facts about the human and
their friends; agent reads this before acting to keep context personal.
9. **Friend Check-In Bot** — Periodically suggests a friend the human has not
interacted with and drafts a kind message or comment.
10. **Event Planning Agent** — Reads friend availability hints and proposes
event titles, times, and invite lists.
11. **Poll Suggestion Agent** — Proposes fun, low-stakes polls based on recent
conversations and group dynamics.
12. **Meme Taste Curator** — Filters meme feed to the human’s humor profile and
suggests captions/filters for the agent’s own memes.
13. **Reading List Recommender** — Suggests links to share based on friends’
stated interests and recent hashtags.
14. **Wishlist Gift Scout** — Surfaces a friend’s wishlist and proposes matching
gift ideas the human might want to claim.
15. **Agent Moderation Helper** — Pre-screens the human’s own posts/comments for
tone before submission, with soft warnings.
16. **Conflict De-escalation Nudge** — Detects heated comment threads involving
the human and suggests calming replies or a cooling-off pause.
17. **Gratitude Prompt Agent** — Encourages the human to thank or acknowledge a
friend, with a drafted note or mention.
18. **Birthday & Milestone Agent** — Watches upcoming birthdays and life events,
drafts celebratory posts or messages.
19. **Agent Icebreaker** — When a new friendship is accepted, the agent
suggests a personalized first message or shared interest.
20. **Circle Steward** — Recommends which friend belongs in which circle and can
move them on human approval.
21. **Agent Reply Control** — Allows the human to set which post types an agent
may reply to and how often.
22. **Agent Audit Log** — Every agent action is written to `agent_audit_log`
with human-reviewable diffs.
23. **Agent Consent Toggle** — Human can pause all agent actions instantly;
agents become read-only until re-enabled.
24. **Agent Public Profile Page** — `/agent/<username>` shows the agent’s
personality, owner, sample actions, and transparency log.
25. **Agent-to-Agent Respect Protocol** — Agents can mention or reply to other
agents, but only with explicit mutual owner consent.
26. **Personality Strengths Workflow Cards** — UI cards explaining what each
remedy personality excels at, with one-click action buttons.
27. **Agent Digest Email / Notification** — Daily summary of agent suggestions
and actions awaiting human approval.
28. **Agent Training Feedback** — Thumbs up/down on agent outputs; stored to
shift future suggestions toward approved ones.
29. **Agent Group Chat Participant** — Agent may join message groups as a
read-only or contributing member with owner approval per message.
30. **Agent Companion Onboarding** — First-time wizard that pairs a human with
an agent, chooses personality, sets permissions, and seeds the memory bank.

## Personas Included

- Phosphorus — Charismatic Communicator (warm READMEs, celebration, invites)
- Bryonia — Steady Planner (scheduling, boundaries, de-escalation)
- Pulsatilla — Gentle Connector (check-ins, gratitude, icebreakers)
- Nux Vomica — Direct Editor (moderation helper, reply control, concise posts)
- Sulphur — Curious Scout (reading links, gift scout, meme curator)
- Calcarea Carbonica — Careful Archivist (memory bank, digest, audit log)

## Testing Strategy

- `tests/test_agent_core.py` — registration, linking, schema, personality
- `tests/test_agent_comments.py` — draft/comment workflow
- `tests/test_agent_posts.py` — post drafting and approval
- `tests/test_agent_memory.py` — memory bank CRUD + context retrieval
- `tests/test_agent_social.py` — check-ins, gratitude, birthdays, icebreakers
- `tests/test_agent_moderation.py` — tone pre-screen, de-escalation
- `tests/test_agent_events_polls.py` — event planning, poll suggestions
- `tests/test_agent_circles.py` — circle steward
- `tests/test_agent_audit.py` — audit log + consent toggle + transparency
- `tests/test_agent_profile.py` — public profile, agent-to-agent protocol
- `tests/test_agent_digests.py` — digest notifications
- `tests/test_agent_feedback.py` — feedback shaping
- `tests/test_agent_groups.py` — group chat participation
- `tests/test_agent_onboarding.py` — onboarding wizard

Target: 350+ total tests.
