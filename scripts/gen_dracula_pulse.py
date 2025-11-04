import os, requests, cmath

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

# TH-EFOOL mask
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

# GraphQL query
query = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date weekday contributionCount
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
    headers={"Authorization": f"bearer ${token}"}
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
micro = CELL / SUBDIV
micro_gap = 0

def intensity(v):
    for i, th in enumerate(THRESHOLDS):
        if v < th:
            return PALETTE[i-1]
    return PALETTE[-1]

# Julia settings
C = complex(-0.7, 0.27015)
MAX_IT = 18
J_COLOR = "#79dafa"

def julia_val(nx, ny):
    # remap pixel -> complex plane, centered
    z = complex((nx - 0.5)*2.2, (ny - 0.5)*2.2)
    for k in range(MAX_IT):
        z = z*z + C
        if abs(z) > 2:
            return k / MAX_IT
    return 1

svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">']

# CSS
svg.append("""
<style>
svg { shape-rendering:crispEdges; }
@keyframes pulse {
  0%,100% { opacity:1; filter:drop-shadow(0 0 2px currentColor); }
  92% { opacity:.85; filter:drop-shadow(0 0 5px currentColor); }
  96% { opacity:.45; filter:drop-shadow(0 0 1px currentColor); }
}
@keyframes juliaBreath {
  0%,100% { opacity: .10 }
  50% { opacity: .32 }
}
.cell {
  animation:pulse 2s infinite linear;
}
.jl {
  mix-blend-mode:screen;
  animation:juliaBreath 5.5s ease-in-out infinite;
}
</style>
""")

# ---------------- GRID ----------------
for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        fill = intensity(day["contributionCount"])
        d = (x * 7 + y) * 0.0113
        is_mask = (x, y) in TH_EFOOL_MASK

        baseX = x*(CELL+GAP)
        baseY = y*(CELL+GAP)

        for i in range(SUBDIV):
            for j in range(SUBDIV):
                px = baseX + i*micro
                py = baseY + j*micro
                svg.append(
                    f'<rect class="cell" x="{px}" y="{py}" width="{micro}" height="{micro}" '
                    f'fill="{fill}" style="animation-delay:{d}s"/>'
                )

        if is_mask:
            svg.append(f'<rect x="{baseX}" y="{baseY}" width="{CELL}" height="{CELL}" '
                       f'fill="none" stroke="white" stroke-width="1.2"/>')

# ------------- JULIA OVERLAY -------------
for x, week in enumerate(weeks):
    for y in range(7):
        baseX = x*(CELL+GAP)
        baseY = y*(CELL+GAP)

        for i in range(SUBDIV):
            for j in range(SUBDIV):
                px = baseX + i*micro
                py = baseY + j*micro

                nx = (px / W)
                ny = (py / H)
                t = julia_val(nx, ny)

                if t < 0.15:
                    continue

                op = round(0.42 * t, 3)

                svg.append(
                    f'<rect class="jl" x="{px}" y="{py}" width="{micro}" height="{micro}" '
                    f'fill="{J_COLOR}" fill-opacity="{op}"/>'
                )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg","w") as f:
    f.write("\n".join(svg))

print("✅ SVG generated with Julia overlay ✨")
