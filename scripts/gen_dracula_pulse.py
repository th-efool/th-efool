import os, requests, cmath, math

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
W = len(weeks)*(CELL+GAP)
H = 7*(CELL+GAP)

SUBDIV = 2
micro = CELL//SUBDIV
micro_gap = GAP/SUBDIV

def intensity(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th:
            return PALETTE[i-1]
    return PALETTE[-1]

# -------- Julia fractal field --------
c = complex(-0.70176, -0.3842)
max_iter = 28

def julia_val(nx, ny):
    # map canvas coords -> complex plane
    zx = 1.4*(nx/W - 0.5)
    zy = 1.4*(ny/H - 0.5)
    z = complex(zx, zy)
    for i in range(max_iter):
        z = z*z + c
        if abs(z) > 2: 
            return i / max_iter
    return 1.0

def mix(a,b,t): return a + (b-a)*t

def julia_color(alpha):
    # base fractal cyan #79dafa blended to your pink #ff6e96
    r1,g1,b1 = (0x79,0xda,0xfa)
    r2,g2,b2 = (0xff,0x6e,0x96)
    t = alpha*0.9
    return f"rgba({int(mix(r1,r2,t))},{int(mix(g1,g2,t))},{int(mix(b1,b2,t))},{alpha:.3f})"

svg = [
    f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">'
]

svg.append("""
<style>
@keyframes pulse {
  0%,100% { opacity:1; filter:drop-shadow(0 0 2px currentColor); }
  92% { opacity:.85; filter:drop-shadow(0 0 5px currentColor); }
  96% { opacity:.45; filter:drop-shadow(0 0 1px currentColor); }
}
.cell{shape-rendering:crispEdges;animation:pulse 2s infinite linear;}
.jf {shape-rendering:crispEdges;animation:pulse 2s infinite linear;}
</style>
""")

for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        baseX = x*(CELL+GAP)
        baseY = y*(CELL+GAP)
        fill = intensity(day["contributionCount"])
        delay = (x*7+y)*0.0113
        is_mask = (x,y) in TH_EFOOL_MASK

        # micro-pixels
        for i in range(SUBDIV):
            for j in range(SUBDIV):
                px = baseX + i*(micro+micro_gap)
                py = baseY + j*(micro+micro_gap)
                svg.append(
                    f'<rect class="cell" x="{px}" y="{py}" width="{micro}" height="{micro}" fill="{fill}" style="animation-delay:{delay}s"/>'
                )

                # fractal overlay
                nx = px + micro*0.5
                ny = py + micro*0.5
                a = julia_val(nx, ny)
                if a > 0.05:
                    col = julia_color(a*0.65)
                    svg.append(
                        f'<rect class="jf" x="{px}" y="{py}" width="{micro}" height="{micro}" fill="{col}" style="animation-delay:{delay}s"/>'
                    )

        if is_mask:
            svg.append(
                f'<rect x="{baseX}" y="{baseY}" width="{CELL}" height="{CELL}" fill="none" stroke="white" stroke-width="1.2"/>'
            )

svg.append("</svg>")

os.makedirs("dist", exist_ok=True)
with open("dist/heartbeat-dracula.svg","w") as f:
    f.write("\n".join(svg))

print("✅ SVG generated: dist/heartbeat-dracula.svg (Julia pulse overlay)")
