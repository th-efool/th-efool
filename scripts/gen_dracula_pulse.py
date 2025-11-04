#!/usr/bin/env python3
import os, requests, math

GITHUB_USER = "th-efool"

PALETTE = [
    "#282A36", # 0 commits (visible, dark)
    "#44475A", # low
    "#6272A4", # medium
    "#BD93F9", # high
    "#FF79C6"  # peak neon
]

query = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
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

token = os.getenv("GITHUB_TOKEN")
if not token:
    raise SystemExit("❌ Missing GITHUB_TOKEN env")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"bearer {token}"
}

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": GITHUB_USER}},
    headers=headers
)

if resp.status_code != 200:
    raise SystemExit(f"❌ GitHub API error: {resp.text}")

weeks = resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = [d for w in weeks for d in w["contributionDays"]]

max_commit = max(d["contributionCount"] for d in days) or 1

CELL, GAP = 14, 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

svg = []
svg.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">')

svg.append("""
<style>
@keyframes glowPulse {
  0%   { filter: drop-shadow(0 0 0px #BD93F9); }
  50%  { filter: drop-shadow(0 0 5px #FF79C6); }
  100% { filter: drop-shadow(0 0 0px #BD93F9); }
}

@keyframes flicker {
  0%, 18%, 20%, 48%, 50%, 100% { opacity: 1; }
  19%, 49% { opacity: 0.55; }
}

.rect {
  shape-rendering: crispEdges;
}
</style>
""")

for x, w in enumerate(weeks):
    for y, d in enumerate(w["contributionDays"]):
        c = d["contributionCount"]
        intensity = c / max_commit
        idx = min(4, max(0, int(intensity * 4)))
        color = PALETTE[idx]

        anim = ""
        if c > 0:
            delay = (x * 7 + y) * 0.07
            anim = f' style="animation: glowPulse 2s ease-in-out infinite {delay}s, flicker 2s infinite {delay}s"'

        svg.append(
            f'<rect x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" width="{CELL}" height="{CELL}" '
            f'fill="{color}" class="rect"{anim}/>'
        )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg", "w") as f:
    f.write("\n".join(svg))

print("✅ Generated dist/heartbeat-dracula.svg")
