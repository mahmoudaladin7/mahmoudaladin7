"""
Live GitHub activity card — regenerated every day by the profile Action.

    GITHUB_TOKEN=xxx python profile/build_stats.py --out dist
    python profile/build_stats.py --mock --out preview      # offline preview

Self-hosted on purpose: the public github-readme-stats instance is
rate-limited, so third-party cards often show up broken. This one can't.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import urllib.request

from svgkit import THEMES, Doc, a, measure, save

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
CFG = C.get("stats", {})

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ── data ────────────────────────────────────────────────────────────────
def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload["data"]["user"]


def mock() -> dict:
    rnd = random.Random(7)
    start = dt.date.today() - dt.timedelta(days=364)
    weeks, cur = [], []
    for i in range(365):
        d = start + dt.timedelta(days=i)
        busy = rnd.random() < (0.72 if d.weekday() < 5 else 0.35)
        cur.append({"date": d.isoformat(), "contributionCount": rnd.randint(1, 14) if busy else 0})
        if len(cur) == 7:
            weeks.append({"contributionDays": cur}); cur = []
    if cur:
        weeks.append({"contributionDays": cur})
    for w in weeks[-1:]:
        for day in w["contributionDays"]:
            day["contributionCount"] = max(day["contributionCount"], 3)
    langs = [("TypeScript", 812_000), ("JavaScript", 402_000), ("Python", 288_000), ("Dart", 240_000),
             ("Java", 96_000), ("Go", 40_000), ("HTML", 900_000)]
    return {
        "repositories": {"totalCount": 34, "nodes": [
            {"stargazerCount": 3, "languages": {"edges": [{"size": s, "node": {"name": n}} for n, s in langs]}}]},
        "contributionsCollection": {"contributionCalendar": {
            "totalContributions": sum(d["contributionCount"] for w in weeks for d in w["contributionDays"]),
            "weeks": weeks}},
    }


def summarize(u: dict) -> dict:
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]

    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:      # today not started yet — don't break the streak
        i -= 1
    while i >= 0 and counts[i]:
        current += 1
        i -= 1

    exclude = set(CFG.get("exclude_languages", []))
    sizes: dict[str, int] = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            if n not in exclude:
                sizes[n] = sizes.get(n, 0) + e["size"]
    total = sum(sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    top = [(n, s / total) for n, s in ranked[:5]]
    rest = sum(s for _, s in ranked[5:]) / total
    if rest > 0.005:
        top.append(("Other", rest))

    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]][-26:]
    return {
        "total": cal["totalContributions"],
        "active": sum(1 for c in counts if c),
        "longest": longest,
        "current": current,
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "langs": top,
        "weekly": weekly,
    }


# ── render ──────────────────────────────────────────────────────────────
def tiles(s: dict) -> list:
    """KPI tiles. Current streak only shows when it's alive, otherwise active days."""
    return [
        (f'{s["total"]:,}', "", "CONTRIBUTIONS · 12 MO"),
        (str(s["current"]), "days", "CURRENT STREAK") if s["current"] >= 2
        else (str(s["active"]), "days", "ACTIVE DAYS · 12 MO"),
        (str(s["longest"]), "days", "LONGEST STREAK"),
        (str(s["repos"]), "", "PUBLIC REPOSITORIES"),
    ]


def render(theme: dict, s: dict) -> Doc:
    t = theme
    W, H = 1200, 352
    d = Doc(W, H, t, "GitHub activity",
            f'{s["total"]} contributions in the last year, longest streak {s["longest"]} days')
    clip = d.clip_card(24)
    d.add(d.card(rx=24))
    d.add(d.orbs([(1130, 30, 190, "g3", -40, 30, 17), (80, 360, 170, "g1", 40, -20, 15)], clip))

    d.add(f'<path d="M48 49 l5.5 5 l-5.5 5" stroke="{t["pink"]}" stroke-width="2.2" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(66, 59, [("gh stats ", t["text"]), ("--live --last 12mo", t["faint"])], "mono", 15))
    stamp = "updated " + dt.datetime.utcnow().strftime("%Y-%m-%d")
    d.add(d.live_dot(W - 48 - measure(stamp, "mono", 12.5) - 16, 54.5, t["green"], 3.6))
    d.add(d.text(W - 48, 59, stamp, "mono", 12.5, t["faint"], anchor="end"))
    d.add(f'<rect x="40" y="82" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')

    streak_live = s["current"] >= 2
    gap, tx0, ty0, th = 16, 40, 104, 120
    tw = (W - 80 - gap * 3) / 4
    vg = d.brand_gradient(d.uid("vg"), 40, W - 40, animate=False)
    vals: list = []
    for i, (val, unit, label) in enumerate(tiles(s)):
        x = tx0 + i * (tw + gap)
        d.add(f'<rect x="{a(x)}" y="{ty0}" width="{a(tw)}" height="{th}" rx="16" fill="{t["bg2"]}" '
              f'fill-opacity=".85" stroke="{t["line"]}" stroke-opacity="{t["line_o"]}"/>')
        d.add(d.text(x + 22, ty0 + 64, val, "display", 46, vg, ls=-1.2))
        if unit:
            vw = measure(val, "display", 46, -1.2)
            d.add(d.text(x + 22 + vw + 8, ty0 + 64, unit, "medium", 18, t["muted"]))
        d.add(d.text(x + 22, ty0 + 96, label, "mono", 11.5, t["faint"], ls=1.3))
        if i == 1 and streak_live:
            d.add(d.live_dot(x + tw - 24, ty0 + 24, t["green"], 4))
        if i == 0 and s["weekly"]:
            # 26-week sparkline tucked into the first tile (skipped if the number is too wide)
            v_end = x + 22 + measure(val, "display", 46, -1.2)
            sx = max(v_end + 18, x + tw - 22 - 100)
            sy, sw, sh = ty0 + 28, x + tw - 22 - sx, 36
            vals = s["weekly"] if sw >= 56 else []
        if i == 0 and len(vals) > 1:
            mx = max(vals) or 1
            pts = [(sx + j * sw / (len(vals) - 1), sy + sh - v / mx * sh) for j, v in enumerate(vals)]
            line = " ".join(f"{'M' if j == 0 else 'L'}{a(px)} {a(py)}" for j, (px, py) in enumerate(pts))
            ag = d.uid("ag")
            d.defs.append(f'<linearGradient id="{ag}" x1="0" y1="{sy}" x2="0" y2="{sy+sh}" gradientUnits="userSpaceOnUse">'
                          f'<stop offset="0" stop-color="{t["g1"]}" stop-opacity=".35"/>'
                          f'<stop offset="1" stop-color="{t["g1"]}" stop-opacity="0"/></linearGradient>')
            d.add(f'<path d="{line} L{a(sx+sw)} {a(sy+sh)} L{a(sx)} {a(sy+sh)}Z" fill="url(#{ag})"/>')
            d.add(f'<path d="{line}" stroke="{t["violet"]}" stroke-width="1.8" fill="none" '
                  f'stroke-linejoin="round" stroke-linecap="round"/>')
            d.add(f'<circle cx="{a(pts[-1][0])}" cy="{a(pts[-1][1])}" r="3" fill="{t["violet"]}"/>')

    if s["langs"]:
        d.add(d.text(40, 262, "TOP LANGUAGES · BY CODE VOLUME", "mono", 11.5, t["faint"], ls=1.3))
        colors = [t["violet"], t["pink"], t["blue"], t["cyan"], t["amber"], t["faint"]]
        bx, bw, by = 40, W - 80, 276
        bclip = d.uid("bar")
        d.defs.append(f'<clipPath id="{bclip}"><rect x="{bx}" y="{by}" width="{bw}" height="10" rx="5"/></clipPath>')
        segs, cx = [], bx
        for i, (n, p) in enumerate(s["langs"]):
            w = bw * p
            segs.append(f'<rect x="{a(cx)}" y="{by}" width="{a(max(w - 2, 1))}" height="10" fill="{colors[i]}"/>')
            cx += w
        an = d.uid("grow")
        d.css.append(f"@keyframes {an}{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}"
                     f".{an}{{transform-box:fill-box;transform-origin:left;animation:{an} 1.4s cubic-bezier(.2,.8,.2,1) both}}")
        d.add(f'<g clip-path="url(#{bclip})"><g class="{an}">{"".join(segs)}</g></g>')
        lx = bx
        for i, (n, p) in enumerate(s["langs"]):
            lab = f"{n} {p * 100:.1f}%"
            d.add(f'<circle cx="{a(lx + 5)}" cy="{H - 38}" r="5" fill="{colors[i]}"/>')
            d.add(d.spans(lx + 18, H - 33.5, [(n + " ", t["text"]), (f"{p * 100:.1f}%", t["faint"])], "mono", 13))
            lx += 18 + measure(lab, "mono", 13) + 30
    return d


def render_mobile(theme: dict, s: dict) -> Doc:
    """Phone layout (served under 768px): 2×2 tiles, wrapped language legend."""
    t = theme
    W = 720
    colors = [t["violet"], t["pink"], t["blue"], t["cyan"], t["amber"], t["faint"]]
    # pre-flow the legend to know the height
    legend, lx, ly = [], 40, 0
    for i, (n, p) in enumerate(s["langs"]):
        w = 26 + measure(f"{n} {p * 100:.1f}%", "mono", 19) + 34
        if lx + w > W - 40:
            lx, ly = 40, ly + 40
        legend.append((lx, ly, n, p, colors[i]))
        lx += w
    H = int(574 + ly + 44) if s["langs"] else 492
    d = Doc(W, H, t, "GitHub activity",
            f'{s["total"]} contributions in the last year, longest streak {s["longest"]} days')
    clip = d.clip_card(32)
    d.add(d.card(rx=32))
    d.add(d.orbs([(700, 30, 220, "g3", -40, 30, 17), (40, H, 200, "g1", 40, -20, 15)], clip))
    d.add(f'<path d="M44 58 l8 7 l-8 7" stroke="{t["pink"]}" stroke-width="3" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(68, 72, [("gh stats ", t["text"]), ("--live", t["faint"])], "mono", 22))
    stamp = dt.datetime.utcnow().strftime("%Y-%m-%d")
    d.add(d.live_dot(W - 48 - measure(stamp, "mono", 17) - 20, 66, t["green"], 5))
    d.add(d.text(W - 44, 72, stamp, "mono", 17, t["faint"], anchor="end"))
    d.add(f'<rect x="40" y="100" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')

    vg = d.brand_gradient(d.uid("vg"), 40, W - 40, animate=False)
    tw, th = (W - 80 - 16) / 2, 156
    for i, (val, unit, label) in enumerate(tiles(s)):
        x = 40 + (i % 2) * (tw + 16)
        y = 124 + (i // 2) * (th + 16)
        d.add(f'<rect x="{a(x)}" y="{y}" width="{a(tw)}" height="{th}" rx="22" fill="{t["bg2"]}" '
              f'fill-opacity=".85" stroke="{t["line"]}" stroke-opacity="{t["line_o"]}"/>')
        d.add(d.text(x + 28, y + 84, val, "display", 62, vg, ls=-1.6))
        if unit:
            d.add(d.text(x + 28 + measure(val, "display", 62, -1.6) + 10, y + 84, unit, "medium", 24, t["muted"]))
        d.add(d.text(x + 28, y + 126, label, "mono", 15, t["faint"], ls=1.3))
        if i == 1 and s["current"] >= 2:
            d.add(d.live_dot(x + tw - 30, y + 30, t["green"], 6))

    if s["langs"]:
        d.add(d.text(40, 500, "TOP LANGUAGES", "mono", 15, t["faint"], ls=1.3))
        bx, bw, by = 40, W - 80, 518
        bclip = d.uid("bar")
        d.defs.append(f'<clipPath id="{bclip}"><rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath>')
        segs, cx = [], bx
        for i, (n, p) in enumerate(s["langs"]):
            segs.append(f'<rect x="{a(cx)}" y="{by}" width="{a(max(bw * p - 3, 1))}" height="14" fill="{colors[i]}"/>')
            cx += bw * p
        d.add(f'<g clip-path="url(#{bclip})">{"".join(segs)}</g>')
        for lx, ly, n, p, col in legend:
            yy = 574 + ly
            d.add(f'<circle cx="{a(lx + 7)}" cy="{yy - 7}" r="7" fill="{col}"/>')
            d.add(d.spans(lx + 24, yy, [(n + " ", t["text"]), (f"{p * 100:.1f}%", t["faint"])], "mono", 19))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    login = os.environ.get("GITHUB_USER") or C["links"]["github_user"]
    data = mock() if args.mock else fetch(login, os.environ["GITHUB_TOKEN"])
    s = summarize(data)
    for name, t in THEMES.items():
        for suffix, fn in (("", render), ("mobile-", render_mobile)):
            p = save(fn(t, s), os.path.join(args.out, f"stats-{suffix}{name}.svg"))
            print("  wrote", p)
    print("  ", {k: v for k, v in s.items() if k != "weekly"})


if __name__ == "__main__":
    main()
