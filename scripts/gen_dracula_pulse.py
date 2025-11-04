import os, requests

GITHUB_USER = "th-efool"

COLORS = [
    "#0d1117",
    "rgba(255,110,150,0.15)",
    "rgba(255,110,150,0.22)",
    "rgba(255,110,150,0.35)",
    "rgba(255,110,150,0.55)",
    "rgba(255,110,150,0.75)",
    "#ff6e96",
]

THRESHOLDS = [0,1,2,4,8,12,20]

MASK_BASE = {
    (0,0),(1,0),(2,0),(1,1),(1,2),(1,3),(1,4),
    (4,0),(4,1),(4,2),(4,3),(4,4),(5,2),(6,0),(6,1),(6,2),(6,3),(6,4),
    (8,2),(9,2),(10,2),
    (12,0),(12,1),(12,2),(12,3),(12,4),(13,0),(14,0),(14,1),(14,2),(13,4),(14,4),
    (16,0),(16,1),(16,2),(16,3),(16,4),(17,0),(18,0),(18,1),(18,2),
    (20,1),(20,2),(20,3),(21,0),(21,4),(22,1),(22,2),(22,3),
    (24,1),(24,2),(24,3),(25,0),(25,4),(26,1),(26,2),(26,3),
    (28,0),(28,1),(28,2),(28,3),(28,4),(29,4),(30,4)
}

QUERY = """
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

def pick_color(count):
    for idx, threshold in enumerate(THRESHOLDS):
        if count < threshold: return COLORS[idx-1]
    return COLORS[-1]

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": GITHUB_USER}},
        headers={"Authorization": f"bearer {token}"}
    ).json()

    weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    week_count = len(weeks)
    glyph_width = max(x for x,_ in MASK_BASE) + 1
    x_shift = (week_count - glyph_width) // 2
    mask = {(x + x_shift, y + 1) for (x, y) in MASK_BASE}

    CELL, GAP = 14, 3
    MICRO_DIV = 2
    micro_size = CELL // MICRO_DIV
    micro_gap = GAP / MICRO_DIV

    total_w = week_count * (CELL + GAP)
    total_h = 7 * (CELL + GAP)

    svg = [f'<svg width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" fill="none" xmlns="http://www.w3.org/2000/svg">']

    svg.append("""
<style>
@keyframes pulse {
  0%,100% { opacity:1; filter:drop-shadow(0 0 2px currentColor); }
  92% { opacity:.85; filter:drop-shadow(0 0 5px currentColor); }
  96% { opacity:.45; filter:drop-shadow(0 0 1px currentColor); }
}
.cell { shape-rendering:crispEdges; animation:pulse 2s infinite linear; }
</style>
""")

    for x, week in enumerate(weeks):
        base_x = x * (CELL + GAP)

        for y, day in enumerate(week["contributionDays"]):
            base_y = y * (CELL + GAP)
            color = pick_color(day["contributionCount"])
            delay = (x * 7 + y) * 0.0113
            selected = (x, y) in mask

            for mx in range(MICRO_DIV):
                px = base_x + mx*(micro_size+micro_gap)
                for my in range(MICRO_DIV):
                    py = base_y + my*(micro_size+micro_gap)
                    svg.append(
                        f'<rect class="cell" x="{px}" y="{py}" width="{micro_size}" height="{micro_size}" '
                        f'fill="{color}" style="animation-delay:{delay}s" />'
                    )

            if selected:
                svg.append(
                    f'<rect x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" '
                    f'fill="none" stroke="white" stroke-width="1.2"/>'
                )

    svg.append("</svg>")

    os.makedirs("dist", exist_ok=True)
    with open("dist/heartbeat-dracula.svg","w") as f:
        f.write("\n".join(svg))

    print("✅ SVG generated: dist/heartbeat-dracula.svg")

if __name__ == "__main__":
    main()
