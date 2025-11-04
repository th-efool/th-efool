#!/usr/bin/env python3
import requests, datetime, os, random

TOKEN = os.environ.get("GH_TOKEN")
USERNAME = "th-efool"

API = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {TOKEN}"}

query = """
query($user:String!) {
  user(login:$user) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            weekday
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

res = requests.post(API, json={"query": query, "variables": {"user": USERNAME}}, headers=headers)
data = res.json()

if "errors" in data:
    print(data)
    exit(1)

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# 6-level dracula neon palette
LEVEL_COLORS = [
    "#8be9fd", # Cyan
    "#50fa7b", # Green
    "#ffb86c", # Orange
    "#ff79c6", # Pink
    "#bd93f9", # Purple
    "#ff5555"  # Red
]

# thresholds for each level
THRESHOLDS = [1,2,4,8,12,20]

def color_for(count):
    for i,th in reversed(list(enumerate(THRESHOLDS))):
        if count >= th:
            return LEVEL_COLORS[i]
    return "none"

# --- SVG parameters ---
cell = 12
pad = 3
bg = "#0d1117"  # github background
width = len(weeks) * (cell + pad)
height = 7 * (cell + pad)

svg = [
f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
f'<rect width="100%" height="100%" fill="{bg}" />',
'<style>',
"""
@keyframes flicker {
  0%, 100% { opacity: 1; filter: drop-shadow(0 0 2px currentColor); }
  92% { opacity: 0.75; filter: drop-shadow(0 0 6px currentColor); }
  95% { opacity: 0.4; filter: drop-shadow(0 0 1px currentColor); }
}
""",
'</style>'
]

for x,week in enumerate(weeks):
    for day in week["contributionDays"]:
        count = day["contributionCount"]
        if count == 0:
            continue
        
        c = color_for(count)
        y = day["weekday"] * (cell + pad)

        # random small desync
        delay = round(random.uniform(0,1), 2)

        svg.append(
            f'<rect x="{x*(cell+pad)}" y="{y}" width="{cell}" height="{cell}" fill="{c}" '
            f'style="animation: flicker 2s infinite steps(2,start); animation-delay:{delay}s;" />'
        )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/dracula_pulse.svg","w") as f:
    f.write("\n".join(svg))

print("✅ Generated dist/dracula_pulse.svg")
