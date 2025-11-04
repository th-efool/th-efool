#!/usr/bin/env python3
# scripts/gen_dracula_pulse.py
# Generates dist/dracula-pulse.svg from GitHub contributions (GraphQL).
# Fallback demo mode if GH_TOKEN is not provided.
#
# Fixes:
#  - transparent background
#  - visible low-commit cells
#  - actual glow via per-rect filters + animated blur
#  - deterministic desynced jitter per cell

import os, sys, math, json, hashlib, datetime, requests
from pathlib import Path

# ---------- CONFIG ----------
CELL = 12            # size of each square in px
GAP = 4              # gap between squares
ROWS = 7
BASE_PERIOD = 2.0
JITTER_SCALE = 0.35
OUT_DIR = Path("dist")
OUT = OUT_DIR / "dracula-pulse.svg"

# Dracula-ish palette for tiers 0..4 (level0 is darkest but still visible)
PALETTE = [
    "#1b1e26",  # 0: very low (distinct from transparency)
    "#44475a",  # 1: low
    "#6272a4",  # 2: mid
    "#bd93f9",  # 3: high
    "#ff79c6",  # 4: top
]

# micro-noise amplitude (additional tiny opacity modulation)
NOISE_AMPL = 0.03
MIN_OPACITY_FLOOR = 0.15   # absolute minimum visible opacity for level0
# ---------- END CONFIG ----------

def demo_grid():
    cols = 52
    grid = []
    import random
    random.seed(42)
    for x in range(cols):
        for y in range(ROWS):
            val = int(max(0, (math.sin(x/6.0 + y/2.0) + 1)*2 + random.random()*3))
            grid.append(val)
    return grid

def fetch_contributions(user):
    token = os.getenv("GH_TOKEN")
    if not token:
        print("GH_TOKEN not present: falling back to demo mode.")
        return demo_grid()

    q = """
    query($user:String!) {
      user(login:$user) {
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
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(url, json={"query": q, "variables": {"user": user}}, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    try:
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except Exception as e:
        print("GraphQL response parse error:", e, file=sys.stderr)
        print(json.dumps(data, indent=2), file=sys.stderr)
        raise

    grid = []
    for w in weeks:
        for d in w["contributionDays"]:
            grid.append(int(d["contributionCount"]))
    return grid

def bucket_level(v, maxv):
    if maxv <= 0: return 0
    t = v / maxv
    if t <= 0.05: return 0
    if t <= 0.25: return 1
    if t <= 0.5: return 2
    if t <= 0.8: return 3
    return 4

def seeded_jitter(i):
    h = hashlib.sha1(str(i).encode()).hexdigest()
    x = int(h[:8], 16)
    frac = (x % 1000000) / 1000000.0
    return (frac * 2 - 1) * JITTER_SCALE

def make_svg(grid):
    if len(grid) % ROWS != 0:
        cols = math.ceil(len(grid) / ROWS)
        needed = cols * ROWS - len(grid)
        grid = grid + [0]*needed

    cols = len(grid) // ROWS
    width = cols * CELL + (cols-1) * GAP
    height = ROWS * CELL + (ROWS-1) * GAP

    max_commit = max(grid) or 1
    now = datetime.date.today().isoformat()

    rects = []
    filters = []

    for idx, commits in enumerate(grid):
        col = idx // ROWS
        row = idx % ROWS
        x = col * (CELL + GAP)
        y = row * (CELL + GAP)

        level = bucket_level(commits, max_commit)
        fill = PALETTE[level]
        intensity = commits / max_commit if max_commit else 0.0

        # baseline and peak opacities: ensure visibility even at low commits
        min_opacity = max(MIN_OPACITY_FLOOR, 0.30 + 0.30 * intensity)  # raised baseline
        max_opacity = min(1.0, 0.70 + 0.30 * intensity)

        # period shorter for higher intensity (faster pulse)
        period = max(0.6, BASE_PERIOD - 0.9 * intensity)

        jitter = seeded_jitter(idx)
        begin = f"{jitter:+.3f}s" if abs(jitter) > 1e-6 else "0s"

        # subtle blur sizing
        blur_base = 0.35 + intensity * 0.9
        blur_peak = blur_base * (1.6 + intensity)

        # Filter id unique per rect to allow animating its inner feGaussianBlur
        fid = f"glow{idx}"

        # create filter definition (per-rect)
        f = f'''
    <filter id="{fid}" x="-80%" y="-80%" width="260%" height="260%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceGraphic" stdDeviation="{blur_base:.3f}" result="b" id="b{idx}"/>
      <feMerge>
        <feMergeNode in="b"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>'''
        filters.append(f)

        # Two opacity animations: main breath + slow micro-noise shimmer (desynced)
        rect = f'''
  <g transform="translate({x:.1f},{y:.1f})">
    <rect x="0" y="0" width="{CELL}" height="{CELL}" rx="2" ry="2"
          fill="{fill}" opacity="{min_opacity:.3f}" filter="url(#{fid})">
      <animate attributeName="opacity"
               values="{min_opacity:.3f};{max_opacity:.3f};{min_opacity:.3f}"
               dur="{period:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
      <animate attributeName="opacity"
               values="{min_opacity:.3f};{(min_opacity+max_opacity)/2:.3f};{min_opacity + NOISE_AMPL:.3f};{(min_opacity+max_opacity)/2:.3f};{min_opacity:.3f}"
               dur="{period*3:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
      <!-- animate blur stdDeviation on the inner feGaussianBlur by targeting its id -->
      <animate xlink:href="#b{idx}" attributeName="stdDeviation"
               from="{blur_base:.3f}" to="{blur_peak:.3f}"
               dur="{period:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
    </rect>
  </g>'''
        rects.append(rect)

    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-label="Dracula pulse grid generated {now}">
  <defs>
    {"".join(filters)}
    <style><![CDATA[
      /* transparent background intentionally: no background rect */
      rect {{ shape-rendering: geometricPrecision; }}
    ]]></style>
  </defs>

  <g>
    {"".join(rects)}
  </g>
</svg>
'''
    return svg

def main():
    repo = os.getenv("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY not set. Falling back to demo mode.")
        grid = demo_grid()
    else:
        owner = repo.split("/")[0]
        grid = fetch_contributions(owner)

    svg = make_svg(grid)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT.resolve()}")

if __name__ == "__main__":
    main()
