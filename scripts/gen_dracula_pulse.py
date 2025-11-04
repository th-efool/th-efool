import os, requests, math, random

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

TH_EFOOL_MASK_BASE = {
    (0,0),(1,0),(2,0),(1,1),(1,2),(1,3),(1,4),
    (4,0),(4,1),(4,2),(4,3),(4,4),(5,2),(6,0),(6,1),(6,2),(6,3),(6,4),
    (8,2),(9,2),(10,2),
    (12,0),(12,1),(12,2),(12,3),(12,4),(13,0),(14,0),(14,1),(14,2),(13,4),(14,4),
    (16,0),(16,1),(16,2),(16,3),(16,4),(17,0),(18,0),(18,1),(18,2),
    (20,1),(20,2),(20,3),(21,0),(21,4),(22,1),(22,2),(22,3),
    (24,1),(24,2),(24,3),(25,0),(25,4),(26,1),(26,2),(26,3),
    (28,0),(28,1),(28,2),(28,3),(28,4),(29,4),(30,4)
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

weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

calendar_width = len(weeks)
mask_width = max(x for x,_ in TH_EFOOL_MASK_BASE) + 1
x_offset = (calendar_width - mask_width) // 2
TH_EFOOL_MASK = {(x + x_offset, y + 1) for (x, y) in TH_EFOOL_MASK_BASE}

CELL, GAP = 14, 3
W = len(weeks) * (CELL + GAP)
H = 7 * (CELL + GAP)

SUBDIV = 2
micro = CELL // SUBDIV
micro_gap = GAP / SUBDIV

def intensity(c):
    for i, th in enumerate(THRESHOLDS):
        if c < th:
            return PALETTE[i-1]
    return PALETTE[-1]

svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">']

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
.noise {
  mix-blend-mode: screen;
  animation:pulse 2s infinite linear;
}
</style>
""")

# -------- Neural noise functions --------

def hash(v):
    v = math.sin(v*12.9898)*43758.5453
    return v - math.floor(v)

def noise2d(x, y):
    i, j = int(x), int(y)
    fx, fy = x - i, y - j
    a = hash(i + j*57)
    b = hash(i+1 + j*57)
    c = hash(i + (j+1)*57)
    d = hash(i+1 + (j+1)*57)
    u = fx*fx*(3-2*fx)
    v = fy*fy*(3-2*fy)
    return (a*(1-u)*(1-v) + b*u*(1-v) + c*(1-u)*v + d*u*v)

# center of mask
cx = (min(x for x,_ in TH_EFOOL_MASK) + max(x for x,_ in TH_EFOOL_MASK)) / 2
cy = (min(y for _,y in TH_EFOOL_MASK) + max(y for _,y in TH_EFOOL_MASK)) / 2

# -------- Draw contribution grid --------
for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        fill = intensity(day["contributionCount"])
        delay = (x * 7 + y) * 0.0113
        is_mask = (x, y) in TH_EFOOL_MASK

        baseX = x*(CELL+GAP)
        baseY = y*(CELL+GAP)

        for i in range(SUBDIV):
            for j in range(SUBDIV):
                px = baseX + i*(micro+micro_gap)
                py = baseY + j*(micro+micro_gap)
                svg.append(
                    f'<rect class="cell" x="{px}" y="{py}" width="{micro}" height="{micro}" '
                    f'fill="{fill}" style="animation-delay:{delay}s"/>'
                )

        if is_mask:
            svg.append(
                f'<rect x="{baseX}" y="{baseY}" width="{CELL}" height="{CELL}" '
                f'fill="none" stroke="white" stroke-width="1.2"/>'
            )

# -------- Neural glow overlay --------
scale = 0.18
falloff = 0.9

for x in range(len(weeks)):
    for y in range(7):
        baseX = x*(CELL+GAP)
        baseY = y*(CELL+GAP)

        # distance from TH-EFOOL field center (grid coords)
        d = math.sqrt((x-cx)**2 + (y-cy)**2)
        mask = math.exp(-d*falloff)

        for i in range(SUBDIV):
            for j in range(SUBDIV):
                px = baseX + i*(micro+micro_gap)
                py = baseY + j*(micro+micro_gap)

                # Perlin noise
                n = noise2d(x*scale + i*0.3, y*scale + j*0.3)
                a = max(0, n * mask * 0.45)  # 0–0.45 opacity

                if a < 0.02: 
                    continue

                svg.append(
                    f'<rect class="noise" x="{px}" y="{py}" width="{micro}" height="{micro}" '
                    f'fill="rgba(255,110,150,{a:.3f})"/>'
                )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg","w") as f:
    f.write("\n".join(svg))

print("✅ SVG generated: dist/heartbeat-dracula.svg")
