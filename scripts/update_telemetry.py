#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

def fetch_github_data(username, token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "TheCreativeCodeFlow-Telemetry-Agent"
    }
    
    query = """
    query($username: String!) {
      user(login: $username) {
        name
        login
        followers {
          totalCount
        }
        repositories(first: 100, ownerAffiliations: OWNER) {
          totalCount
          nodes {
            name
            isFork
            stargazerCount
            forkCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    data = json.dumps({"query": query, "variables": {"username": username}}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "errors" in res_data:
                print(f"GraphQL errors: {res_data['errors']}", file=sys.stderr)
                sys.exit(1)
            return res_data["data"]["user"]
    except urllib.error.URLError as e:
        print(f"Failed to fetch data from GitHub API: {e}", file=sys.stderr)
        sys.exit(1)

def get_mock_data():
    # Return mock data matching original telemetry layout for testing/fallback
    return {
        "name": "Rahul Seervi",
        "login": "TheCreativeCodeFlow",
        "followers": {"totalCount": 10},
        "repositories": {
            "totalCount": 45,
            "nodes": [
                # Mock a few repositories to simulate stats calculation
                {"name": "Distributed-job-Scheduler", "isFork": False, "stargazerCount": 25, "forkCount": 1, "languages": {"edges": [{"size": 100000, "node": {"name": "TypeScript", "color": "#3178c6"}}]}},
                {"name": "MockPilot", "isFork": False, "stargazerCount": 15, "forkCount": 1, "languages": {"edges": [{"size": 50000, "node": {"name": "TypeScript", "color": "#3178c6"}}, {"size": 20000, "node": {"name": "JavaScript", "color": "#f1e05a"}}]}},
                {"name": "CodeZilaa", "isFork": False, "stargazerCount": 10, "forkCount": 0, "languages": {"edges": [{"size": 80000, "node": {"name": "TypeScript", "color": "#3178c6"}}]}},
                {"name": "CropCast", "isFork": False, "stargazerCount": 5, "forkCount": 0, "languages": {"edges": [{"size": 60000, "node": {"name": "Python", "color": "#3572A5"}}]}},
                {"name": "fork-1", "isFork": True, "stargazerCount": 0, "forkCount": 0, "languages": {"edges": []}},
                {"name": "fork-2", "isFork": True, "stargazerCount": 0, "forkCount": 0, "languages": {"edges": []}},
            ]
        },
        "contributionsCollection": {
            "contributionCalendar": {
                "totalContributions": 142,
                "weeks": [
                    # Simulate 16 weeks of activity with varying contribution counts
                    {"contributionDays": [{"contributionCount": (week_idx * 3 + day_idx) % 5 if (week_idx + day_idx) % 3 != 0 else 0, "date": f"2026-05-{day_idx+1:02d}"} for day_idx in range(7)]}
                    for week_idx in range(16)
                ]
            }
        }
    }

def calculate_stats(user_data, is_mock=False):
    stats = {}
    stats["total_repos"] = user_data["repositories"]["totalCount"]
    stats["followers"] = user_data["followers"]["totalCount"]
    
    total_stars = 0
    total_forks = 0
    stored_forks = 0
    language_totals = {}
    
    for repo in user_data["repositories"]["nodes"]:
        if repo["isFork"]:
            stored_forks += 1
        else:
            total_stars += repo["stargazerCount"]
            total_forks += repo["forkCount"]
            for edge in repo["languages"]["edges"]:
                lang_name = edge["node"]["name"]
                lang_size = edge["size"]
                language_totals[lang_name] = language_totals.get(lang_name, 0) + lang_size
                
    stats["stars"] = total_stars
    stats["forks"] = total_forks
    stats["stored_forks"] = stored_forks
    
    # Language percentages
    total_lang_size = sum(language_totals.values())
    languages_sorted = []
    if total_lang_size > 0:
        for name, size in language_totals.items():
            pct = (size / total_lang_size) * 100
            # Get default color if none exists
            color = "#888888"
            for repo in user_data["repositories"]["nodes"]:
                for edge in repo["languages"]["edges"]:
                    if edge["node"]["name"] == name:
                        color = edge["node"]["color"]
                        break
                if color != "#888888":
                    break
            languages_sorted.append({
                "name": name,
                "percentage": pct,
                "color": color
            })
        languages_sorted.sort(key=lambda x: x["percentage"], reverse=True)
    
    # Fallback to defaults if no languages found
    if not languages_sorted:
        languages_sorted = [
            {"name": "TypeScript", "percentage": 72.0, "color": "#3178c6"},
            {"name": "Python", "percentage": 24.0, "color": "#3572A5"},
            {"name": "JavaScript", "percentage": 3.0, "color": "#f1e05a"}
        ]
        
    stats["languages"] = languages_sorted[:3]  # Top 3 languages
    
    # Streaks calculation
    calendar = user_data["contributionsCollection"]["contributionCalendar"]
    stats["total_contributions"] = calendar["totalContributions"]
    
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append(day)
            
    days.sort(key=lambda x: x["date"])
    
    # Filter future days
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = [d for d in days if d["date"] <= today_str]
    
    active_days = sum(1 for d in days if d["contributionCount"] > 0)
    stats["active_days"] = active_days
    
    # Streak metrics
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    for d in days:
        if d["contributionCount"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0
            
    if len(days) >= 1:
        last_idx = len(days) - 1
        if days[last_idx]["contributionCount"] > 0:
            idx = last_idx
            while idx >= 0 and days[idx]["contributionCount"] > 0:
                current_streak += 1
                idx -= 1
        elif len(days) >= 2 and days[last_idx - 1]["contributionCount"] > 0:
            idx = last_idx - 1
            while idx >= 0 and days[idx]["contributionCount"] > 0:
                current_streak += 1
                idx -= 1
                
    if is_mock:
        stats["current_streak"] = 3
        stats["longest_streak"] = 17
        stats["active_days"] = 142
        stats["total_range"] = "22 Apr 2025 - Present"
        stats["current_range"] = "18 Aug - 20 Aug"
        stats["longest_range"] = "4 Jun - 20 Jun"
    else:
        stats["current_streak"] = current_streak
        stats["longest_streak"] = longest_streak
        
        # Total contributions range
        if len(days) > 0:
            start_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
            stats["total_range"] = f"{int(start_date.strftime('%d'))} {start_date.strftime('%b %Y')} - Present"
        else:
            stats["total_range"] = "Present"
            
        # Current streak range
        current_range = ""
        if current_streak > 0:
            last_active_idx = None
            for idx in range(len(days) - 1, -1, -1):
                if days[idx]["contributionCount"] > 0:
                    last_active_idx = idx
                    break
            if last_active_idx is not None:
                start_idx = last_active_idx - current_streak + 1
                if start_idx >= 0:
                    s_date = datetime.strptime(days[start_idx]["date"], "%Y-%m-%d")
                    e_date = datetime.strptime(days[last_active_idx]["date"], "%Y-%m-%d")
                    current_range = f"{int(s_date.strftime('%d'))} {s_date.strftime('%b')} - {int(e_date.strftime('%d'))} {e_date.strftime('%b')}"
        stats["current_range"] = current_range if current_range else "Inactive"
        
        # Longest streak range
        longest_range = ""
        best_start_idx = None
        best_end_idx = None
        current_start_idx = None
        max_len = 0
        current_len = 0
        for idx, d in enumerate(days):
            if d["contributionCount"] > 0:
                if current_len == 0:
                    current_start_idx = idx
                current_len += 1
                if current_len > max_len:
                    max_len = current_len
                    best_start_idx = current_start_idx
                    best_end_idx = idx
            else:
                current_len = 0
                
        if best_start_idx is not None and best_end_idx is not None:
            s_date = datetime.strptime(days[best_start_idx]["date"], "%Y-%m-%d")
            e_date = datetime.strptime(days[best_end_idx]["date"], "%Y-%m-%d")
            longest_range = f"{int(s_date.strftime('%d'))} {s_date.strftime('%b')} - {int(e_date.strftime('%d'))} {e_date.strftime('%b')}"
        stats["longest_range"] = longest_range if longest_range else "Inactive"
        
    # Get last 16 weeks contributions for the wave chart
    weeks = calendar["weeks"]
    last_16_weeks = weeks[-16:]
    week_contributions = []
    for w in last_16_weeks:
        w_sum = sum(d["contributionCount"] for d in w["contributionDays"])
        week_contributions.append(w_sum)
        
    stats["week_contributions"] = week_contributions
    return stats

def generate_svg(stats):
    # Retrieve stats variables
    total_repos = stats["total_repos"]
    followers = stats["followers"]
    stars = stats["stars"]
    forks = stats["forks"]
    stored_forks = stats["stored_forks"]
    current_streak = stats["current_streak"]
    longest_streak = stats["longest_streak"]
    languages = stats["languages"]
    total_contributions = stats["total_contributions"]
    total_range = stats["total_range"]
    current_range = stats["current_range"]
    longest_range = stats["longest_range"]
    
    # Calculate ring progress (circumference is 2 * pi * 22 = 138.23)
    # Arc path has a 40 degree gap at the top, so total arc length is 138.23 * (320 / 360) = 122.88
    total_arc_len = 122.88
    if longest_streak > 0:
        progress = min(current_streak / longest_streak, 1.0)
    else:
        progress = 0.0
    dash_offset = total_arc_len * (1 - progress)
        
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 240" width="100%" height="100%">
  <defs>
    <pattern id="dot-grid" width="16" height="16" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="1" fill="#1E293B" opacity="0.4" />
    </pattern>
    <linearGradient id="panel-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#030508"/>
      <stop offset="100%" stop-color="#070b12"/>
    </linearGradient>
    <style>
      .bg {{ fill: url(#panel-grad); stroke: #0f172a; stroke-width: 1.5; }}
      .title-main {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; font-weight: 700; fill: #00E5FF; letter-spacing: 2px; }}
      .hud-text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 8px; fill: #64748B; letter-spacing: 0.5px; }}
      .hud-text-bright {{ fill: #00FF87; font-weight: bold; }}
      .sec-title {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; font-weight: 700; fill: #8892b0; letter-spacing: 1px; }}
      .metric-lbl {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; fill: #64748B; font-weight: bold; letter-spacing: 0.5px; }}
      .metric-val {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; font-weight: bold; fill: #00E5FF; }}
      .env-lbl {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 8px; fill: #64748B; }}
      .env-val {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 8px; font-weight: bold; fill: #00FF87; }}
      .lang-lbl {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; font-weight: bold; fill: #94A3B8; }}
      .lang-pct {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; fill: #64748B; }}
      .bar-track {{ fill: #080d16; stroke: #1e293b; stroke-width: 0.5; }}
    </style>
  </defs>

  <!-- Container -->
  <rect width="800" height="240" rx="8" class="bg" />
  <rect width="800" height="240" rx="8" fill="url(#dot-grid)" />

  <!-- Top Header HUD -->
  <circle cx="25" cy="24" r="4" fill="#00FF87">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" />
  </circle>
  <text x="38" y="27" class="title-main">GITHUB CORE TELEMETRY // NODE_01</text>
  <text x="450" y="27" class="hud-text" text-anchor="middle">
    PORT: <tspan class="hud-text-bright">9000</tspan> &#160;▪&#160; 
    DAEMON: <tspan class="hud-text-bright">ACTIVE</tspan> &#160;▪&#160; 
    STABLE: <tspan class="hud-text-bright">TRUE</tspan>
  </text>
  <text x="770" y="27" class="hud-text" text-anchor="end">SYNC: {timestamp}</text>
  <line x1="20" y1="38" x2="780" y2="38" stroke="#0F172A" stroke-width="1.5" />

  <!-- COLUMN 1: System Metrics & Environment (X: 30 to 240) -->
  <g transform="translate(30, 50)">
    <text x="0" y="8" class="sec-title">CORE SYSTEM METRICS</text>
    <line x1="0" y1="14" x2="210" y2="14" stroke="#0F172A" stroke-width="1" />
    
    <!-- Core Metrics List -->
    <g transform="translate(0, 30)">
      <text x="0" y="0" class="metric-lbl">REPOSITORIES</text>
      <text x="210" y="0" class="metric-val" text-anchor="end">{total_repos}</text>
    </g>
    <g transform="translate(0, 48)">
      <text x="0" y="0" class="metric-lbl">FOLLOWERS</text>
      <text x="210" y="0" class="metric-val" text-anchor="end">{followers}</text>
    </g>
    <g transform="translate(0, 66)">
      <text x="0" y="0" class="metric-lbl">TOTAL STARS</text>
      <text x="210" y="0" class="metric-val" text-anchor="end">{stars}</text>
    </g>
    <g transform="translate(0, 84)">
      <text x="0" y="0" class="metric-lbl">STORED FORKS</text>
      <text x="210" y="0" class="metric-val" text-anchor="end">{stored_forks}</text>
    </g>

    <!-- Divider -->
    <line x1="0" y1="98" x2="210" y2="98" stroke="#0F172A" stroke-width="1" opacity="0.3" />

    <!-- Environment List -->
    <g transform="translate(0, 114)">
      <text x="0" y="0" class="env-lbl">RUNTIME: <tspan class="env-val">NODE v20</tspan></text>
      <text x="110" y="0" class="env-lbl">SOCKET: <tspan class="env-val">RESOLVED</tspan></text>
    </g>
    <g transform="translate(0, 130)">
      <text x="0" y="0" class="env-lbl">ENCRYPT: <tspan class="env-val">TLS_1.3</tspan></text>
      <text x="110" y="0" class="env-lbl">FRAMEWORK: <tspan class="env-val">ENG.</tspan></text>
    </g>
    <g transform="translate(0, 146)">
      <text x="0" y="0" class="env-lbl">ACCOUNT: <tspan class="env-val">ACTIVE</tspan></text>
      <text x="110" y="0" class="env-lbl">STATUS: <tspan class="env-val">SECURE</tspan></text>
    </g>
  </g>

  <!-- COLUMN DIVIDERS -->
  <line x1="260" y1="50" x2="260" y2="210" stroke="#0F172A" stroke-width="1.5" opacity="0.4" />
  <line x1="530" y1="50" x2="530" y2="210" stroke="#0F172A" stroke-width="1.5" opacity="0.4" />

  <!-- COLUMN 2: Active Streak Engine (X: 280 to 520) -->
  <g transform="translate(280, 50)">
    <text x="0" y="8" class="sec-title">ACTIVE STREAK ENGINE</text>
    <line x1="0" y1="14" x2="230" y2="14" stroke="#0F172A" stroke-width="1" />

    <!-- Left Column: Total Contributions -->
    <g transform="translate(0, 20)">
      <text x="35" y="45" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="22" font-weight="800" fill="#00E5FF" text-anchor="middle">{total_contributions}</text>
      <text x="35" y="68" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="700" fill="#94A3B8" text-anchor="middle">TOTAL</text>
      <text x="35" y="78" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="700" fill="#94A3B8" text-anchor="middle">CONTRIBS</text>
      <text x="35" y="94" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="6.5" fill="#64748B" text-anchor="middle">{total_range}</text>
    </g>

    <!-- Middle Column: Current Streak -->
    <g transform="translate(0, 20)">
      <!-- Flame Icon -->
      <path d="M 115 18 C 117.2 22 119.4 23.8 119.4 27 A 4.4 4.4 0 0 1 110.6 27 C 110.6 23.8 112.8 22 115 18 Z" fill="#FF9100" />
      
      <!-- Background Arc Ring -->
      <path d="M 122.5 31.3 A 22 22 0 1 1 107.5 31.3" fill="none" stroke="#101726" stroke-width="2.5" stroke-linecap="round" />
      
      <!-- Active Progress Arc Ring -->
      <path d="M 122.5 31.3 A 22 22 0 1 1 107.5 31.3" fill="none" stroke="#00E5FF" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="122.88" stroke-dashoffset="{dash_offset:.2f}" />
      
      <text x="115" y="57" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="18" font-weight="800" fill="#00E5FF" text-anchor="middle">{current_streak}</text>
      <text x="115" y="82" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="800" fill="#F1F5F9" text-anchor="middle">CURRENT</text>
      <text x="115" y="92" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="800" fill="#F1F5F9" text-anchor="middle">STREAK</text>
      <text x="115" y="108" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="6.5" fill="#64748B" text-anchor="middle">{current_range}</text>
    </g>

    <!-- Right Column: Longest Streak -->
    <g transform="translate(0, 20)">
      <text x="195" y="45" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="22" font-weight="800" fill="#00E5FF" text-anchor="middle">{longest_streak}</text>
      <text x="195" y="68" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="700" fill="#94A3B8" text-anchor="middle">LONGEST</text>
      <text x="195" y="78" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="8" font-weight="700" fill="#94A3B8" text-anchor="middle">STREAK</text>
      <text x="195" y="94" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="6.5" fill="#64748B" text-anchor="middle">{longest_range}</text>
    </g>
  </g>

  <!-- COLUMN 3: Primary Language Distribution (X: 550 to 780) -->
  <g transform="translate(550, 50)">
    <text x="0" y="8" class="sec-title">PRIMARY LANGUAGE DISTRIBUTION</text>
    <line x1="0" y1="14" x2="220" y2="14" stroke="#0F172A" stroke-width="1" />

    <g transform="translate(0, 25)">
"""
    
    for idx, lang in enumerate(languages):
        y_offset = idx * 45
        pct = lang["percentage"]
        name = lang["name"]
        color = lang["color"]
        
        # Track width is 220px
        bar_width = int((pct / 100) * 220)
        
        svg += f"""      <!-- {name} Bar -->
      <g transform="translate(0, {y_offset})">
        <text x="0" y="8" class="lang-lbl">{name}</text>
        <text x="220" y="8" class="lang-pct" text-anchor="end">{pct:.1f}%</text>
        <rect x="0" y="14" width="220" height="8" rx="2" class="bar-track" />
        <rect x="0" y="14" width="{bar_width}" height="8" rx="2" fill="{color}">
          <animate attributeName="width" from="0" to="{bar_width}" dur="1.2s" fill="freeze" />
        </rect>
      </g>
"""

    svg += """    </g>
  </g>
</svg>"""
    return svg


def main():
    username = "TheCreativeCodeFlow"
    # Check for GitHub token in env
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("PAT_TOKEN")
    
    if token:
        print("Token detected in environment. Fetching live data from GitHub GraphQL API...")
        user_data = fetch_github_data(username, token)
        stats = calculate_stats(user_data)
    else:
        print("No GitHub token detected. Generating dashboard using fallback/mock profile statistics...")
        user_data = get_mock_data()
        stats = calculate_stats(user_data, is_mock=True)
        
    svg_content = generate_svg(stats)
    
    # Save the SVG
    target_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(target_dir)
    output_path = os.path.join(workspace_dir, "assets", "github_telemetry.svg")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"Successfully generated telemetry SVG at: {output_path}")

if __name__ == "__main__":
    main()
