#!/usr/bin/env python3
import os, requests, math

GITHUB_USER = "th-efool"

PALETTE = [
    "#0d1117",
    "rgba(255,110,150,0.15)",
    "rgba(255,110,150,0.22)",
    "rgba(255,110,150,0.35)",
    "rgba(255,110,150,0.55)",
    "rgba(255,110,150,0.75)",
    "#ff6e96",
]
THRESHOLDS = [0,1,2,4,8,12,20]

# === Roboto-inspired 7px high bitmap font ===
letters = {
"t":[
"###..",
".#...",
".#...",
".#...",
".#...",
".#...",
"....."
],
"h":[
"#....",
"#....",
"####.",
"#..#.",
"#..#.",
"#..#.",
"....."
],
"-":[
".....",
".....",
".###.",
".....",
".....",
".....",
"....."
],
"e":[
".###.",
"#...#",
"#####",
"#....",
"#....",
".###.",
"....."
],
"f":[
".###.",
".#...",
"####.",
".#...",
".#...",
".#...",
"....."
],
"o":[
".###.",
"#...#",
"#...#",
"#...#",
"#...#",
".###.",
"....."
],
"l":[
"#....",
"#....",
"#....",
"#....",
"#....",
"####.",
"....."
]
}

text = "th-e fool"

# Build raw pixel mask coordinates (local space)
mask_pixels = []
cursor = 0
for ch in text:
    glyph = letters[ch]
    for y, row in enumerate(glyph):
        for x, c in enumerate(row):
            if c == "#":
                mask_pixels.append((cursor + x, y))
    cursor += len(glyph[0]) + 1  # 1px gap between letters

# GitHub GraphQL query
query = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
          }
        }
      }
    }
  }
}
"""

token = os.getenv("GITHUB_TOKEN")
if not token:
    raise SystemExit("Missing GITHUB_TOKEN")

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": GITHUB_USER}},
    headers={"Authorization": f"bearer {token}"}
).json()

weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# === Center the mask across the calendar ===
week_count = len(weeks)
mask_width = max([p[0] for p in mask_pixels]) + 1
mask_start = max(0, (week_count - mask_width) // 2)

TH_EFOOL_MASK = {(mask_start+x, y) for (x, y) in mask_pixels}

CELL, GAP = 14, 3
W = week_count * (CELL+GAP)
H = 7 * (CELL+GAP)

def intensity(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th: return PALETTE[i-1]
    return PALETTE[-1]

svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'fill="none" xmlns="http://www.w3.org/2000/svg">']

svg.append("""
<style>
@keyframes pulse {
  0%,100% { opacity:1; filter:drop-shadow(0 0 2px currentColor); }
  92% { opacity:.85; filter:drop-shadow(0 0 5px currentColor); }
  96% { opacity:.45; filter:drop-shadow(0 0 1px currentColor); }
}
.cell {
  shape-rendering:crispEdges;
  animation:pulse 2s infinite linear;
}
</style>
""")

for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        c = day["contributionCount"]
        fill = intensity(c)
        delay = (x*7+y)*0.0113

        stroke = 'stroke="white" stroke-width="1.2"' \
            if (x, y) in TH_EFOOL_MASK else ""

        svg.append(
            f'<rect class="cell" x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" '
            f'width="{CELL}" height="{CELL}" fill="{fill}" {stroke} '
            f'style="animation-delay:{delay}s"/>'
        )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/dracula-grid.svg","w") as f:
    f.write("\n".join(svg))

print("✅ SVG generated: dist/dracula-grid.svg (Roboto centered SIG)")
