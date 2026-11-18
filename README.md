# advocatesetu-social

Public hosting for AdvocateSetu's daily social media posts (served via GitHub Pages so Instagram/LinkedIn can fetch them).

- `brand/` — logo, avatar, X header, LinkedIn cover
- `daily/YYYY-MM-DD/` — `content.json` (copy + captions), `banner.jpg` (1080×1350), `reel.mp4` (1080×1920), `cover.jpg`, `log.json` (what was posted)
- `tools/make_post.py` — renders banner and reel from `content.json`: `python3 tools/make_post.py daily/YYYY-MM-DD/content.json`

Public URL base: https://iampankaj0601.github.io/advocatesetu-social/
