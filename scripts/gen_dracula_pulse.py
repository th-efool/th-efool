#!/usr/bin/env python3
# gen_heartbeat_grid_dracula.py
# Generates dist/heartbeat-grid.svg from GitHub contributions (GraphQL).
# Fallback demo mode if GH_TOKEN is not provided.

import os, sys, math, json, hashlib, datetime, requests
from pathlib import Path

# ---------- CONFIG ----------
CELL = 12            # size of each square in px
GAP = 4              # gap between squares
ROWS = 7
# pulse base period (we target ~2s for mid intensity)
BASE_PERIOD = 2.0
# jitter scale (seconds) applied per cell (desynced)
JITTER_SCALE = 0.35

OUT_DIR = Path("dist")
OUT = OUT_DIR / "dracula-pulse.svg"

# Dracula-ish palette for tiers 0..4 (level0 is darkest background)
PALETTE = [
    "#282a36",  # 0: background / empty
    "#44475a",  # 1: low
    "#6272a4",  # 2: mid
    "#bd93f9",  # 3: high
    "#ff79c6",  # 4: top
]

# micro-noise amplitude (opacity fraction)
NOISE_AMPL = 0.03
# ---------- END CONFIG ----------

# Safe demo data generator when GH_TOKEN missing
def demo_grid():
    # create 52 weeks * 7 days = 364 (approx) grid pattern with variety
    cols = 52
    grid = []
    import random
    random.seed(42)
    for x in range(cols):
        for y in range(ROWS):
            # make a natural-looking curve with randomness
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
    # map normalized intensity to 0..4
    if maxv <= 0: return 0
    t = v / maxv
    # thresholds tuned for pleasing dracula mapping
    if t <= 0.05: return 0
    if t <= 0.25: return 1
    if t <= 0.5: return 2
    if t <= 0.8: return 3
    return 4

def seeded_jitter(i):
    # produce stable jitter in [-JITTER_SCALE, +JITTER_SCALE] based on index
    h = hashlib.sha1(str(i).encode()).hexdigest()
    # take first 8 hex chars -> int
    x = int(h[:8], 16)
    frac = (x % 1000000) / 1000000.0  # 0..1
    return (frac * 2 - 1) * JITTER_SCALE

def make_svg(grid):
    if len(grid) % ROWS != 0:
        # pad to full weeks
        cols = math.ceil(len(grid) / ROWS)
        needed = cols * ROWS - len(grid)
        grid = grid + [0]*needed

    cols = len(grid) // ROWS
    width = cols * CELL + (cols-1) * GAP
    height = ROWS * CELL + (ROWS-1) * GAP

    max_commit = max(grid) or 1

    now = datetime.date.today().isoformat()

    # Build rects
    rects = []
    for idx, commits in enumerate(grid):
        col = idx // ROWS
        row = idx % ROWS
        x = col * (CELL + GAP)
        y = row * (CELL + GAP)

        level = bucket_level(commits, max_commit)
        fill = PALETTE[level]
        # intensity normalized 0..1
        intensity = commits / max_commit if max_commit else 0.0

        # compute opacity range per config:
        min_opacity = 0.45 + 0.35 * intensity   # base dim floor increases with commits
        max_opacity = min(1.0, 0.7 + 0.3 * intensity)

        # period slightly faster for higher intensity
        period = max(0.6, BASE_PERIOD - 0.9 * intensity)  # clamp min period to 0.6s

        # stable jitter per cell
        jitter = seeded_jitter(idx)
        begin = f"{jitter:+.3f}s" if jitter != 0 else "0s"

        # micro-noise using a very slow animate on opacity small amplitude
        noise_from = max(min_opacity - NOISE_AMPL, 0.0)
        noise_to   = min(max_opacity + NOISE_AMPL, 1.0)

        # Gaussian blur varying with intensity (subtle)
        blur_base = 0.3 + intensity * 0.9
        blur_peak = blur_base * 2.2

        # create rect with two animates: opacity pulse and blur stdDeviation animate
        rect = f'''
  <g transform="translate({x:.1f},{y:.1f})">
    <rect x="0" y="0" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{fill}" opacity="{min_opacity:.3f}" filter="url(#g{level})">
      <!-- breathing pulse (smooth ease) -->
      <animate attributeName="opacity"
               values="{min_opacity:.3f};{max_opacity:.3f};{min_opacity:.3f}"
               dur="{period:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
      <!-- micro-noise shimmer (slower, tiny amplitude, desynced) -->
      <animate attributeName="opacity"
               values="{min_opacity:.3f};{(min_opacity+max_opacity)/2:.3f};{noise_to:.3f};{(min_opacity+max_opacity)/2:.3f};{min_opacity:.3f}"
               dur="{period*3:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
      <!-- subtle blur pulse to simulate glow -->
      <animate xlink:href="#blur{idx}" attributeName="stdDeviation"
               from="{blur_base:.3f}" to="{blur_peak:.3f}"
               dur="{period:.3f}s"
               begin="{begin}"
               repeatCount="indefinite" />
    </rect>
  </g>
'''
        rects.append(rect)

    # Build filters for glow grouped per level (cheaper)
    filters = []
    for lvl in range(len(PALETTE)):
        # IDs g{lvl} and a blur id per rect referenced above
        filters.append(f'''
  <filter id="g{lvl}" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="0.6" result="blur" id="blur-level-{lvl}"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
''')

    # NOTE: we referenced blur{idx} in the animate xlink:href above — to ensure valid targets,
    # create invisible feGaussianBlur primitives per rect with unique ids. This technique
    # keeps the primary filter usage but animates a separate feGaussianBlur node linked by id.
    # We'll include them in defs as empty placeholders that the animate can target.
    blur_nodes = []
    for idx in range(len(grid)):
        blur_nodes.append(f'<feGaussianBlur id="blur{idx}" in="SourceGraphic" stdDeviation="0.6" />')

    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-label="Contribution heartbeat grid generated {now}">
  <defs>
    <style><![CDATA[
      svg {{ background: {PALETTE[0]}; display:block; }}
    ]]></style>
    <!-- group filters per level -->
    {''.join(filters)}
    <!-- per-rect blur nodes (targets for animate) -->
    <filter id="perrect-blur" x="-200%" y="-200%" width="400%" height="400%">
      {"".join(blur_nodes)}
    </filter>
  </defs>

  <g>
    {''.join(rects)}
  </g>
</svg>
'''
    return svg

def main():
    repo = os.getenv("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY not set. Use format 'owner/repo'. Falling back to demo mode.")
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
