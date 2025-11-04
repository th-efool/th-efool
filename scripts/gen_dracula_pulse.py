import os, requests

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

# Roboto-ish TH-EFOOL mask (grid coords)
TH_EFOOL_MASK_BASE = {
    # T
    (0,0),(1,0),(2,0),
    (1,1),(1,2),(1,3),(1,4),

    # H
    (4,0),(4,1),(4,2),(4,3),(4,4),
    (5,2),
    (6,0),(6,1),(6,2),(6,3),(6,4),

    # -
    (8,2),(9,2),(10,2),

    # E
    (12,0),(12,1),(12,2),(12,3),(12,4),
    (13,0),
    (14,0),(14,1),(14,2),
    (13,4),(14,4),

    # F
    (16,0),(16,1),(16,2),(16,3),(16,4),
    (17,0),
    (18,0),(18,1),(18,2),

    # O
    (20,1),(20,2),(20,3),
    (21,0),(21,4),
    (22,1),(22,2),(22,3),

    # O
    (24,1),(24,2),(24,3),
    (25,0),(25,4),
    (26,1),(26,2),(26,3),

    # L
    (28,0),(28,1),(28,2),(28,3),(28,4),
    (29,4),(30,4)
}

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

try:
    weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
except Exception as e:
    print("❌ GitHub API error\n", resp)
    raise

calendar_width = len(weeks)
mask_width = max(x for x,_ in TH_EFOOL_MASK_BASE) + 1
x_offset = (calendar_width - mask_width) // 2

# final mask: centered + shifted down by 1 row
TH_EFOOL_MASK = {(x + x_offset, y + 1) for (x, y) in TH_EFOOL_MASK_BASE}

CELL, GAP = 14, 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

def intensity(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th:
            return PALETTE[i-1]
    return PALETTE[-1]

svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'fill="none" xmlns="http://www.w3.org/2000/svg">']

svg.append("""
<style>
@keyframes spark {
  0%   { opacity: .85; filter: drop-shadow(0 0 1px currentColor); }
  6%   { opacity: 1; filter: drop-shadow(0 0 8px currentColor); }
  15%  { opacity: .45; filter: drop-shadow(0 0 3px currentColor); }
  28%  { opacity: .95; filter: drop-shadow(0 0 6px currentColor); }
  40%  { opacity: .55; filter: drop-shadow(0 0 1px currentColor); }
  100% { opacity: .82; filter: drop-shadow(0 0 2px currentColor); }
}

@keyframes ripple {
  0%   { opacity: .95; }
  60%  { opacity: .45; }
  100% { opacity: .90; }
}

.cell {
  shape-rendering: crispEdges;
  animation: ripple 3.5s infinite cubic-bezier(.4,0,.2,1);
}

.maskCell {
  shape-rendering: crispEdges;
  animation: spark 1.8s infinite ease-in-out;
  stroke: white;
  stroke-width: 1.2;
}
</style>
""")

for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        c = day["contributionCount"]
        fill = intensity(c)
        delay = (x * 7 + y) * 0.0113

        css_class = "maskCell" if (x, y) in TH_EFOOL_MASK else "cell"

        svg.append(
            f'<rect class="{css_class}" '
            f'x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" '
            f'width="{CELL}" height="{CELL}" '
            f'fill="{fill}" '
            f'style="animation-delay:{delay}s"/>'
        )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg","w") as f:
    f.write("\n".join(svg))

print("✅ SVG generated: dist/heartbeat-dracula.svg")
