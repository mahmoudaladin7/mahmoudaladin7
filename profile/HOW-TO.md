# How this profile works

Every image in the README is an SVG generated from **`profile/content.json`**: one palette, one type system, dark + light, desktop + phone.

## First-time setup (5 minutes)

1. The repo must be named exactly **`mahmoudaladin7/mahmoudaladin7`** (GitHub's special profile repo) and be **public**.
2. Put `README.md`, `assets/`, `profile/` and `.github/` in the repo root and push to `main`.
3. The push runs the `profile` workflow automatically, which publishes the live stats card and the contribution snake to the `output` branch (give it ~2 minutes). After that it refreshes itself every day. You can also trigger it from **Actions → profile → Run workflow**.

> If that run fails with a 403 on push: **Settings → Actions → General → Workflow permissions → Read and write**, then run it again.

## Updating content

Edit `profile/content.json` (right on github.com is fine) and commit. The `artwork` job rebuilds every SVG and the projects block in the README within a minute or two.

| You want to…                      | Edit in `content.json`                         |
| --------------------------------- | ---------------------------------------------- |
| Change name, role, tagline        | `name`, `role`, `tagline`                      |
| Update the 3 numbers in the hero  | `highlights`                                   |
| Change what the terminal types    | `terminal` (keep lines ≤ 38 characters)        |
| Add / remove / reorder projects   | `projects` (status: `live`, `client`, `build`, `open`) |
| Add a new job                     | `experience` (put it first, `"current": true`) |
| Add a tool                        | `toolbox` (ids come from skillicons.dev; add a matching icon in `profile/icons/`) |
| Hide noisy languages from stats   | `stats.exclude_languages`                      |

## Building locally (optional)

```bash
pip install fonttools brotli
python profile/build_assets.py           # all artwork + README projects block
python profile/build_stats.py --mock --out preview   # stats card with sample data
```

## Credits

Fonts: Space Grotesk, Inter, JetBrains Mono (SIL Open Font License).
Toolbox icons: [skill-icons](https://github.com/tandpfun/skill-icons) (MIT, see `profile/icons/LICENSE`).
Contribution snake: [Platane/snk](https://github.com/Platane/snk).
