#!/usr/bin/env python3
import os, requests, math

GITHUB_USER = "th-efool"

# Dracula intensity palette (low → high)
# 0 commit uses background tone internally
DRACULA_PALETTE = [
    "#6272a4", # 0 commits - bg visible
    "#8be9fd", # 1+ Cyan
    "#50fa7b", # 2+ Green
    "#ffb86c", # 4+ Orange
    "#ff79c6", # 8+ Pink
    "#bd93f9", # 12+ Purple
    "#ff5555"  # 20+ Red
]

# commit thresholds matching palette indexes
THRESHOLDS = [0,1,2,4,8,12,20]

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
days = [d for w in weeks for d in w["contributionDays"]]

CELL, GAP = 14, 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

def color_for(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th: return DRACULA_PALETTE[i-1]
    return DRACULA_PALETTE[-1]

svg = []
svg.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">')

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

for x, w in enumerate(weeks):
    for y, d in enumerate(w["contributionDays"]):
        c = d["contributionCount"]
        color = color_for(c)

        # desync but very subtle — NOT wavey
        delay = (x*7 + y) * 0.012  

        svg.append(
            f'<rect class="rect" x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" '
            f'width="{CELL}" height="{CELL}" fill="{color}" '
            f'style="animation-delay:{delay}s" />'
        )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg", "w") as f:
    f.write("\n".join(svg))

print("✅ Dracula Pulse grid alive from start — cyan→red done")
