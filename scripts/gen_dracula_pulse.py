#!/usr/bin/env python3
import os, requests, math

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

# Roboto-ish TH-EFOOL pixel mask base coords (small pixel font)
TH_EFOOL_MASK_BASE = {
    # T (Roboto)
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

# GraphQL query
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
)
try:
    resp_json = resp.json()
except Exception:
    print("❌ GitHub returned non-json:", resp.text)
    raise

if "errors" in resp_json:
    print("❌ GitHub GraphQL errors:", resp_json["errors"])
    raise SystemExit("GitHub GraphQL error")

weeks = resp_json["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
calendar_width = len(weeks)

# Center mask and shift down 1 row
mask_width = max(x for x,_ in TH_EFOOL_MASK_BASE) + 1
x_offset = (calendar_width - mask_width) // 2
TH_EFOOL_MASK = {(x + x_offset, y + 1) for (x, y) in TH_EFOOL_MASK_BASE}

# Grid visual parameters
CELL, GAP = 14, 3
W = calendar_width * (CELL + GAP)
H = 7 * (CELL + GAP)

# Fractal band sizes (px)
band_h = 80   # height of each fractal band (top & bottom)
band_w = W    # render fractal across full svg width
fractal_res_x = 300  # resolution for fractal (lower -> fewer rects)
fractal_res_y = 80   # should approximate band_h

# color mapper for fractal (pink-magenta tones)
def fractal_color(iter_norm):
    # iter_norm in [0,1], map to pinkish palette (soft -> intense)
    # Using simple interpolation between two hues
    # base rgba low -> bright hex
    if iter_norm >= 0.95:
        return "#ff6e96"
    # map to rgba variants for subtlety
    a = 0.2 + 0.8 * iter_norm
    # produce rgba with same pink channel
    r, g, b = 255, 110, 150
    return f"rgba({r},{g},{b},{a:.3f})"

# intensity mapping for contribution cells (fixed bug: direct index)
def intensity(count):
    for i, th in enumerate(THRESHOLDS):
        if count < th:
            return PALETTE[i]
    return PALETTE[-1]

# generate julia set values for a small raster grid
def generate_julia(width, height, cx=-0.8, cy=0.156, zoom=1.5, maxiter=80):
    # returns list of rows, each row is list of normalized iteration [0..1]
    result = [[0.0]*width for _ in range(height)]
    # bounding box in complex plane
    aspect = width/height
    x_min = -zoom*aspect
    x_max = zoom*aspect
    y_min = -zoom
    y_max = zoom
    for j in range(height):
        y = y_min + (y_max - y_min) * (j / (height - 1))
        for i in range(width):
            x = x_min + (x_max - x_min) * (i / (width - 1))
            zx, zy = x, y
            iteration = 0
            while zx*zx + zy*zy < 4.0 and iteration < maxiter:
                xt = zx*zx - zy*zy + cx
                zy = 2*zx*zy + cy
                zx = xt
                iteration += 1
            result[j][i] = iteration / maxiter
    return result

# compute two fractal rasters (top and bottom reuse same data)
julia = generate_julia(fractal_res_x, fractal_res_y, cx=-0.8, cy=0.156, zoom=1.2, maxiter=120)

# Build svg
svg_lines = []
total_h = band_h + H + band_h
svg_lines.append(f'<svg width="{W}" height="{total_h}" viewBox="0 0 {W} {total_h}" xmlns="http://www.w3.org/2000/svg" fill="none">')

# CSS + animations: breathing glow for fractal bands, ripple for grid cells
svg_lines.append("""
<style>
@keyframes fractalBreathe {
  0% { opacity: 0.65; filter: drop-shadow(0 0 6px rgba(255,110,150,0.2)); transform: translateY(0px) scale(1); }
  50% { opacity: 1;    filter: drop-shadow(0 0 20px rgba(255,110,150,0.45)); transform: translateY(-2px) scale(1.01); }
  100% { opacity: 0.65; filter: drop-shadow(0 0 6px rgba(255,110,150,0.2)); transform: translateY(0px) scale(1); }
}

@keyframes cellPulse {
  0% { opacity: 0.95; }
  50% { opacity: 0.5; }
  100% { opacity: 0.95; }
}

.fractalBand {
  transform-origin: center;
  animation: fractalBreathe 5.2s ease-in-out infinite;
}

.cell {
  shape-rendering: crispEdges;
  animation: cellPulse 3.5s infinite ease-in-out;
}
.mask {
  stroke: white;
  stroke-width: 1.2;
}
</style>
""")

# Draw top fractal band as grouped <rect> (scaled to full width)
svg_lines.append(f'<g class="fractalBand" transform="translate(0,0)">')
# compute rect size in svg coords
rect_w = W / fractal_res_x
rect_h = band_h / fractal_res_y
for row in range(fractal_res_y):
    y = row * rect_h
    for col in range(fractal_res_x):
        x = col * rect_w
        v = julia[row][col]  # 0..1
        color = fractal_color(v)
        svg_lines.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{rect_w:.3f}" height="{rect_h:.3f}" fill="{color}" />')
svg_lines.append('</g>')

# Draw center GitHub grid group, positioned after top band
grid_y = band_h
svg_lines.append(f'<g id="github" transform="translate(0,{grid_y})">')

# Draw grid cells
for x, week in enumerate(weeks):
    for y, day in enumerate(week["contributionDays"]):
        c = day["contributionCount"]
        fill = intensity(c)
        # fractal-based subtle phase offset for variety
        # sample julia at corresponding normalized position
        sample_x = int((x / max(1, calendar_width-1)) * (fractal_res_x-1))
        sample_y = int((y / 6) * (fractal_res_y-1))
        phase = julia[sample_y][sample_x]
        duration = 2.4 + phase * 2.0
        delay = phase * 1.2
        stroke_attr = 'class="mask"' if (x, y) in TH_EFOOL_MASK else ''
        svg_lines.append(
            f'<rect class="cell" x="{x*(CELL+GAP)}" y="{y*(CELL+GAP)}" width="{CELL}" height="{CELL}" '
            f'fill="{fill}" {stroke_attr} '
            f'style="animation-duration:{duration:.3f}s; animation-delay:{delay:.3f}s"/>'
        )

svg_lines.append('</g>')  # end github group

# Draw bottom fractal band, positioned after grid
bottom_y = band_h + H
svg_lines.append(f'<g class="fractalBand" transform="translate(0,{bottom_y})">')
for row in range(fractal_res_y):
    y = row * rect_h
    for col in range(fractal_res_x):
        x = col * rect_w
        # optionally invert rows to create mirrored effect
        v = julia[fractal_res_y-1-row][col]
        color = fractal_color(v)
        svg_lines.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{rect_w:.3f}" height="{rect_h:.3f}" fill="{color}" />')
svg_lines.append('</g>')

svg_lines.append('</svg>')

os.makedirs("dist", exist_ok=True)
out_path = "dist/heartbeat-dracula-fractal.svg"
with open(out_path, "w") as f:
    f.write("\n".join(svg_lines))

print("✅ Generated", out_path)
