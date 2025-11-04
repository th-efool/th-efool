import requests, os, math, datetime
user = os.getenv("GITHUB_REPOSITORY").split("/")[0]
token = os.getenv("GH_TOKEN")

query = """
query($user:String!) {
  user(login:$user) {
    contributionsCollection {
      contributionCalendar {
        colors
        weeks {
          contributionDays {
            contributionCount
          }
        }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"user": user}},
    headers={"Authorization": f"Bearer {token}"}
).json()

weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
grid = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]

maxCommits = max(grid) or 1

cellSize = 12
padding = 2
rows = 7
cols = len(grid) // rows

def cell(x, y, commits):
    intensity = commits / maxCommits
    class_name = f"p{min(int(intensity*4),4)}"
    cx = x * (cellSize + padding)
    cy = y * (cellSize + padding)
    return f'<rect class="{class_name}" x="{cx}" y="{cy}" width="{cellSize}" height="{cellSize}" rx="2"/>'

svg_cells = []
for i, commits in enumerate(grid):
    x = i // rows
    y = i % rows
    svg_cells.append(cell(x, y, commits))

svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{cols*(cellSize+padding)}" height="{rows*(cellSize+padding)}">
<style>
rect {{ fill:#1a0000; transform-origin:center; }}

@keyframes pulse {{
  0% {{ transform:scale(1); fill:#220000; }}
  50% {{ transform:scale(1.35); fill:#a00000; }}
  100% {{ transform:scale(1); fill:#220000; }}
}}

.p0 {{ animation:pulse 4s infinite ease-in-out; opacity:0.2; }}
.p1 {{ animation:pulse 3s infinite ease-in-out; opacity:0.4; }}
.p2 {{ animation:pulse 2s infinite ease-in-out; opacity:0.7; }}
.p3 {{ animation:pulse 1.5s infinite ease-in-out; opacity:0.9; }}
.p4 {{ animation:pulse 1s infinite ease-in-out; opacity:1.0; }}
</style>
{"".join(svg_cells)}
</svg>
"""

os.makedirs("dist", exist_ok=True)
open("dist/heartbeat-grid.svg", "w").write(svg)
