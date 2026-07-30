# PROMPTS_v9.md — Meme Engine v0.9.0 (30 Improvements)

> Inspired by [memelord.com](https://memelord.com), adapted for privacy-first
> local-first communities. No external APIs — all deterministic, all local.

## Templates & Text

### Prompt 1: Meme Templates Table
Create a `meme_templates` table with 12 classic seeded templates (Drake,
Distracted Boyfriend, Woman Yelling at Cat, Change My Mind, Two Buttons,
Expanding Brain, Gal Brain, Stonks, Roll Safe, Doge, This Is Fine,
Surprised Pikachu). Each has name, category, image_url, width, height.

**Test:** `test_meme_templates_schema_and_seed` — `list_meme_templates()` returns 12 rows with expected names.

### Prompt 2: Custom Template Creation
`create_meme_template(name, category, image_url, width, height, created_by)`
inserts a new template and returns its ID.

**Test:** `test_create_custom_meme_template` — Created template appears in `list_meme_templates()`.

### Prompt 3: Template Search
`search_meme_templates(query)` searches templates by name (case-insensitive
LIKE match).

**Test:** `test_search_meme_templates` — Searching "drake" returns the Drake template.

### Prompt 4: Template Favorites
`favorite_template(user_id, template_id)` toggles a favorite entry.
`list_favorite_templates(user_id)` returns favorited templates.

**Test:** `test_template_favorites_toggle` — Favorite toggles on then off.

### Prompt 5: Top/Bottom Text
Add `top_text` and `bottom_text` columns to `posts` table.
`update_meme_post(post_id, top_text=..., bottom_text=...)` sets them.

**Test:** `test_meme_top_bottom_text` — `get_post()` returns both text fields.

### Prompt 6: Custom Text Color
Add `text_color` column to `posts` (default `#ffffff`).
`update_meme_post(post_id, text_color="#ff5733")` sets custom color.

**Test:** `test_meme_text_color` — `get_post()["text_color"]` matches.

### Prompt 7: Text Rotation
Add `text_rotation` column to `posts` (default 0).
`update_meme_post(post_id, text_rotation=5.0)` tilts text.

**Test:** `test_meme_text_rotation` — `get_post()["text_rotation"]` == 5.0.

### Prompt 8: Caption Suggestion Bank
Seed `meme_tags` with 10 trending tags. `list_meme_tags()` returns them as
caption inspiration.

**Test:** `test_caption_suggestion_bank` — Tags include "trending", "classic", "wholesome".

## Stickers & Overlays

### Prompt 9: Meme Sticker Library
Create `meme_stickers` table with 8 seeded SVG stickers (Fire, Heart, 100,
Crown, Thumbs Up, Skull, Clown, Flex).

**Test:** `test_meme_stickers_schema_and_seed` — `list_meme_stickers()` returns 8 stickers.

### Prompt 10: Sticker Placement
`place_sticker(post_id, sticker_id, pos_x, pos_y, rotation, scale)` places a
sticker on a meme post. `get_sticker_placements(post_id)` returns all
placements.

**Test:** `test_sticker_placement` — Placement with x=100, y=200, rotation=15.0 is retrievable.

### Prompt 11: User Watermark
Add `watermark_text` column to `posts`. `update_meme_post(post_id,
watermark_text="@handle")` stamps a watermark.

**Test:** `test_meme_watermark` — `get_post()["watermark_text"]` matches.

## Interactions & Voting

### Prompt 12: Meme-Specific Emoji Reactions
`react_meme(post_id, user_id, emoji)` toggles an emoji reaction.
`get_meme_reactions(post_id)` returns `{emoji, count}` aggregated.

**Test:** `test_meme_specific_reactions` — 🔥 reaction toggles on then off.

### Prompt 13: Meme Remix Chain
`update_meme_post(post_id, meme_remix_of=original_id)` links a remix.
`get_meme_remix_chain(post_id)` follows the chain recursively (root → leaf).

**Test:** `test_meme_remix_chain` — Chain has 2 entries, root first.

### Prompt 14: Upvote System
`vote_meme(post_id, user_id, 1)` casts an upvote. `get_meme_score(post_id)`
returns net score.

**Test:** `test_meme_vote_up` — Score == 1 after one upvote.

### Prompt 15: Downvote System
`vote_meme(post_id, user_id, -1)` casts a downvote.

**Test:** `test_meme_vote_down` — Score == -1 after one downvote.

### Prompt 16: Meme Leaderboard
`get_top_memes(user_id, limit)` returns friends' memes ordered by score desc.

**Test:** `test_meme_leaderboard` — Results sorted by score descending.

## Organization & Workflow

### Prompt 17: Meme Collections
`create_meme_collection(user_id, name, description)` creates a named folder.
`list_meme_collections(user_id)` lists them.

**Test:** `test_meme_collection_create` — Collection appears in list.

### Prompt 18: Collection Add/Remove
`add_to_collection(collection_id, post_id)` and
`remove_from_collection(collection_id, post_id)` manage items.

**Test:** `test_meme_collection_add_remove` — Add then remove verifies empty.

### Prompt 19: Custom Meme Tags
`tag_meme_post(post_id, tag_name)` creates/links a tag.
`get_meme_post_tags(post_id)` returns tag names.

**Test:** `test_meme_tagging` — "funny" and "cats" tags appear.

### Prompt 20: Meme Drafts
`update_meme_post(post_id, is_meme_draft=1)` marks as draft.
`list_meme_drafts(user_id)` lists unfinished memes.

**Test:** `test_meme_draft` — Draft appears in user's draft list.

### Prompt 21: Meme Scheduling
`update_meme_post(post_id, meme_scheduled_at="2026-08-01 10:00")` schedules.
`list_scheduled_memes(user_id)` returns upcoming.

**Test:** `test_meme_scheduling` — Scheduled meme appears in list.

## Variations & Tools

### Prompt 22: A/B Variant Creation
`create_ab_variant(original_post_id, variant_post_id)` creates a variant pair.
`get_ab_variant(variant_id)` returns the pair.

**Test:** `test_ab_variant_creation` — Variant links original and variant posts.

### Prompt 23: A/B Variant Voting
`vote_ab(variant_id, choice)` increments votes_a or votes_b.

**Test:** `test_ab_variant_voting` — 2 votes for A, 1 for B.

### Prompt 24: Filter Roulette
`/meme/filter-roulette` picks a random filter from `list_meme_filters()` and
redirects to meme creation with it pre-selected.

**Test:** `test_filter_roulette` — Random choice from 8+ filters is valid.

### Prompt 25: Filter Strength Slider
Add `filter_strength` column to `posts` (default 100).
`update_meme_post(post_id, filter_strength=50)` sets intensity.

**Test:** `test_filter_strength` — `get_post()["filter_strength"]` == 50.

### Prompt 26: Before/After Comparison
`/meme/<id>/compare` shows side-by-side original vs filtered. Requires both
`photo_url` and `filter_id` on the post.

**Test:** `test_before_after_compare` — Post has both fields for comparison.

### Prompt 27: Meme Grid Maker
`/meme/grid` creates a grid meme. `update_meme_post(post_id,
meme_grid_layout="2x2")` sets layout.

**Test:** `test_meme_grid` — `get_post()["meme_grid_layout"]` == "2x2".

### Prompt 28: Meme of the Day
`get_meme_of_the_day()` deterministically picks a meme using date + post hash.
Same result all day, changes next day.

**Test:** `test_meme_of_the_day` — Returns dict or None without error.

## Social & Discovery

### Prompt 29: Meme Stats Page
`get_meme_stats(post_id)` returns `{votes, reactions, remixes, views}`.

**Test:** `test_meme_stats` — Stats dict has votes=1 and reactions>=1.

### Prompt 30: Meme JSON Export
`export_meme_json(post_id)` returns full meme data as dict: post, tags,
stickers, reactions.

**Test:** `test_meme_json_export` — Exported dict contains id, top_text, filter_id.

## Additional Tests

- `test_meme_trending_tags` — `get_trending_meme_tags()` returns a list.
- `test_meme_search` — `search_meme_posts("hello")` finds matching posts.
- `test_meme_challenge_create` — `create_meme_challenge()` creates a challenge.
- `test_meme_challenge_enter` — `enter_meme_challenge()` creates an entry.
- `test_meme_remix_of_the_day` — Meme of the day is deterministic (same result twice).