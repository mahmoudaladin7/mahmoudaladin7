"""
svgkit — the tiny design system behind the profile art.

Every SVG in /assets is generated from here so the hero, project cards,
timeline, stats and footer all share one palette, one type scale and one
motion language. Fonts are subset per-file and embedded as base64, so the
images render identically on every OS (GitHub blocks external fonts in SVGs).
"""
from __future__ import annotations

import base64
import io
import os
from collections import defaultdict
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ── Type ────────────────────────────────────────────────────────────────
# key: (css family, weight, file)
FONTS = {
    "body":    ("IN",  400, "inter-400.woff2"),
    "medium":  ("SG",  500, "space-grotesk-500.woff2"),
    "display": ("SG",  700, "space-grotesk-700.woff2"),
    "mono":    ("JBM", 400, "jetbrains-mono-400.woff2"),
    "monob":   ("JBM", 700, "jetbrains-mono-700.woff2"),
}

# ── Color ───────────────────────────────────────────────────────────────
# Brand gradient kept from the original README: violet → pink → blue.
THEMES = {
    "dark": {
        "name": "dark",
        "bg": "#0B0B14", "bg2": "#12121E", "line": "#FFFFFF", "line_o": 0.09,
        "text": "#F5F5FA", "muted": "#A3A5BA", "faint": "#666A80",
        "violet": "#A78BFA", "pink": "#F472B6", "blue": "#60A5FA",
        "cyan": "#22D3EE", "amber": "#FBBF24", "green": "#34D399",
        "g1": "#8B5CF6", "g2": "#EC4899", "g3": "#3B82F6",
        "orb_o": 0.42, "dot_o": 0.08, "chip_o": 0.12, "chip_line_o": 0.34,
        "term": "#0D0D17",
    },
    "light": {
        "name": "light",
        "bg": "#FFFFFF", "bg2": "#F6F5FB", "line": "#1B1638", "line_o": 0.11,
        "text": "#0F0E1A", "muted": "#545669", "faint": "#9597AA",
        "violet": "#7C3AED", "pink": "#DB2777", "blue": "#2563EB",
        "cyan": "#0891B2", "amber": "#D97706", "green": "#059669",
        "g1": "#7C3AED", "g2": "#DB2777", "g3": "#2563EB",
        "orb_o": 0.16, "dot_o": 0.09, "chip_o": 0.08, "chip_line_o": 0.28,
        "term": "#0D0D17",
    },
}

ACCENTS = ["violet", "pink", "blue", "cyan", "amber", "green"]

# ── Metrics (for wrapping + chip sizing) ───────────────────────────────
_metrics_cache: dict[str, tuple[dict, int, dict]] = {}


def _font(key):
    if key not in _metrics_cache:
        fam, w, file = FONTS[key]
        f = TTFont(os.path.join(FONT_DIR, file))
        _metrics_cache[key] = (f["hmtx"].metrics, f["head"].unitsPerEm, f.getBestCmap())
    return _metrics_cache[key]


def measure(s: str, key: str, size: float, ls: float = 0.0) -> float:
    hmtx, upm, cmap = _font(key)
    total = 0
    for ch in s:
        g = cmap.get(ord(ch))
        total += hmtx[g][0] if g else upm * 0.5
    return total * size / upm + ls * max(len(s) - 1, 0)


def wrap(s: str, key: str, size: float, width: float, max_lines: int = 99) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if measure(trial, key, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while measure(lines[-1] + "…", key, size) > width and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def a(v):
    """Format a number for SVG attributes."""
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


# ── Document ────────────────────────────────────────────────────────────
class Doc:
    def __init__(self, w: int, h: int, theme: dict, title: str, desc: str = ""):
        self.w, self.h, self.t = w, h, theme
        self.title, self.desc = title, desc
        self.defs: list[str] = []
        self.css: list[str] = []
        self.body: list[str] = []
        self.used: dict[str, set] = defaultdict(set)
        self._id = 0

    def uid(self, p="i"):
        self._id += 1
        return f"{p}{self._id}"

    def add(self, s: str):
        self.body.append(s)

    # Text with automatic font tracking ------------------------------------
    def text(self, x, y, s, key="body", size=16, fill=None, anchor="start",
             ls=0, cls=None, opacity=None, extra=""):
        self.used[key].update(s)
        fam, wt, _ = FONTS[key]
        attrs = [f'x="{a(x)}"', f'y="{a(y)}"', f'font-family="{fam}"',
                 f'font-weight="{wt}"', f'font-size="{a(size)}"',
                 f'fill="{fill or self.t["text"]}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if ls:
            attrs.append(f'letter-spacing="{a(ls)}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if opacity is not None:
            attrs.append(f'opacity="{a(opacity)}"')
        if extra:
            attrs.append(extra)
        return f'<text {" ".join(attrs)}>{escape(s)}</text>'

    def spans(self, x, y, parts, key="mono", size=15, anchor="start", ls=0, cls=None):
        """parts: list of (string, fill[, fontkey])"""
        fam, wt, _ = FONTS[key]
        inner = []
        for p in parts:
            s, fill = p[0], p[1]
            k = p[2] if len(p) > 2 else key
            self.used[k].update(s)
            f2, w2, _ = FONTS[k]
            extra = f' font-family="{f2}" font-weight="{w2}"' if k != key else ""
            inner.append(f'<tspan fill="{fill}"{extra}>{escape(s)}</tspan>')
        c = f' class="{cls}"' if cls else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{a(ls)}"' if ls else ""
        return (f'<text x="{a(x)}" y="{a(y)}" font-family="{fam}" font-weight="{wt}" '
                f'font-size="{a(size)}"{an}{l}{c} xml:space="preserve">{"".join(inner)}</text>')

    # Shared visual primitives ---------------------------------------------
    def brand_gradient(self, gid, x1=0, x2=600, animate=True, dur=6, y=0):
        t = self.t
        anim = (f'<animateTransform attributeName="gradientTransform" type="translate" '
                f'from="0 0" to="{x2 - x1} 0" dur="{dur}s" repeatCount="indefinite"/>') if animate else ""
        self.defs.append(
            f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y}" '
            f'x2="{x2}" y2="{y}" spreadMethod="repeat">'
            f'<stop offset="0" stop-color="{t["g1"]}"/><stop offset=".33" stop-color="{t["g2"]}"/>'
            f'<stop offset=".66" stop-color="{t["g3"]}"/><stop offset="1" stop-color="{t["g1"]}"/>'
            f'{anim}</linearGradient>')
        return f"url(#{gid})"

    def card(self, x=0.5, y=0.5, w=None, h=None, rx=24, fill=None):
        t = self.t
        w = w if w is not None else self.w - 1
        h = h if h is not None else self.h - 1
        return (f'<rect x="{a(x)}" y="{a(y)}" width="{a(w)}" height="{a(h)}" rx="{rx}" '
                f'fill="{fill or t["bg"]}" stroke="{t["line"]}" stroke-opacity="{t["line_o"]}"/>')

    def orbs(self, specs, clip_id):
        """specs: list of (cx, cy, r, color_key, drift_x, drift_y, dur)"""
        t = self.t
        fid = self.uid("blur")
        self.defs.append(f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">'
                         f'<feGaussianBlur stdDeviation="70"/></filter>')
        out = [f'<g clip-path="url(#{clip_id})">']
        for i, (cx, cy, r, ck, dx, dy, dur) in enumerate(specs):
            an = self.uid("drift")
            self.css.append(
                f"@keyframes {an}{{0%{{transform:translate(0,0)}}50%{{transform:translate({dx}px,{dy}px)}}"
                f"100%{{transform:translate(0,0)}}}}"
                f".{an}{{animation:{an} {dur}s ease-in-out infinite}}")
            out.append(f'<g class="{an}"><circle cx="{cx}" cy="{cy}" r="{r}" fill="{t[ck]}" '
                       f'opacity="{t["orb_o"]}" filter="url(#{fid})"/></g>')
        out.append("</g>")
        return "".join(out)

    def dot_grid(self, clip_id, cx, cy, rx, ry, step=24):
        t = self.t
        pid, mid, gid = self.uid("dots"), self.uid("mask"), self.uid("fade")
        self.defs.append(
            f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{step/2}" cy="{step/2}" r="1.1" fill="{t["text"]}" opacity="{t["dot_o"]}"/></pattern>'
            f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{max(rx, ry)}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="{mid}"><rect width="{self.w}" height="{self.h}" fill="url(#{gid})"/></mask>')
        return (f'<g clip-path="url(#{clip_id})" mask="url(#{mid})">'
                f'<rect width="{self.w}" height="{self.h}" fill="url(#{pid})"/></g>')

    def clip_card(self, rx=24):
        cid = self.uid("clip")
        self.defs.append(f'<clipPath id="{cid}"><rect x="0.5" y="0.5" width="{self.w-1}" '
                         f'height="{self.h-1}" rx="{rx}"/></clipPath>')
        return cid

    def chip(self, x, y, label, color, size=13, pad=12, h=28, key="mono"):
        t = self.t
        w = measure(label, key, size) + pad * 2
        return w, (f'<g><rect x="{a(x)}" y="{a(y)}" width="{a(w)}" height="{h}" rx="{h/2}" '
                   f'fill="{color}" fill-opacity="{t["chip_o"]}" stroke="{color}" '
                   f'stroke-opacity="{t["chip_line_o"]}"/>'
                   + self.text(x + pad, y + h / 2 + size * 0.36, label, key, size, color) + "</g>")

    def live_dot(self, cx, cy, color, r=4.5):
        an = self.uid("ping")
        self.css.append(
            f"@keyframes {an}{{0%{{transform:scale(1);opacity:.55}}80%,100%{{transform:scale(3.2);opacity:0}}}}"
            f".{an}{{transform-box:fill-box;transform-origin:center;animation:{an} 2s cubic-bezier(0,0,.2,1) infinite}}")
        return (f'<circle class="{an}" cx="{a(cx)}" cy="{a(cy)}" r="{r}" fill="{color}"/>'
                f'<circle cx="{a(cx)}" cy="{a(cy)}" r="{r}" fill="{color}"/>')

    def arrow_ne(self, x, y, size, color, sw=2.2):
        """↗ drawn as a path (the glyph isn't in the Latin font subset)."""
        s = size
        return (f'<path d="M{a(x)} {a(y+s)} L{a(x+s)} {a(y)} M{a(x+s*0.28)} {a(y)} L{a(x+s)} {a(y)} '
                f'L{a(x+s)} {a(y+s*0.72)}" fill="none" stroke="{color}" stroke-width="{sw}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')

    # Render ------------------------------------------------------------------
    def _font_faces(self) -> str:
        faces = []
        for key, chars in self.used.items():
            if not chars:
                continue
            fam, wt, file = FONTS[key]
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga", "calt"]
            opts.name_IDs = []
            opts.notdef_outline = True
            font = TTFont(os.path.join(FONT_DIR, file), recalcTimestamp=False)
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(chars)) + " ")
            sub.subset(font)
            buf = io.BytesIO()
            font.flavor = "woff2"
            font.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            faces.append(f"@font-face{{font-family:{fam};font-weight:{wt};"
                         f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        return "".join(faces)

    def render(self) -> str:
        reduce = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        css = self._font_faces() + "".join(self.css) + reduce
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc" fill="none">'
            f'<title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.desc)}</desc>'
            f'<style>{css}</style><defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>'
        )


def save(doc: Doc, path: str):
    from xml.dom import minidom
    svg = doc.render()
    minidom.parseString(svg.encode("utf-8"))      # fail loudly on malformed XML
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
