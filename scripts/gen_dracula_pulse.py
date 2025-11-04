#!/usr/bin/env python3
import os, requests, random

GITHUB_USER = "th-efool"

# Dracula palette — your choices preserved
DRACULA_PALETTE = [
    "#0d1117",
    "rgba(255, 110, 150, 0.15)",
    "rgba(255, 110, 150, 0.22)",
    "rgba(255, 110, 150, 0.35)",
    "rgba(255, 110, 150, 0.55)",
    "rgba(255, 110, 150, 0.75)",
    "#ff6e96"
]

THRESHOLDS = [0,1,2,4,8,12,20]

# ── Signature bitmap (7 rows, columns = characters)
# '#' = draw stroke; space = ignore
# Text: "th-e fool"
SIGNATURE = [
"####  #   ####        ###    #### ",
"#     #   #           #  #   #    ",
"###   #   ####   ##   ###    ###  ",
"#     #   #      ##   #  #   #    ",
"#     ########        #  #   #### ",
]

# Build overlay pixel coordinates
signature_pixels = set()
for row, line in enumerate(SIGNATURE):
    for col, ch in enumerate(line):
        if ch == "#":
            signature_pixels.add((col, row))  # (x, y) in text grid

# GraphQL query
query = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
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
    raise SystemExit("❌ Missing GITHUB_TOKEN")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"bearer {token}"
}

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": GITHUB_USER}},
    headers=headers
)
data = resp.json()
if "errors" in data:
    print(data)
    exit(1)

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

def palette_for(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th:
            return DRACULA_PALETTE[i-1]
    return DRACULA_PALETTE[-1]

CELL, GAP = 14, 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

svg = []
svg.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http:\/\/www.w3.org/2000/svg">')

svg.append("""
<style>
@keyframes neonFlicker {
  0%, 100% { opacity: 1; filter: drop-shadow(0 0 2px currentColor); }
  92% { opacity: 0.8; filter: drop-shadow(0 0 6px currentColor); }
  95% { opacity: 0.4; filter: drop-shadow(0 0 1px currentColor); }
}
.rect {
  shape-rendering: crispEdges;
  animation: neonFlicker 1.85s infinite linear;
}
</style>
""")

for w_idx, week in enumerate(weeks):
    for day in week["contributionDays"]:
        d_idx = day["weekday"]
        count = day["contributionCount"]
        base_color = palette_for(count)

        # tiny random flicker only on text pixels to feel alive
        is_text = (w_idx, d_idx) in signature_pixels
        color = base_color
        if is_text and random.random() < 0.10:
            color = DRACULA_PALETTE[-1]

        delay = (w_idx*7 + d_idx) * 0.012

        x = w_idx * (CELL + GAP)
        y = d_idx * (CELL + GAP)

        if is_text:
            svg.append(
                f'<rect class="rect" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{color}" stroke="#ffffff" stroke-width="1.5" '
                f'style="animation-delay:{delay}s" />'
            )
        else:
            svg.append(
                f'<rect class="rect" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{color}" style="animation-delay:{delay}s" />'
            )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg", "w") as f:
    f.write("\n".join(svg))

print("✅ Generated with neon flicker + signature")
