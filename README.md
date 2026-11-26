# advocatesetu-social

Public hosting for AdvocateSetu's daily social media posts (served via GitHub Pages so Instagram/LinkedIn can fetch them).

- `brand/` — logo, avatar, X header, LinkedIn cover
- `daily/YYYY-MM-DD/` — `content.json` (copy + captions), `banner.jpg` (1080×1350), `reel.mp4` (1080×1920), `cover.jpg`, `log.json` (what was posted)
- `tools/make_post.py` — renders banner and reel from `content.json`: `python3 tools/make_post.py daily/YYYY-MM-DD/content.json`

Public URL base: https://iampankaj0601.github.io/advocatesetu-social/

## Story format (from 2026-11-27)

- `tools/make_story.py` — bold-colour story posts with original illustrated characters: `python3 tools/make_story.py daily/YYYY-MM-DD/content.json`
  - reads `content.story` (characters, hook, dialogue, facts, ending, cta) and `content.banner` (+ `banner.highlight`)
  - writes `reel.mp4` (chat-story reel with an original synthesised music track + pop/whoosh SFX), `cover.jpg`, `carousel_1..N.jpg` (1080×1350) and `banner.jpg`
  - palettes rotate daily (`punch`, `electric`, `sunset`, `mint`) or set `story.palette`
- `tools/story_art.py` (characters, bubbles, highlights), `tools/story_music.py` (royalty-free music, generated from scratch)
- Example: `samples/2026-11-26-story/content.json`
