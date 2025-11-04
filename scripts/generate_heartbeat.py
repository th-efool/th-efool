import requests, os, math, datetime, json

user = os.getenv("GITHUB_REPOSITORY").split("/")[0]
token = os.getenv("GH_TOKEN")

query = """
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

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"user": user}},
    headers={"Authorization": f"Bearer {token}"}
)

days = [d for w in resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
today = datetime.date.today().isoformat()
commits = next((d["contributionCount"] for d in days if d["date"] == today), 0)

pulse = max(min(commits / 10, 1.0), 0.1)
speed = 0.8 - pulse * 0.5  # seconds per beat

svg = f"""
<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
<style>
@keyframes beat {{
  0%   {{ transform: scale(1); filter: brightness(0.5); }}
  25%  {{ transform: scale({1 + pulse}); filter: brightness(1); }}
  50%  {{ transform: scale(1); filter: brightness(0.6); }}
  100% {{ transform: scale(1); filter: brightness(0.5); }}
}}
.heart {{
  fill: #8b0000;
  animation: beat {speed}s infinite;
  transform-origin: center;
}}
.bg {{
  fill: black;
}}
</style>
<rect class="bg" width="100%" height="100%"/>
<path class="heart"
d="M120 210
C10 130 30 40 120 80
C210 40 230 130 120 210Z"/>
</svg>
"""

os.makedirs("dist", exist_ok=True)
open("dist/heartbeat.svg", "w").write(svg)
