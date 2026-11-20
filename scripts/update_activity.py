"""Redraws the animated contribution graph on the profile page.

Reads the public contribution calendar for the account (the same squares a
visitor sees) and writes assets/activity-dark.svg and assets/activity-light.svg.
Standard library only. No tokens, no third-party services.

If the calendar is nearly empty (private contributions are not shown on the
profile), nothing is written and the current images stay as they are.
"""
import datetime as dt
import html
import os
import re
import sys
import urllib.request

USER = os.environ.get("PROFILE_USER", "ALZAR3OUNI")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("OUT_DIR", os.path.join(ROOT, "assets"))
MIN_TOTAL = int(os.environ.get("MIN_TOTAL", "50"))
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TRAVEL, LOOP = 42.0, 50.0
MODES = {
    "dark": dict(ink="#F5F7FA", muted="#9AA4B2", head="#FFFFFF", body="#D5DBE3",
                 levels=["rgba(255,255,255,0.06)", "rgba(255,255,255,0.22)", "rgba(255,255,255,0.42)", "rgba(255,255,255,0.66)", "rgba(255,255,255,0.95)"],
                 panel="rgba(255,255,255,0.045)", border="rgba(255,255,255,0.2)", shine="0.12", blobs=("#FFFFFF", "#94A3B8", "#FFFFFF"), blob_op="0.14"),
    "light": dict(ink="#0F172A", muted="#55627A", head="#0F172A", body="#334155",
                  levels=["rgba(15,23,42,0.06)", "rgba(15,23,42,0.2)", "rgba(15,23,42,0.4)", "rgba(15,23,42,0.62)", "rgba(15,23,42,0.9)"],
                  panel="rgba(255,255,255,0.5)", border="rgba(15,23,42,0.14)", shine="0.7", blobs=("#0F172A", "#64748B", "#0F172A"), blob_op="0.07"),
}


def calendar():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"X-Requested-With": "XMLHttpRequest", "User-Agent": "profile-activity-graph"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    cells = re.findall(r'data-date="(\d{4}-\d\d-\d\d)" id="contribution-day-component-\d+-\d+" data-level="(\d)"', page)
    return (int(total.group(1).replace(",", "")) if total else 0), {dt.date.fromisoformat(d): int(lv) for d, lv in cells}


def draw(total, days, m):
    w, h = 1200, 268
    last = max(days)
    start = last - dt.timedelta(days=(last.weekday() + 1) % 7 + 52 * 7)  # a Sunday
    x0, y0, s, g = 96, 112, 15, 4
    n = sum(1 for wk in range(53) for d in range(7) if start + dt.timedelta(days=wk * 7 + d) <= last)
    base, eat, pts, labels, k, last_month = [], [], [], [], 0, None
    for wk in range(53):
        for d in (range(7) if wk % 2 == 0 else range(6, -1, -1)):  # the snake goes down one column, up the next
            day = start + dt.timedelta(days=wk * 7 + d)
            if day > last:
                continue
            x, y = x0 + wk * (s + g), y0 + d * (s + g)
            base.append(f'<rect class="c" style="animation-delay:{wk * 7 / 53:.2f}s" x="{x}" y="{y}" width="{s}" height="{s}" rx="3" fill="{m["levels"][0]}"/>')
            lv = days.get(day, 0)
            if lv:
                eat.append(f'<rect class="c" style="animation-delay:{wk * 7 / 53:.2f}s" x="{x}" y="{y}" width="{s}" height="{s}" rx="3" fill="{m["levels"][lv]}"/>')
            pts.append(f"{x} {y}")
            k += 1
        first = start + dt.timedelta(days=wk * 7)
        if first.month != last_month and first.day <= 7:
            labels.append(f'<text x="{x0 + wk * (s + g)}" y="{y0 - 12}" font-size="13" fill="{m["muted"]}">{MONTHS[first.month - 1]}</text>')
            last_month = first.month
    # a line that sweeps the graph from left to right, with a soft trail behind it
    span, top, tall = 53 * (s + g), y0 - 5, 7 * (s + g) + 6
    fade = '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.92;1" dur="7s" repeatCount="indefinite"/>'
    sweep = (f'<rect x="{x0 - 30}" y="{top}" width="30" height="{tall}" fill="url(#trail)" opacity="0"><animate attributeName="x" values="{x0 - 30};{x0 + span - 30}" dur="7s" repeatCount="indefinite"/>{fade}</rect>'
             f'<rect x="{x0}" y="{top}" width="2.5" height="{tall}" rx="1.25" fill="{m["head"]}" opacity="0"><animate attributeName="x" values="{x0};{x0 + span}" dur="7s" repeatCount="indefinite"/>{fade}</rect>')
    trail = f'<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{m["head"]}" stop-opacity="0"/><stop offset="1" stop-color="{m["head"]}" stop-opacity="0.22"/></linearGradient>'
    weekdays = "".join(f'<text x="52" y="{y0 + d * (s + g) + 12}" font-size="12" fill="{m["muted"]}">{t}</text>' for d, t in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    title = f"{total} contributions in the last year"
    b = m["blobs"]
    blobs = (f'<circle cx="{w * 0.12}" cy="{h * 0.25}" r="{h * 0.55}" fill="{b[0]}"/><circle cx="{w * 0.62}" cy="{h * 0.85}" r="{h * 0.6}" fill="{b[1]}"/>'
             f'<circle cx="{w * 0.93}" cy="{h * 0.2}" r="{h * 0.45}" fill="{b[2]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{html.escape(title)}">'
            f'<defs><filter id="blur" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="46"/></filter>'
            f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="22"/></clipPath>'
            f'<linearGradient id="shine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="{m["shine"]}"/><stop offset="0.45" stop-color="#fff" stop-opacity="0.02"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>{trail}</defs>'
            f'<style>text{{font-family:{FONT}}}'
            '.c{animation:lift 7s ease-out infinite}@keyframes lift{0%{transform:translateY(0)}2.5%{transform:translateY(-7px)}8%{transform:translateY(0)}100%{transform:translateY(0)}}@media (prefers-reduced-motion:reduce){.c{animation:none}}</style>'
            f'<g clip-path="url(#clip)"><g filter="url(#blur)" opacity="{m["blob_op"]}">{blobs}</g>'
            f'<rect width="{w}" height="{h}" fill="{m["panel"]}"/><rect width="{w}" height="{h}" fill="url(#shine)"/></g>'
            f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="22" fill="none" stroke="{m["border"]}" stroke-width="1.5"/>'
            f'<text x="52" y="60" font-size="24" font-weight="700" fill="{m["ink"]}">{title}</text>{"".join(labels)}{weekdays}{"".join(base)}{"".join(eat)}{sweep}</svg>')


if __name__ == "__main__":
    total, days = calendar()
    if total < MIN_TOTAL or not days:
        print(f"Only {total} contributions are public; leaving the current graph as it is.")
        sys.exit(0)
    os.makedirs(OUT, exist_ok=True)
    for mode, m in MODES.items():
        with open(os.path.join(OUT, f"activity-{mode}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(draw(total, days, m))
    print(f"Graph redrawn: {total} contributions.")
