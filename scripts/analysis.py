#!/usr/bin/env python3
"""Spending analysis for Up Banking — generates reports and HTML widgets."""

import json
import os
import sys
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta


def _fetch(endpoint):
    """Run up_client.py with --json and return parsed data."""
    script = os.environ.get(
        "UP_CLIENT_SCRIPT",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "up_client.py"),
    )
    r = subprocess.run(
        [sys.executable, script] + endpoint.split(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        print("error: " + r.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    if not r.stdout.strip():
        return []
    return json.loads(r.stdout)


def _parse_amount(val):
    return float(val) if val else 0.0


def cmd_summary(days=30):
    """Top spending categories and totals over the last N days."""
    data = _fetch("transactions --page-size 100 --json")
    cutoff = datetime.now().astimezone() - timedelta(days=days)
    categories = defaultdict(lambda: {"count": 0, "total": 0.0})
    total_in = 0.0
    total_out = 0.0

    for tx in data:
        a = tx["attributes"]
        if a["status"] != "SETTLED":
            continue
        dt_str = a.get("settledAt") or a.get("createdAt", "")
        if not dt_str:
            continue
        try:
            dt = datetime.fromisoformat(dt_str)
        except ValueError:
            continue
        if dt < cutoff:
            continue

        amt = _parse_amount(a["amount"]["value"])
        cat_rel = tx.get("relationships", {}).get("category", {}).get("data", {})
        cat_id = cat_rel.get("id", "uncategorised") if cat_rel else "uncategorised"

        if amt < 0:
            total_out += abs(amt)
            categories[cat_id]["count"] += 1
            categories[cat_id]["total"] += abs(amt)
        else:
            total_in += amt

    sorted_cats = sorted(categories.items(), key=lambda x: -x[1]["total"])

    print("--- Spending Summary (last {} days) ---".format(days))
    print("  Total in:  ${:.2f}".format(total_in))
    print("  Total out: ${:.2f}".format(total_out))
    print("  Net:       ${:.2f}".format(total_in - total_out))
    print()
    print("  Top categories by spending:")
    for cat_id, stats in sorted_cats[:10]:
        pct = (stats["total"] / total_out * 100) if total_out else 0
        print("    {:30s}  ${:>8.2f}  ({:5.1f}%)  {}tx".format(
            cat_id, stats["total"], pct, stats["count"]))


def cmd_widget(days=30):
    """Generate an HTML spending breakdown widget for ::preview."""
    data = _fetch("transactions --page-size 100 --json")
    cutoff = datetime.now().astimezone() - timedelta(days=days)
    categories = defaultdict(float)
    total_out = 0.0

    for tx in data:
        a = tx["attributes"]
        if a["status"] != "SETTLED":
            continue
        dt_str = a.get("settledAt") or a.get("createdAt", "")
        if not dt_str:
            continue
        try:
            dt = datetime.fromisoformat(dt_str)
        except ValueError:
            continue
        if dt < cutoff:
            continue
        amt = _parse_amount(a["amount"]["value"])
        desc = a["description"] or "Unknown"
        if amt < 0:
            total_out += abs(amt)
            categories[desc] += abs(amt)

    sorted_cats = sorted(categories.items(), key=lambda x: -x[1])[:8]
    others = total_out - sum(v for _, v in sorted_cats)
    if others > 0:
        sorted_cats.append(("Everything else", others))

    bars_html = ""
    colors = [
        "#e06c75", "#61afef", "#98c379", "#e5c07b",
        "#c678dd", "#56b6c2", "#d19a66", "#be5046", "#528bff",
    ]
    for i, (name, amt) in enumerate(sorted_cats):
        pct = (amt / total_out * 100) if total_out else 0
        color = colors[i % len(colors)]
        bars_html += (
            '<div style="margin:6px 0">'
            '<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:2px">'
            '<span style="color:var(--muted-foreground)">' + name + "</span>"
            "<span>$" + "{:.2f}".format(amt) + ' <span style="color:var(--muted-foreground)">'
            "(" + "{:.0f}".format(pct) + "%)</span></span></div>"
            '<div style="height:8px;background:var(--border);border-radius:4px;overflow:hidden">'
            '<div style="width:' + "{:.0f}".format(pct) + "%;height:100%;background:"
            + color + ';border-radius:4px"></div></div></div>'
        )

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        '<body style="font-family:system-ui,sans-serif;color:var(--foreground);margin:0">'
        "<h3 style=\"margin:0 0 4px 0;font-weight:600\">Spending Breakdown</h3>"
        '<p style="margin:0 0 12px 0;font-size:13px;color:var(--muted-foreground)">'
        "Last {} days — total ".format(days)
        + "<strong>${:.2f}</strong> spent</p>".format(total_out)
        + bars_html
        + "</body></html>"
    )

    path = os.path.join(tempfile.gettempdir(), "up-spending.html")
    with open(path, "w") as f:
        f.write(html)
    print("::preview{file=\"" + path.replace("\\", "/") + "}")
    print("Widget written to " + path, file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: analysis.py <summary|widget> [--days N]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    days = 30
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days = max(1, int(sys.argv[idx + 1]))
            except ValueError:
                pass

    if cmd == "summary":
        cmd_summary(days)
    elif cmd == "widget":
        cmd_widget(days)
    else:
        print("error: unknown command '{}'".format(cmd), file=sys.stderr)
        sys.exit(1)