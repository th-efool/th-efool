#!/usr/bin/env python3
import os, requests, datetime, math

GITHUB_USER = "th-efool"

# Dracula-ish colors for contribution intensity
PALETTE = [
    "#282A36", # empty (still visible)
    "#44475A", # low
    "#6272A4", # mid
    "#BD93F9", # high
    "#FF79C6"  # peak glow base
]

# --- Fetch contributions via GraphQL --- #
query = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

headers = {
    "Content-Type": "application/json",
    "Authorization": f"bearer {os.getenv('GITHUB_TOKEN')}"
}

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": GITHUB_USER}},
    headers=headers
)
if resp.status_code != 200:
    raise SystemExit(f"GitHub API error: {resp.text}")

weeks = resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = [d for w in weeks for d in w["contributionDays"]]

max_commit = max(d["contributionCount"] for d in days) or 1

# SVG config
CELL = 14  # px
GAP = 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

svg = []
svg.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">')
svg.append("""<style>
@keyframes glowPulse {
  0% { filter: drop-shadow(0 0 0px #FF79C6); }
  50% { filter: drop-shadow(0 0 4px #FF79C6); }
  100% { filter: drop-shadow(0 0 0px #FF79C6); }
}
@keyframes flicker {
  0%, 19%, 21%, 50%, 52%, 100% { opacity: 1; }
  20%, 51% { opacity: 0.6; }
}
.rect {
  shape-rendering: crispEdges;
}
</style>""")

# Draw cells
for x, w in enumerate(weeks):
    for y, d in enumerate(w["contributionDays"]):
        c = d["contributionCount"]
        intensity = c / max_commit

        # map to palette index (0-4)
        idx = min(4, max(0, int(intensity * 4)))

        color = PALETTE[idx]

        # animation only if > 0 contributions
        anim = ""
        if c > 0:
            # desync by day index
            delay = (x * 7 + y) * 0.05
            anim = f' style="animation: glowPulse 2s ease-in-out infinite {delay}s, flicker 2s infinite {delay}s"'

        # visible even for zero commits (just darkest square)
        svg.append(f'<rect class="rect" x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" width="{CELL}" height="{CELL}" '
                   f'fill="{color}"{anim}/>')


svg.append("</svg>")

with open("heartbeat-dracula.svg", "w") as f:
    f.write("\n".join(svg))

print("✅ Generated heartbeat-dracula.svg with REAL GitHub data")
