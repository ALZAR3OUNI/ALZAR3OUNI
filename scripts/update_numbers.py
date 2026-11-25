"""Refresh the live numbers inside the profile cards (hero.svg, signal.svg).

The cards are drawn once on my machine. Each number sits between two comment
markers, for example <!--total-->841<!--/total-->, so this script only swaps the
digits. It reads the same public contribution calendar as update_activity.py.
No tokens, no third-party services.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from update_activity import MIN_TOTAL, calendar  # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), "assets")


def main():
    total, days = calendar()
    if total < MIN_TOTAL or not days:
        print(f"Only {total} contributions are public; leaving the cards as they are.")
        return
    ordered = sorted(days)
    active = sum(1 for d in ordered if days[d] > 0)
    best = cur = 0
    for d in ordered:
        cur = cur + 1 if days[d] > 0 else 0
        best = max(best, cur)
    values = {"total": f"{total:,}", "active": str(active), "streak": str(best)}
    for name in ("hero.svg", "signal.svg"):
        path = os.path.join(ASSETS, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        new = svg
        for key, val in values.items():
            new = re.sub(rf"<!--{key}-->.*?<!--/{key}-->", f"<!--{key}-->{val}<!--/{key}-->", new)
        if new != svg:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
            print(f"{name}: updated ({values})")


if __name__ == "__main__":
    main()
