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
    else:
        stats["current_streak"] = current_streak
        stats["longest_streak"] = longest_streak
        
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
    active_days = stats["active_days"]
    languages = stats["languages"]
    week_contributions = stats["week_contributions"]
    
    # Calculate wave chart coordinates (relative to the active streak engine group translate(280, 50))
    # Available area width: 220px (X: 10 to 230), height: 75px (Y: 40 to 115)
    max_c = max(week_contributions) if max(week_contributions) > 0 else 1
    points = []
    for i, c in enumerate(week_contributions):
        x = 10 + (i * 14.66)
        y = 115 - (c / max_c) * 70
        points.append((x, y))
        
    # Build SVG path for spline
    path_d = ""
    if points:
        path_d = f"M {points[0][0]:.2f} {points[0][1]:.2f}"
        for i in range(1, len(points)):
            path_d += f" L {points[i][0]:.2f} {points[i][1]:.2f}"
            
    # Area path (closed polygon for gradient fill)
    area_d = ""
    if points:
        area_d = f"{path_d} L {points[-1][0]:.2f} 115.00 L {points[0][0]:.2f} 115.00 Z"
        
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 240" width="100%" height="100%">
  <defs>
    <pattern id="dot-grid" width="16" height="16" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="1" fill="#1E293B" opacity="0.4" />
    </pattern>
    <linearGradient id="wave-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#00FF87" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#00FF87" stop-opacity="0.0"/>
    </linearGradient>
    <linearGradient id="panel-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#030508"/>
      <stop offset="100%" stop-color="#070b12"/>
    </linearGradient>
    <style>
      .bg {{ fill: url(#panel-grad); stroke: #0f172a; stroke-width: 1.5; }}
      .title-main {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; font-weight: 700; fill: #00E5FF; letter-spacing: 2px; }}
      .hud-text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 8px; fill: #64748B; letter-spacing: 0.5px; }}
      .hud-text-bright {{ fill: #00FF87; font-weight: bold; }}
      .card-border {{ fill: #050810; stroke: #1e293b; stroke-width: 1; }}
      .card-title {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 8px; font-weight: 700; fill: #64748B; letter-spacing: 0.5px; }}
      .card-val {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 16px; font-weight: 800; fill: #F1F5F9; }}
      .accent-cyan {{ fill: #00E5FF; }}
      .accent-green {{ fill: #00FF87; }}
      .accent-amber {{ fill: #FF9100; }}
      .accent-purple {{ fill: #BD00FF; }}
      .sec-title {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; font-weight: 700; fill: #64748B; letter-spacing: 1px; }}
      .chart-grid {{ stroke: #1e293b; stroke-width: 0.5; stroke-dasharray: 2,2; }}
      .stat-lbl {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; fill: #64748B; }}
      .stat-val {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9px; font-weight: bold; fill: #F1F5F9; }}
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
  <text x="38" y="27" class="title-main">GITHUB CORE TELEMETRY // SYSTEM_NODE_01</text>
  <text x="500" y="26" class="hud-text" text-anchor="start">
    PORT: <tspan class="hud-text-bright">9000</tspan> &#160;▪&#160; 
    DAEMON: <tspan class="hud-text-bright">ACTIVE</tspan> &#160;▪&#160; 
    STABLE: <tspan class="hud-text-bright">TRUE</tspan>
  </text>
  <text x="775" y="26" class="hud-text" text-anchor="end">SYNC_TIME: {timestamp}</text>
  <line x1="20" y1="38" x2="780" y2="38" stroke="#0F172A" stroke-width="1.5" />

  <!-- LEFT PANEL: Core Metrics (X: 20 to 260) -->
  <!-- Card 1: Repositories -->
  <g transform="translate(20, 50)">
    <rect width="112" height="42" rx="4" class="card-border" style="stroke: #00E5FF; stroke-opacity: 0.5;" />
    <!-- Mini Folder Graphic -->
    <path d="M 12 14 L 18 14 L 20 17 L 26 17 L 26 28 L 12 28 Z" fill="none" stroke="#00E5FF" stroke-width="1" />
    <text x="34" y="18" class="card-title">SYS.REPOSITORIES</text>
    <text x="34" y="32" class="card-val">{total_repos}</text>
    <rect x="98" y="10" width="4" height="4" class="accent-cyan" />
  </g>

  <!-- Card 2: Followers -->
  <g transform="translate(148, 50)">
    <rect width="112" height="42" rx="4" class="card-border" style="stroke: #FF9100; stroke-opacity: 0.5;" />
    <!-- Mini Connections Graphic -->
    <circle cx="16" cy="18" r="2.5" fill="none" stroke="#FF9100" stroke-width="1" />
    <circle cx="24" cy="24" r="2.5" fill="none" stroke="#FF9100" stroke-width="1" />
    <line x1="18.5" y1="20.5" x2="21.5" y2="21.5" stroke="#FF9100" stroke-width="1" />
    <text x="34" y="18" class="card-title">SYS.FOLLOWERS</text>
    <text x="34" y="32" class="card-val">{followers}</text>
    <rect x="98" y="10" width="4" height="4" class="accent-amber" />
  </g>

  <!-- Card 3: Profile Stars -->
  <g transform="translate(20, 102)">
    <rect width="112" height="42" rx="4" class="card-border" style="stroke: #00FF87; stroke-opacity: 0.5;" />
    <!-- Mini Star Graphic -->
    <path d="M 18 12 L 20 16 L 24 16 L 21 19 L 22 23 L 18 21 L 14 23 L 15 19 L 12 16 L 16 16 Z" fill="none" stroke="#00FF87" stroke-width="1" />
    <text x="34" y="18" class="card-title">SYS.STARS_TOTAL</text>
    <text x="34" y="32" class="card-val">{stars}</text>
    <rect x="98" y="10" width="4" height="4" class="accent-green" />
  </g>

  <!-- Card 4: Stored Forks -->
  <g transform="translate(148, 102)">
    <rect width="112" height="42" rx="4" class="card-border" style="stroke: #BD00FF; stroke-opacity: 0.5;" />
    <!-- Mini Fork Graphic -->
    <path d="M 14 13 L 14 17 A 4 4 0 0 0 18 21 L 18 26 M 22 13 L 22 17 A 4 4 0 0 1 18 21" fill="none" stroke="#BD00FF" stroke-width="1" />
    <circle cx="18" cy="27" r="1.5" fill="#BD00FF" />
    <text x="34" y="18" class="card-title">SYS.STORED_FORKS</text>
    <text x="34" y="32" class="card-val">{stored_forks}</text>
    <rect x="98" y="10" width="4" height="4" class="accent-purple" />
  </g>
  
  <!-- Environment indicators at the bottom left -->
  <g transform="translate(20, 160)">
    <rect width="240" height="60" rx="4" class="card-border" />
    <text x="15" y="18" class="hud-text">ENV_RUNTIME: <tspan class="hud-text-bright">NODE v20</tspan></text>
    <text x="15" y="33" class="hud-text">SYS_ENCRYPTION: <tspan class="hud-text-bright">TLS_1.3</tspan></text>
    <text x="15" y="48" class="hud-text">CORE_ACCOUNT: <tspan class="hud-text-bright">ACTIVE</tspan></text>
    
    <text x="130" y="18" class="hud-text">IP_SOCKET: <tspan class="hud-text-bright">RESOLVED</tspan></text>
    <text x="130" y="33" class="hud-text">FRAMEWORK: <tspan class="hud-text-bright">ENGINEERING</tspan></text>
    <text x="130" y="48" class="hud-text">SYS_STATUS: <tspan class="hud-text-bright" fill="#00FF87">SECURE</tspan></text>
  </g>

  <!-- MIDDLE PANEL: Active Streak Engine (X: 280 to 520) -->
  <g transform="translate(280, 50)">
    <text x="0" y="8" class="sec-title">ACTIVE STREAK ENGINE</text>
    <line x1="0" y1="14" x2="240" y2="14" stroke="#0F172A" stroke-width="1" />

    <!-- Wave Chart Grid -->
    <line x1="10" y1="45" x2="235" y2="45" class="chart-grid" />
    <line x1="10" y1="75" x2="235" y2="75" class="chart-grid" />
    <line x1="10" y1="105" x2="235" y2="105" class="chart-grid" />
    <line x1="10" y1="115" x2="235" y2="115" stroke="#1e293b" stroke-width="1" />

    <!-- Wave Chart Fill and Line -->
    <path d="{area_d}" fill="url(#wave-grad)" />
    <path d="{path_d}" fill="none" stroke="#00FF87" stroke-width="1.5" />
    
    <!-- Sparkles on Peak -->
    <circle cx="{points[-1][0]:.2f}" cy="{points[-1][1]:.2f}" r="2" fill="#00FF87" />

    <!-- Streak Data Grid -->
    <g transform="translate(0, 130)">
      <text x="0" y="10" class="stat-lbl">CURRENT STREAK</text>
      <text x="0" y="22" class="stat-val" style="fill: #00E5FF; font-size: 11px;">{current_streak} DAYS</text>

      <text x="90" y="10" class="stat-lbl">LONGEST STREAK</text>
      <text x="90" y="22" class="stat-val">{longest_streak} DAYS</text>

      <text x="180" y="10" class="stat-lbl">ACTIVE DAYS</text>
      <text x="180" y="22" class="stat-val">{active_days} / 365</text>
    </g>
  </g>

  <!-- RIGHT PANEL: Language Distribution (X: 540 to 780) -->
  <g transform="translate(540, 50)">
    <text x="0" y="8" class="sec-title">PRIMARY LANGUAGE DISTRIBUTION</text>
    <line x1="0" y1="14" x2="240" y2="14" stroke="#0F172A" stroke-width="1" />

    <!-- Languages loop -->
    <g transform="translate(0, 25)">
"""
    
    for idx, lang in enumerate(languages):
        y_offset = idx * 45
        pct = lang["percentage"]
        name = lang["name"]
        color = lang["color"]
        
        # Track width is 240px
        bar_width = int((pct / 100) * 240)
        
        svg += f"""      <!-- {name} Bar -->
      <g transform="translate(0, {y_offset})">
        <text x="0" y="8" class="lang-lbl">{name}</text>
        <text x="240" y="8" class="lang-pct" text-anchor="end">{pct:.1f}%</text>
        <rect x="0" y="14" width="240" height="8" rx="2" class="bar-track" />
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
