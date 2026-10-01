"""
Builds every static SVG in /assets from content.json — in dark and light.

    pip install fonttools brotli
    python profile/build_assets.py

The GitHub Action runs this automatically whenever profile/ changes,
so editing content.json on github.com is enough.
"""
from __future__ import annotations

import hashlib
import json
import os

from svgkit import ACCENTS, THEMES, Doc, a, measure, save, wrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
C = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.json"), encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════
#  HERO — name, tagline, highlights + a live-typing terminal
# ═══════════════════════════════════════════════════════════════════════
def terminal(d, t, tx, ty, tw, k=1.0):
    """Animated terminal. k scales every metric (1.0 desktop, ~1.5 mobile). Returns height."""
    rows = sum(1 + len(b["out"]) for b in C["terminal"]) + 1
    th = k * (44 + 40 + (rows - 1) * 28 + 40)
    glow = d.uid("glow")
    d.defs.append(f'<filter id="{glow}" x="-30%" y="-30%" width="160%" height="160%">'
                  f'<feGaussianBlur stdDeviation="{a(28 * k)}"/></filter>')
    glow_grad = d.brand_gradient(d.uid("tg"), tx, tx + tw, dur=9)
    d.add(f'<rect x="{a(tx + 18*k)}" y="{a(ty + 26*k)}" width="{a(tw - 36*k)}" height="{a(th - 30*k)}" rx="20" '
          f'fill="{glow_grad}" opacity="{0.55 if t["name"] == "dark" else 0.32}" filter="url(#{glow})"/>')
    r = 16 * k
    d.add(f'<rect x="{a(tx)}" y="{a(ty)}" width="{a(tw)}" height="{a(th)}" rx="{a(r)}" fill="{t["term"]}"/>')
    d.add(f'<rect x="{a(tx+.5)}" y="{a(ty+.5)}" width="{a(tw-1)}" height="{a(th-1)}" rx="{a(r-.5)}" fill="none" '
          f'stroke="#FFFFFF" stroke-opacity=".1"/>')
    for i, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        d.add(f'<circle cx="{a(tx + (24 + i * 20) * k)}" cy="{a(ty + 22 * k)}" r="{a(6 * k)}" fill="{col}"/>')
    d.add(d.text(tx + tw / 2, ty + 27 * k, "mahmoud@dev: ~", "mono", 12.5 * k, "#6E7191", anchor="middle"))
    d.add(f'<rect x="{a(tx)}" y="{a(ty + 44*k)}" width="{a(tw)}" height="1" fill="#FFFFFF" fill-opacity=".07"/>')

    tclip = d.uid("tclip")
    d.defs.append(f'<clipPath id="{tclip}"><rect x="{a(tx+1)}" y="{a(ty+45*k)}" width="{a(tw-2)}" '
                  f'height="{a(th-46*k)}" rx="{a(r-1)}"/></clipPath>')

    D = THEMES["dark"]                   # the terminal is always dark
    size, cw, lh = 15 * k, 9.0 * k, 28 * k   # JetBrains Mono advance = 0.6em
    lx, py = tx + 24 * k, ty + 84 * k
    cx0 = lx + 18 * k

    tl, tcur = [], 0.7
    for blk in C["terminal"]:
        ps = tcur
        ts = ps + 0.35
        te = ts + len(blk["cmd"]) * 0.075
        outs = [te + 0.3 + j * 0.22 for j in range(len(blk["out"]))]
        tl.append((ps, ts, te, outs))
        tcur = (outs[-1] if outs else te) + 1.0
    t_final = tcur
    T = round(t_final + 4.5, 2)
    pct = lambda s_: f"{s_ / T * 100:.3f}%"
    eps = 0.02

    term = [f'<g clip-path="url(#{tclip})"><g class="tall">']
    d.css.append(f"@keyframes tall{{0%,95%{{opacity:1}}98.5%,100%{{opacity:0}}}}"
                 f".tall{{animation:tall {T}s linear infinite}}")
    d.css.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
                 ".blink{animation:blink 1.05s step-end infinite}"
                 "@media (prefers-reduced-motion:reduce){.cur{display:none}}")

    def show_at(cls, s0, s1=None):
        if s1 is None:
            kf = f"0%,{pct(s0 - eps)}{{opacity:0}}{pct(s0)},100%{{opacity:1}}"
        else:
            kf = (f"0%,{pct(s0 - eps)}{{opacity:0}}{pct(s0)},{pct(s1 - eps)}{{opacity:1}}"
                  f"{pct(s1)},100%{{opacity:0}}")
        d.css.append(f"@keyframes {cls}{{{kf}}}.{cls}{{animation:{cls} {T}s linear infinite}}")

    def chevron(x, y):
        return (f'<path d="M{a(x)} {a(y-10*k)} l{a(5.5*k)} {a(5*k)} l{a(-5.5*k)} {a(5*k)}" stroke="{D["pink"]}" '
                f'stroke-width="{a(2.2*k)}" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')

    row = 0
    for i, (blk, (ps, ts, te, outs)) in enumerate(zip(C["terminal"], tl)):
        y = py + row * lh
        n = len(blk["cmd"])
        shift = n * cw
        pcls, ccls, vcls = f"p{i}", f"c{i}", f"v{i}"
        show_at(pcls, ps)
        d.css.append(
            f"@keyframes {ccls}{{0%,{pct(ts)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
            f"{pct(te)},100%{{transform:translateX({a(shift)}px)}}}}"
            f".{ccls}{{transform:translateX({a(shift)}px);animation:{ccls} {T}s linear infinite}}")
        show_at(vcls, ps, outs[0] if outs else te + 0.4)
        term.append(
            f'<g class="{pcls}">{chevron(lx, y)}'
            + d.text(cx0, y, blk["cmd"], "mono", size, D["text"])
            + f'<rect class="{ccls}" x="{a(cx0 - 1)}" y="{a(y - 15*k)}" width="{a(shift + 4*k)}" '
              f'height="{a(21*k)}" fill="{t["term"]}"/>'
            + f'<g class="{vcls} cur"><rect class="{ccls}" x="{a(cx0)}" y="{a(y - 13*k)}" '
              f'width="{a(cw)}" height="{a(17*k)}" rx="1.5" fill="{D["violet"]}" opacity=".9"/></g></g>')
        row += 1
        for j, parts in enumerate(blk["out"]):
            y = py + row * lh
            ocls = f"o{i}_{j}"
            show_at(ocls, outs[j])
            term.append(d.spans(lx, y, [(s_, D[c]) for s_, c in parts], "mono", size, cls=ocls))
            row += 1

    y = py + row * lh
    show_at("pf", t_final)
    term.append(f'<g class="pf">{chevron(lx, y)}<rect class="blink" x="{a(cx0)}" y="{a(y - 13*k)}" '
                f'width="{a(cw)}" height="{a(17*k)}" rx="1.5" fill="{D["violet"]}"/></g>')
    term.append("</g></g>")
    d.add("".join(term))
    return th


def highlights(d, t, x, y, vsize, lsize, gap):
    """Row of big gradient numbers with mono captions; y = value baseline."""
    val_grad = d.brand_gradient(d.uid("vg"), x, x + 560, animate=False)
    hx = x
    for i, h in enumerate(C["highlights"]):
        if i:
            d.add(f'<rect x="{a(hx - gap / 2)}" y="{a(y - vsize * .87)}" width="1" height="{a(vsize * 1.4)}" '
                  f'fill="{t["line"]}" fill-opacity="{t["line_o"] * 1.6}"/>')
        d.add(d.text(hx, y, h["value"], "display", vsize, val_grad, ls=-0.5))
        d.add(d.text(hx, y + lsize * 2.1, h["label"].upper(), "mono", lsize, t["faint"], ls=1.2))
        hx += max(measure(h["value"], "display", vsize, -0.5),
                  measure(h["label"].upper(), "mono", lsize, 1.2)) + gap


def hero(theme):
    t = theme
    W, H = 1200, 520
    d = Doc(W, H, t, f'{" ".join(C["name"])} — {C["role"]}', C["tagline"])
    clip = d.clip_card(28)
    d.add(d.card(rx=28))
    d.add(d.orbs([(150, 40, 230, "g1", 60, 40, 16),
                  (1080, 500, 260, "g3", -70, -30, 19),
                  (640, 560, 170, "g2", 40, -50, 13)], clip))
    d.add(d.dot_grid(clip, 300, 220, 520, 400))

    x = 68
    d.add(f'<rect x="{x}" y="80" width="32" height="3" rx="1.5" '
          f'fill="{d.brand_gradient(d.uid("gb"), x, x + 32, animate=False)}"/>')
    d.add(d.text(x + 46, 87, C["role"].upper(), "mono", 13.5, t["muted"], ls=2))
    name_grad = d.brand_gradient(d.uid("ng"), x, x + 520, dur=7)
    d.add(d.text(x - 4, 184, C["name"][0], "display", 88, t["text"], ls=-2.5))
    d.add(d.text(x - 4, 270, C["name"][1], "display", 88, name_grad, ls=-2.5))
    for i, line in enumerate(wrap(C["tagline"], "body", 20, 520, 3)):
        d.add(d.text(x, 322 + i * 31, line, "body", 20, t["muted"]))
    highlights(d, t, x, 458, 32, 11.5, 48)
    terminal(d, t, 664, 72, 472, 1.0)
    return d


def hero_mobile(theme):
    t = theme
    W, x, inner = 720, 48, 624
    lines = wrap(C["tagline"], "body", 28, inner, 5)
    tag_y = 388
    hl_y = tag_y + (len(lines) - 1) * 40 + 92
    ty = hl_y + 62
    k = 1.5
    rows = sum(1 + len(b["out"]) for b in C["terminal"]) + 1
    H = int(ty + k * (44 + 40 + (rows - 1) * 28 + 40) + 48)
    d = Doc(W, H, t, f'{" ".join(C["name"])} — {C["role"]}', C["tagline"])
    clip = d.clip_card(32)
    d.add(d.card(rx=32))
    d.add(d.orbs([(80, 60, 260, "g1", 50, 40, 16), (680, H - 40, 280, "g3", -50, -30, 19),
                  (520, 520, 180, "g2", 30, -40, 13)], clip))
    d.add(d.dot_grid(clip, 300, 260, 520, 480))
    d.add(f'<rect x="{x}" y="78" width="36" height="4" rx="2" '
          f'fill="{d.brand_gradient(d.uid("gb"), x, x + 36, animate=False)}"/>')
    d.add(d.text(x + 52, 86, C["role"].upper(), "mono", 17, t["muted"], ls=2))
    name_grad = d.brand_gradient(d.uid("ng"), x, x + 560, dur=7)
    d.add(d.text(x - 5, 204, C["name"][0], "display", 116, t["text"], ls=-3.5))
    d.add(d.text(x - 5, 318, C["name"][1], "display", 116, name_grad, ls=-3.5))
    for i, line in enumerate(lines):
        d.add(d.text(x, tag_y + i * 40, line, "body", 28, t["muted"]))
    highlights(d, t, x, hl_y, 46, 15, 40)
    terminal(d, t, x, ty, inner, k)
    return d


# ═══════════════════════════════════════════════════════════════════════
#  BUTTONS
# ═══════════════════════════════════════════════════════════════════════
def icon(kind, x, y, color):
    if kind == "portfolio":
        return (f'<g fill="none" stroke="{color}" stroke-width="1.8"><circle cx="{x+9}" cy="{y+9}" r="8.2"/>'
                f'<ellipse cx="{x+9}" cy="{y+9}" rx="3.6" ry="8.2"/><path d="M{x+1} {y+9}h16"/></g>')
    if kind == "linkedin":
        return (f'<g><rect x="{x}" y="{y}" width="18" height="18" rx="4" fill="{color}"/>'
                f'<rect x="{x+3.6}" y="{y+7.4}" width="2.6" height="7.2" fill="#fff"/>'
                f'<circle cx="{x+4.9}" cy="{y+4.6}" r="1.55" fill="#fff"/>'
                f'<path d="M{x+8.2} {y+7.4}h2.5v1.1c.5-.8 1.4-1.3 2.6-1.3 2 0 2.9 1.2 2.9 3.4v4h-2.6v-3.6'
                f'c0-1-.4-1.6-1.3-1.6s-1.5.6-1.5 1.6v3.6h-2.6z" fill="#fff"/></g>')
    if kind == "email":
        return (f'<g fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round">'
                f'<rect x="{x}" y="{y+2.5}" width="18" height="13" rx="2.5"/>'
                f'<path d="M{x+1} {y+4} l8 6 l8 -6"/></g>')
    return ""


def button(theme, kind, label, primary=False):
    t = theme
    lw = measure(label, "medium", 18)
    W, H = int(24 + 18 + 12 + lw + 14 + 12 + 24), 56
    d = Doc(W, H, t, label)
    if primary:
        g = d.brand_gradient(d.uid("bg"), 0, W, dur=5)
        d.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{(H-2)/2}" fill="{t["bg2"]}" '
              f'stroke="{g}" stroke-width="2"/>')
    else:
        d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="{(H-1)/2}" fill="{t["bg2"]}" '
              f'stroke="{t["line"]}" stroke-opacity="{t["line_o"] * 1.4}"/>')
    ic = {"portfolio": t["violet"], "linkedin": t["blue"], "email": t["pink"]}[kind]
    d.add(icon(kind, 24, 19, ic))
    d.add(d.text(24 + 18 + 12, 34.5, label, "medium", 18, t["text"]))
    d.add(d.arrow_ne(W - 24 - 11, 22.5, 11, t["faint"], 2))
    return d


# ═══════════════════════════════════════════════════════════════════════
#  PROJECT CARDS
# ═══════════════════════════════════════════════════════════════════════
STATUS = {
    "live":   ("LIVE",        "green"),
    "client": ("CLIENT WORK", "muted"),
    "build":  ("PRODUCT",     "muted"),
    "open":   ("OPEN SOURCE", "muted"),
}


def project(theme, p, idx):
    t = theme
    W, H = 600, 300
    acc = t[ACCENTS[idx % 3]]
    d = Doc(W, H, t, p["title"], p["description"])
    clip = d.clip_card(22)
    d.add(d.card(rx=22))

    # corner glow + animated top hairline
    blur = d.uid("cg")
    d.defs.append(f'<filter id="{blur}" x="-60%" y="-60%" width="220%" height="220%">'
                  f'<feGaussianBlur stdDeviation="55"/></filter>')
    d.add(f'<g clip-path="url(#{clip})"><circle cx="{W-40}" cy="-10" r="130" fill="{acc}" '
          f'opacity="{0.30 if t["name"] == "dark" else 0.16}" filter="url(#{blur})"/>'
          f'<rect x="0" y="0" width="{W}" height="3" fill="{d.brand_gradient(d.uid("hl"), 0, W, dur=6 + idx)}"/></g>')
    d.add(d.dot_grid(clip, W - 60, 0, 260, 200, 20))

    # header row
    d.add(d.spans(32, 52, [(f"{idx+1:02d}", acc, "monob"), ("  /  " + p["category"].upper(), t["faint"])],
                  "mono", 13, ls=1.4))
    label, ck = STATUS.get(p.get("status", ""), ("", "muted"))
    if label:
        lw = measure(label, "mono", 11.5, 1.2)
        dot = 14 if p.get("status") == "live" else 0
        pw = lw + 24 + dot
        px = W - 32 - pw
        col = t[ck]
        d.add(f'<rect x="{a(px)}" y="33" width="{a(pw)}" height="26" rx="13" fill="{col}" '
              f'fill-opacity="{0.12 if ck == "green" else 0.0}" stroke="{col}" stroke-opacity="{.45 if ck == "green" else .3}"/>')
        if dot:
            d.add(d.live_dot(px + 15, 46, col, 3.6))
        d.add(d.text(px + 12 + dot, 50.2, label, "mono", 11.5, col, ls=1.2))

    # title (+ arrow if linked)
    title = wrap(p["title"], "display", 34, W - 64 - (40 if p.get("url") else 0), 1)[0]
    d.add(d.text(32, 112, title, "display", 34, t["text"], ls=-0.8))
    if p.get("url"):
        tw = measure(title, "display", 34, -0.8)
        d.add(d.arrow_ne(32 + tw + 14, 89, 15, acc, 2.4))

    for i, line in enumerate(wrap(p["description"], "body", 17.5, W - 64, 3)):
        d.add(d.text(32, 152 + i * 27, line, "body", 17.5, t["muted"]))

    cx = 32
    for tech in p["tech"]:
        w, svg = d.chip(cx, H - 32 - 28, tech, acc)
        if cx + w > W - 32:
            break
        d.add(svg)
        cx += w + 8
    return d


# ═══════════════════════════════════════════════════════════════════════
#  EXPERIENCE — rendered as `git log --graph`
# ═══════════════════════════════════════════════════════════════════════
def timeline(theme):
    t = theme
    W = 1200
    rows, y = [], 118
    for e in C["experience"]:
        lines = wrap(e["summary"], "body", 17.5, 860, 2)
        h = 18 + 34 + (len(lines) - 1) * 26 + 22 + 26 + 34
        rows.append((e, lines, y, h))
        y += h
    H = int(y + 10)
    d = Doc(W, H, t, "Experience", " → ".join(f'{e["role"]} at {e["company"]}' for e in C["experience"]))
    clip = d.clip_card(24)
    d.add(d.card(rx=24))
    d.add(d.orbs([(1150, 40, 200, "g1", -40, 30, 18)], clip))

    # header
    d.add(f'<path d="M48 51 l5.5 5 l-5.5 5" stroke="{t["pink"]}" stroke-width="2.2" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(66, 61, [("git log ", t["text"]), ("--graph --career", t["faint"])], "mono", 15))
    d.add(f'<rect x="40" y="84" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')

    # rail
    nx = 72
    y_first, y_last = rows[0][2] + 10, rows[-1][2] + 10
    rail = d.uid("rail")
    d.defs.append(f'<linearGradient id="{rail}" x1="0" y1="{y_first}" x2="0" y2="{y_last + 60}" '
                  f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{t["g1"]}"/>'
                  f'<stop offset=".6" stop-color="{t["g3"]}"/><stop offset="1" stop-color="{t["g3"]}" stop-opacity="0"/>'
                  f'</linearGradient>')
    d.add(f'<rect x="{nx-1}" y="{y_first}" width="2" height="{y_last - y_first + 60}" fill="url(#{rail})"/>')

    role_grad = d.brand_gradient(d.uid("rg"), 0, W, animate=False)
    for i, (e, lines, y0, h) in enumerate(rows):
        acc = t[ACCENTS[i % 3]]
        cy = y0 + 10
        if e.get("current"):
            d.add(d.live_dot(nx, cy, t["green"], 7))
            d.add(f'<circle cx="{nx}" cy="{cy}" r="12" fill="none" stroke="{t["green"]}" stroke-opacity=".35"/>')
        else:
            d.add(f'<circle cx="{nx}" cy="{cy}" r="7" fill="{t["bg"]}" stroke="{acc}" stroke-width="2.5"/>')

        sha = hashlib.sha1((e["company"] + e["role"]).encode()).hexdigest()[:7]
        d.add(d.text(104, y0 + 17, sha, "mono", 14, t["amber"]))
        d.add(d.text(184, y0 + 18, e["role"], "display", 24, t["text"], ls=-0.4))
        rw = measure(e["role"], "display", 24, -0.4)
        d.add(d.text(184 + rw + 14, y0 + 18, e["company"], "medium", 19, acc))

        right = W - 48
        if e.get("period"):
            d.add(d.text(right, y0 + 15, e["period"], "mono", 13, t["faint"], anchor="end"))
            right -= measure(e["period"], "mono", 13) + 14
        if e.get("current"):
            lbl = "HEAD · NOW"
            lw = measure(lbl, "mono", 11.5, 1.2) + 24
            d.add(f'<rect x="{a(right-lw)}" y="{y0-3}" width="{a(lw)}" height="26" rx="13" fill="{t["green"]}" '
                  f'fill-opacity=".12" stroke="{t["green"]}" stroke-opacity=".4"/>')
            d.add(d.text(right - lw + 12, y0 + 14.2, lbl, "mono", 11.5, t["green"], ls=1.2))

        for j, ln in enumerate(lines):
            d.add(d.text(184, y0 + 52 + j * 26, ln, "body", 17.5, t["muted"]))
        cx = 184
        chip_y = y0 + 52 + (len(lines) - 1) * 26 + 18
        for tech in e["tech"]:
            w, svg = d.chip(cx, chip_y, tech, acc, size=13, pad=11, h=27)
            d.add(svg)
            cx += w + 8
    return d


# ═══════════════════════════════════════════════════════════════════════
#  TOOLBOX — icons vendored from skill-icons (MIT), inlined so nothing
#  depends on a third-party image server
# ═══════════════════════════════════════════════════════════════════════
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
ICON_META = {
    "ts": ("TypeScript", "TypeScript"), "js": ("JavaScript", "JavaScript"), "python": ("Python", "Python"),
    "java": ("Java", "Java"), "go": ("GoLang", "Go"), "dart": ("Dart", "Dart"), "kotlin": ("Kotlin", "Kotlin"),
    "nodejs": ("NodeJS", "Node.js"), "nestjs": ("NestJS", "NestJS"), "express": ("ExpressJS", "Express"),
    "django": ("Django", "Django"), "spring": ("Spring", "Spring"), "graphql": ("GraphQL", "GraphQL"),
    "react": ("React", "React"), "nextjs": ("NextJS", "Next.js"), "redux": ("Redux", "Redux"),
    "tailwind": ("TailwindCSS", "Tailwind"), "sass": ("Sass", "Sass"), "html": ("HTML", "HTML"),
    "css": ("CSS", "CSS"), "bootstrap": ("Bootstrap", "Bootstrap"), "flutter": ("Flutter", "Flutter"),
    "electron": ("Electron", "Electron"), "firebase": ("Firebase", "Firebase"),
    "postgres": ("PostgreSQL", "PostgreSQL"), "mysql": ("MySQL", "MySQL"), "mongodb": ("MongoDB", "MongoDB"),
    "redis": ("Redis", "Redis"), "docker": ("Docker", "Docker"), "kubernetes": ("Kubernetes", "Kubernetes"),
    "aws": ("AWS", "AWS"), "vercel": ("Vercel", "Vercel"), "linux": ("Linux", "Linux"), "git": ("Git", "Git"),
    "github": ("Github", "GitHub"), "postman": ("Postman", "Postman"), "figma": ("Figma", "Figma"),
}


def inline_icon(id_, theme_name, x, y, size, n):
    import re
    base = ICON_META[id_][0]
    for f in (f"{base}-{theme_name.capitalize()}.svg", f"{base}.svg"):
        path = os.path.join(ICON_DIR, f)
        if os.path.exists(path):
            break
    else:
        raise SystemExit(f"icon not found for '{id_}' — add it to profile/icons/")
    src = open(path, encoding="utf-8").read()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", src.strip(), flags=re.S)
    p = f"ic{n}_"                                  # keep ids unique across icons
    inner = re.sub(r'id="([^"]+)"', lambda m: f'id="{p}{m.group(1)}"', inner)
    inner = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{p}{m.group(1)})", inner)
    inner = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}{m.group(1)}"', inner)
    return f'<svg x="{a(x)}" y="{a(y)}" width="{size}" height="{size}" viewBox="{vb}">{inner}</svg>'


def toolbox(theme):
    t = theme
    W, row_h, top = 1200, 104, 112
    groups = C["toolbox"]
    H = top + row_h * len(groups) + 18
    d = Doc(W, H, t, "Toolbox", "; ".join(
        f'{g["group"]}: {", ".join(ICON_META[i][1] for i in g["items"])}' for g in groups))
    clip = d.clip_card(24)
    d.add(d.card(rx=24))
    d.add(d.orbs([(60, H + 20, 200, "g2", 40, -30, 17), (1180, 60, 180, "g3", -30, 30, 19)], clip))
    d.add(f'<path d="M48 51 l5.5 5 l-5.5 5" stroke="{t["pink"]}" stroke-width="2.2" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(66, 61, [("ls ", t["text"]), ("~/toolbox --group", t["faint"])], "mono", 15))
    d.add(f'<rect x="40" y="84" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')

    n, size, slot, x0 = 0, 46, 96, 262
    for gi, g in enumerate(groups):
        y = top + gi * row_h
        acc = t[ACCENTS[gi % 3]]
        if gi:
            d.add(f'<rect x="48" y="{y - 14}" width="{W-96}" height="1" fill="{t["line"]}" '
                  f'fill-opacity="{t["line_o"] * 0.7}"/>')
        d.add(f'<rect x="48" y="{y + 15}" width="3" height="22" rx="1.5" fill="{acc}"/>')
        d.add(d.text(64, y + 26, g["group"].upper(), "mono", 12.5, t["text"], ls=1.6))
        d.add(d.text(64, y + 44, f'{len(g["items"]):02d} tools', "mono", 11.5, t["faint"]))
        for k, id_ in enumerate(g["items"]):
            cx = x0 + k * slot + slot / 2
            # static on purpose: the toolbox must read even if animations never run
            d.add("<g>" + inline_icon(id_, t["name"], cx - size / 2, y, size, n)
                  + d.text(cx, y + size + 22, ICON_META[id_][1], "mono", 11.5, t["muted"], anchor="middle")
                  + "</g>")
            n += 1
    return d


# ═══════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════
def footer(theme):
    t = theme
    W, H = 1200, 320
    f = C["footer"]
    d = Doc(W, H, t, " ".join(f["headline"]), f["email"])
    clip = d.clip_card(28)
    d.add(d.card(rx=28))
    d.add(d.orbs([(220, 330, 220, "g1", 50, -30, 15), (980, -10, 220, "g3", -60, 40, 18),
                  (600, 360, 140, "g2", 30, -20, 12)], clip))
    d.add(d.dot_grid(clip, 600, 160, 520, 260))
    d.add(d.text(W / 2, 86, f["kicker"].upper(), "mono", 13.5, t["faint"], anchor="middle", ls=2.4))
    d.add(d.text(W / 2, 156, f["headline"][0], "display", 58, t["text"], anchor="middle", ls=-1.8))
    g = d.brand_gradient(d.uid("fg"), 360, 840, dur=6)
    d.add(d.text(W / 2, 222, f["headline"][1], "display", 58, g, anchor="middle", ls=-1.8))

    ew = measure(f["email"], "mono", 17)
    ex = W / 2 - (ew + 26) / 2
    d.add(d.text(ex, 272, f["email"], "mono", 17, t["muted"]))
    d.add(d.arrow_ne(ex + ew + 14, 261, 11, t["pink"], 2))
    ug = d.brand_gradient(d.uid("ug"), ex, ex + ew + 26, dur=4)
    an = d.uid("draw")
    d.css.append(f"@keyframes {an}{{0%{{transform:scaleX(0)}}45%,80%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}"
                 f".{an}{{transform-box:fill-box;transform-origin:left;animation:{an} 5s cubic-bezier(.65,0,.35,1) infinite}}")
    d.add(f'<rect class="{an}" x="{a(ex)}" y="284" width="{a(ew + 26)}" height="2" rx="1" fill="{ug}"/>')
    return d


# ═══════════════════════════════════════════════════════════════════════
#  MOBILE VARIANTS — served to screens under 768px via <picture> media
#  queries, so the art stays readable on a phone instead of shrinking to 5px
# ═══════════════════════════════════════════════════════════════════════
def project_mobile(theme, p, idx):
    t = theme
    W, H = 600, 320
    acc = t[ACCENTS[idx % 3]]
    d = Doc(W, H, t, p["title"], p["description"])
    clip = d.clip_card(30)
    d.add(d.card(rx=30))
    blur = d.uid("cg")
    d.defs.append(f'<filter id="{blur}" x="-60%" y="-60%" width="220%" height="220%">'
                  f'<feGaussianBlur stdDeviation="60"/></filter>')
    d.add(f'<g clip-path="url(#{clip})"><circle cx="{W-40}" cy="-10" r="150" fill="{acc}" '
          f'opacity="{0.34 if t["name"] == "dark" else 0.18}" filter="url(#{blur})"/>'
          f'<rect x="0" y="0" width="{W}" height="6" fill="{d.brand_gradient(d.uid("hl"), 0, W, dur=6 + idx)}"/></g>')
    d.add(d.spans(40, 72, [(f"{idx+1:02d}", acc, "monob"), ("  " + p["category"].upper(), t["faint"])],
                  "mono", 24, ls=1.5))
    rx = W - 40
    if p.get("url"):
        d.add(d.arrow_ne(rx - 26, 48, 26, acc, 4))
        rx -= 50
    if p.get("status") == "live":
        d.add(d.live_dot(rx - 10, 62, t["green"], 8))
    lines = wrap(p["title"], "display", 62, W - 80, 2)
    base = H - 104
    for i, ln in enumerate(lines):
        d.add(d.text(38, base - (len(lines) - 1 - i) * 66, ln, "display", 62, t["text"], ls=-1.6))
    tech = " · ".join(p["tech"][:3])
    while measure(tech, "mono", 23) > W - 96 and " · " in tech:
        tech = tech.rsplit(" · ", 1)[0]
    d.add(d.text(40, H - 44, tech, "mono", 23, t["muted"]))
    return d


def timeline_mobile(theme):
    t = theme
    W, x = 720, 92
    rows, y = [], 132
    for e in C["experience"]:
        lines = wrap(e["summary"], "body", 24, W - x - 40, 3)
        chips, cx, cy = [], x, 0
        for tech in e["tech"]:
            w = measure(tech, "mono", 18) + 32
            if cx + w > W - 40:
                cx, cy = x, cy + 48
            chips.append((cx, cy, tech))
            cx += w + 10
        h = 40 + 38 + (36 if e.get("period") else 0) + len(lines) * 34 + 22 + cy + 40 + 52
        rows.append((e, lines, chips, y, h))
        y += h
    H = int(y)
    d = Doc(W, H, t, "Experience", " → ".join(f'{e["role"]} at {e["company"]}' for e in C["experience"]))
    clip = d.clip_card(32)
    d.add(d.card(rx=32))
    d.add(d.orbs([(700, 40, 220, "g1", -40, 30, 18)], clip))
    d.add(f'<path d="M44 58 l8 7 l-8 7" stroke="{t["pink"]}" stroke-width="3" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(68, 72, [("git log ", t["text"]), ("--graph --career", t["faint"])], "mono", 22))
    d.add(f'<rect x="40" y="100" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')
    nx = 52
    y_first, y_last = rows[0][3] + 14, rows[-1][3] + 14
    rail = d.uid("rail")
    d.defs.append(f'<linearGradient id="{rail}" x1="0" y1="{y_first}" x2="0" y2="{y_last + 90}" '
                  f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{t["g1"]}"/>'
                  f'<stop offset=".6" stop-color="{t["g3"]}"/><stop offset="1" stop-color="{t["g3"]}" stop-opacity="0"/>'
                  f'</linearGradient>')
    d.add(f'<rect x="{nx-1.5}" y="{y_first}" width="3" height="{y_last - y_first + 90}" fill="url(#{rail})"/>')
    for i, (e, lines, chips, y0, h) in enumerate(rows):
        acc = t[ACCENTS[i % 3]]
        cy = y0 + 14
        if e.get("current"):
            d.add(d.live_dot(nx, cy, t["green"], 10))
            d.add(f'<circle cx="{nx}" cy="{cy}" r="17" fill="none" stroke="{t["green"]}" stroke-opacity=".35" stroke-width="1.5"/>')
        else:
            d.add(f'<circle cx="{nx}" cy="{cy}" r="10" fill="{t["bg"]}" stroke="{acc}" stroke-width="3.5"/>')
        d.add(d.text(x, y0 + 26, e["role"], "display", 34, t["text"], ls=-0.6))
        if e.get("current"):
            lbl = "NOW"
            lw = measure(lbl, "mono", 17, 1.5) + 32
            d.add(f'<rect x="{a(W-40-lw)}" y="{y0-6}" width="{a(lw)}" height="38" rx="19" fill="{t["green"]}" '
                  f'fill-opacity=".12" stroke="{t["green"]}" stroke-opacity=".4"/>')
            d.add(d.text(W - 40 - lw + 16, y0 + 19, lbl, "mono", 17, t["green"], ls=1.5))
        d.add(d.text(x, y0 + 66, e["company"], "medium", 25, acc))
        off = 0
        if e.get("period"):
            d.add(d.text(x, y0 + 102, e["period"], "mono", 18, t["faint"]))
            off = 36
        for j, ln in enumerate(lines):
            d.add(d.text(x, y0 + 110 + off + j * 34, ln, "body", 24, t["muted"]))
        base = y0 + 110 + off + (len(lines) - 1) * 34 + 26
        for cx, cy_, tech in chips:
            _, svg = d.chip(cx, base + cy_, tech, acc, size=18, pad=16, h=38)
            d.add(svg)
    return d


def toolbox_mobile(theme):
    t = theme
    W, per, size, slot, x0 = 720, 6, 60, 104, 48
    groups = C["toolbox"]
    y, layout = 136, []
    for g in groups:
        rows = (len(g["items"]) + per - 1) // per
        layout.append((g, y))
        y += 54 + rows * 116 + 30
    H = int(y)
    d = Doc(W, H, t, "Toolbox", "; ".join(
        f'{g["group"]}: {", ".join(ICON_META[i][1] for i in g["items"])}' for g in groups))
    clip = d.clip_card(32)
    d.add(d.card(rx=32))
    d.add(d.orbs([(40, H, 240, "g2", 40, -30, 17), (700, 60, 200, "g3", -30, 30, 19)], clip))
    d.add(f'<path d="M44 58 l8 7 l-8 7" stroke="{t["pink"]}" stroke-width="3" fill="none" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(d.spans(68, 72, [("ls ", t["text"]), ("~/toolbox --group", t["faint"])], "mono", 22))
    d.add(f'<rect x="40" y="100" width="{W-80}" height="1" fill="{t["line"]}" fill-opacity="{t["line_o"]}"/>')
    n = 0
    for gi, (g, gy) in enumerate(layout):
        acc = t[ACCENTS[gi % 3]]
        d.add(f'<rect x="{x0}" y="{gy - 2}" width="4" height="28" rx="2" fill="{acc}"/>')
        d.add(d.spans(x0 + 18, gy + 20, [(g["group"].upper(), t["text"]),
                                          (f'  {len(g["items"]):02d}', t["faint"])], "mono", 18, ls=1.6))
        for k, id_ in enumerate(g["items"]):
            cx = x0 + (k % per) * slot + slot / 2
            iy = gy + 54 + (k // per) * 116
            d.add("<g>" + inline_icon(id_, t["name"], cx - size / 2, iy, size, n)
                  + d.text(cx, iy + size + 30, ICON_META[id_][1], "mono", 15, t["muted"], anchor="middle")
                  + "</g>")
            n += 1
    return d


def footer_mobile(theme):
    t = theme
    W = 720
    f = C["footer"]
    head = wrap(f["headline"][0], "display", 72, 620) + [f["headline"][1]]
    H = 150 + len(head) * 78 + 150
    d = Doc(W, H, t, " ".join(f["headline"]), f["email"])
    clip = d.clip_card(32)
    d.add(d.card(rx=32))
    d.add(d.orbs([(120, H, 240, "g1", 50, -30, 15), (660, 0, 240, "g3", -50, 40, 18)], clip))
    d.add(d.dot_grid(clip, 360, H / 2, 420, 300))
    d.add(d.text(W / 2, 104, f["kicker"].upper(), "mono", 18, t["faint"], anchor="middle", ls=2.4))
    g = d.brand_gradient(d.uid("fg"), 140, 580, dur=6)
    for i, ln in enumerate(head):
        last = i == len(head) - 1
        d.add(d.text(W / 2, 190 + i * 78, ln, "display", 72, g if last else t["text"], anchor="middle", ls=-2.2))
    ey = 190 + (len(head) - 1) * 78 + 92
    ew = measure(f["email"], "mono", 24)
    ex = W / 2 - (ew + 36) / 2
    d.add(d.text(ex, ey, f["email"], "mono", 24, t["muted"]))
    d.add(d.arrow_ne(ex + ew + 20, ey - 16, 16, t["pink"], 3))
    ug = d.brand_gradient(d.uid("ug"), ex, ex + ew + 36, dur=4)
    an = d.uid("draw")
    d.css.append(f"@keyframes {an}{{0%{{transform:scaleX(0)}}45%,80%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}"
                 f".{an}{{transform-box:fill-box;transform-origin:left;animation:{an} 5s cubic-bezier(.65,0,.35,1) infinite}}")
    d.add(f'<rect class="{an}" x="{a(ex)}" y="{ey + 18}" width="{a(ew + 36)}" height="3" rx="1.5" fill="{ug}"/>')
    return d


# ═══════════════════════════════════════════════════════════════════════
#  README sync — rewrites only the block between the projects markers
# ═══════════════════════════════════════════════════════════════════════
MQ_MOBILE = "(max-width: 767px)"
MQ_MOBILE_DARK = "(max-width: 767px) and (prefers-color-scheme: dark)"
MQ_DARK = "(prefers-color-scheme: dark)"


def projects_html():
    from xml.sax.saxutils import quoteattr
    fallback = C["links"]["portfolio"].rstrip("/") + "/#projects"
    cards = []
    for i, p in enumerate(C["projects"], 1):
        alt = quoteattr(f'{p["title"]} — {p["description"]} ({", ".join(p["tech"])})')
        cards.append(
            f'  <a href="{p.get("url") or fallback}"><picture>'
            f'<source media="{MQ_MOBILE_DARK}" srcset="assets/project-{i}-mobile-dark.svg">'
            f'<source media="{MQ_MOBILE}" srcset="assets/project-{i}-mobile-light.svg">'
            f'<source media="{MQ_DARK}" srcset="assets/project-{i}-dark.svg">'
            f'<img alt={alt} src="assets/project-{i}-light.svg" width="49%"></picture></a>')
    rows = ["\n".join(cards[i:i + 2]) for i in range(0, len(cards), 2)]
    return "\n".join(f'<p align="center">\n{r}\n</p>' for r in rows)


def sync_readme():
    path = os.path.join(ROOT, "README.md")
    if not os.path.exists(path):
        return
    start, end = "<!-- projects:start -->", "<!-- projects:end -->"
    s = open(path, encoding="utf-8").read()
    if start in s and end in s:
        head, rest = s.split(start, 1)
        _, tail = rest.split(end, 1)
        new = f"{head}{start}\n{projects_html()}\n{end}{tail}"
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            print("  README.md projects block updated")


def main():
    written = []
    for name, t in THEMES.items():
        written.append(save(hero(t), f"{OUT}/hero-{name}.svg"))
        written.append(save(timeline(t), f"{OUT}/experience-{name}.svg"))
        written.append(save(toolbox(t), f"{OUT}/toolbox-{name}.svg"))
        written.append(save(footer(t), f"{OUT}/footer-{name}.svg"))
        for kind, label, primary in [("portfolio", "Portfolio", True), ("linkedin", "LinkedIn", False),
                                     ("email", "Email", False)]:
            written.append(save(button(t, kind, label, primary), f"{OUT}/btn-{kind}-{name}.svg"))
        for i, p in enumerate(C["projects"]):
            written.append(save(project(t, p, i), f"{OUT}/project-{i+1}-{name}.svg"))
            written.append(save(project_mobile(t, p, i), f"{OUT}/project-{i+1}-mobile-{name}.svg"))
        written.append(save(hero_mobile(t), f"{OUT}/hero-mobile-{name}.svg"))
        written.append(save(timeline_mobile(t), f"{OUT}/experience-mobile-{name}.svg"))
        written.append(save(toolbox_mobile(t), f"{OUT}/toolbox-mobile-{name}.svg"))
        written.append(save(footer_mobile(t), f"{OUT}/footer-mobile-{name}.svg"))
    # remove cards for projects that were deleted from content.json
    for f in os.listdir(OUT):
        if f.startswith("project-") and f not in {os.path.basename(w) for w in written}:
            os.remove(os.path.join(OUT, f))
    for w in written:
        print(f"  {os.path.relpath(w, ROOT):38s} {os.path.getsize(w)/1024:6.1f} KB")
    sync_readme()


if __name__ == "__main__":
    main()
