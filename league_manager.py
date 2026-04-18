import json
import os
from datetime import datetime, timedelta

# Configuration
TEAMS_FILE = 'teams.json'
RESULTS_FILE = 'results.json'
TEMPLATE_FILE = 'template.html'
OUTPUT_FILE = 'umfa.html'

def load_data():
    with open(TEAMS_FILE, 'r') as f:
        teams_data = json.load(f)
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            results_data = json.load(f)
    else:
        results_data = {"matches": []}
    return teams_data, results_data

def save_results(results_data):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results_data, f, indent=4)

def generate_fixtures(teams):
    """Generates Round Robin fixtures using the Circle Method."""
    team_names = [t['name'] for t in teams]
    if len(team_names) % 2 != 0:
        team_names.append("BYE")
        
    n = len(team_names)
    fixtures = []
    
    # Rotation logic
    temp_teams = list(team_names)
    
    for round_num in range(n - 1):
        for i in range(n // 2):
            t1 = temp_teams[i]
            t2 = temp_teams[n - 1 - i]
            
            if t1 != "BYE" and t2 != "BYE":
                fixtures.append({
                    "id": f"match_{len(fixtures) + 1}",
                    "team1": t1,
                    "team2": t2,
                    "round": round_num + 1,
                    "score1": None,
                    "score2": None
                })
        
        # Rotate: keep first, move last to second
        temp_teams = [temp_teams[0]] + [temp_teams[-1]] + temp_teams[1:-1]
        
    return fixtures

def get_match_schedule(fixtures, start_date_str):
    """Assigns dates and slots (Morning/Evening) to fixtures."""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    scheduled = []
    
    for i, f in enumerate(fixtures):
        days_offset = i // 2
        is_evening = i % 2 != 0
        match_date = start_date + timedelta(days=days_offset)
        
        f["date"] = match_date.strftime("%a %b %d")
        f["time"] = "04:00 PM (Evening)" if is_evening else "06:30 AM (Morning)"
        scheduled.append(f)
        
    return scheduled

def calculate_standings(teams, matches):
    """Points Engine: Processes matches to calculate full standings."""
    stats = {t['name']: {
        "name": t['name'],
        "mp": 0, "w": 0, "d": 0, "l": 0, 
        "gf": 0, "ga": 0, "gd": 0, "pts": 0
    } for t in teams}
    
    for m in matches:
        if m['score1'] is not None and m['score2'] is not None:
            t1, t2 = m['team1'], m['team2']
            s1, s2 = int(m['score1']), int(m['score2'])
            
            stats[t1]["mp"] += 1
            stats[t2]["mp"] += 1
            stats[t1]["gf"] += s1
            stats[t2]["gf"] += s2
            stats[t1]["ga"] += s2
            stats[t2]["ga"] += s1
            
            if s1 > s2:
                stats[t1]["w"] += 1
                stats[t1]["pts"] += 3
                stats[t2]["l"] += 1
            elif s2 > s1:
                stats[t2]["w"] += 1
                stats[t2]["pts"] += 3
                stats[t1]["l"] += 1
            else:
                stats[t1]["d"] += 1
                stats[t2]["d"] += 1
                stats[t1]["pts"] += 1
                stats[t2]["pts"] += 1
                
    # Calculate GD
    for s in stats.values():
        s["gd"] = s["gf"] - s["ga"]
        
    # Sort: Points > GD > GF
    sorted_stats = sorted(stats.values(), key=lambda x: (x['pts'], x['gd'], x['gf']), reverse=True)
    return sorted_stats

def render_html(teams_data, standings, matches):
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()
    
    # 1. Basic Info
    t_info = teams_data['tournament']
    template = template.replace('{{title}}', t_info['name'])
    template = template.replace('{{title_main}}', 'UMFA League 1')
    template = template.replace('{{title_split}}', 'UMFA<span>.</span>League<span>.</span>1')
    template = template.replace('{{subtitle}}', t_info['subtitle'])
    template = template.replace('{{organizer}}', t_info['organizer'])
    template = template.replace('{{organizer_full}}', "Union of MITS Football Associations")
    template = template.replace('{{venue}}', t_info['venue'])
    template = template.replace('{{venue_short}}', "MITS College")
    template = template.replace('{{badge_text}}', "MITS College Premiere")
    template = template.replace('{{status}}', "IN PROGRESS")
    
    # 2. Progress Tracker
    completed = sum(1 for m in matches if m['score1'] is not None)
    total = len(matches)
    percent = (completed / total * 100) if total > 0 else 0
    template = template.replace('{{progress_percent}}', str(int(percent)))
    template = template.replace('{{progress_text}}', f"{completed} / {total} Group Matches Completed")
    
    # 3. Fixtures
    fixtures_html = ""
    for m in matches:
        score_display = f"{m['score1']} - {m['score2']}" if m['score1'] is not None else "VS"
        status_text = "Completed" if m['score1'] is not None else "Upcoming"
        fixtures_html += f"""
                <div class="fixture-card reveal">
                    <div class="fixture-header">
                        <span class="fixture-date">{m['date']}</span>
                        <span>{m['time']}</span>
                    </div>
                    <div class="fixture-main">
                        <div class="match-teams">
                            <div class="team-side"><div class="team-name">{m['team1']}</div></div>
                            <div class="vs-box">{score_display}</div>
                            <div class="team-side"><div class="team-name">{m['team2']}</div></div>
                        </div>
                    </div>
                    <div class="fixture-footer">
                        <div class="match-meta">
                            <span><i class="fas fa-trophy"></i> League Match</span>
                            <span><i class="fas fa-circle-info"></i> {status_text}</span>
                        </div>
                    </div>
                </div>"""
                
    # Add locked Semifinal/Final placeholders
    fixtures_html += """
                <div class="fixture-card reveal locked">
                    <div class="fixture-header"><span>TBD</span><span>TBD</span></div>
                    <div class="fixture-main">
                        <div class="match-teams">
                            <div class="team-side"><div class="team-name">2nd Place</div></div>
                            <div class="vs-box">VS</div>
                            <div class="team-side"><div class="team-name">3rd Place</div></div>
                        </div>
                    </div>
                    <div class="fixture-footer"><div class="match-meta"><span><i class="fas fa-lock"></i> Semifinal</span></div></div>
                </div>
                <div class="fixture-card reveal locked">
                    <div class="fixture-header"><span>TBD</span><span>TBD</span></div>
                    <div class="fixture-main">
                        <div class="match-teams">
                            <div class="team-side"><div class="team-name">1st Place</div></div>
                            <div class="vs-box">VS</div>
                            <div class="team-side"><div class="team-name">SF Winner</div></div>
                        </div>
                    </div>
                    <div class="fixture-footer"><div class="match-meta"><span><i class="fas fa-crown"></i> Grand Final</span></div></div>
                </div>"""
    template = template.replace('{{fixtures_placeholder}}', fixtures_html)
    
    # 4. Points Table
    table_html = ""
    for i, s in enumerate(standings):
        zone_class = ""
        if i == 0: zone_class = "zone-final"
        elif i in [1, 2]: zone_class = "zone-sf"
        
        table_html += f"""
                        <tr class="{zone_class}">
                            <td class="pos">{i+1}</td>
                            <td class="team-cell">{s['name']}</td>
                            <td class="stat">{s['mp']}</td>
                            <td class="stat">{s['w']}</td>
                            <td class="stat">{s['d']}</td>
                            <td class="stat">{s['l']}</td>
                            <td class="stat">{s['gf']}</td>
                            <td class="stat">{s['ga']}</td>
                            <td class="stat">{s['gd']}</td>
                            <td class="pts">{s['pts']}</td>
                        </tr>"""
    template = template.replace('{{table_placeholder}}', table_html)
    
    # 5. Squads
    squads_html = ""
    for t in teams_data['teams']:
        players_html = ""
        for p in t['players']:
            is_cap = "star-captain" if p.get('is_captain') else ""
            players_html += f'<div class="player-item {is_cap}"><span class="player-num">{p["num"]}</span> {p["name"]}</div>'
            
        squads_html += f"""
                <div class="squad-card reveal">
                    <div class="squad-card-inner">
                        <div class="squad-front glass-card">
                            <div class="squad-accent" style="background: {t['accent']};"></div>
                            <div class="squad-logo-placeholder">{t['name'][0]}</div>
                            <div class="squad-name-main">{t['name']}</div>
                            <div class="captain-badge">{t['captain']} (C)</div>
                            <div class="player-count">{len(t['players'])} Official Players</div>
                        </div>
                        <div class="squad-back glass-card">
                            <div class="squad-accent" style="background: {t['accent']};"></div>
                            <h4 style="font-family: var(--heading-font); border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px;">{t['name'].upper()} ROSTER</h4>
                            <div class="squad-list">
                                {players_html}
                            </div>
                        </div>
                    </div>
                </div>"""
    template = template.replace('{{squads_placeholder}}', squads_html)
    
    # 6. Scorers (Placeholder)
    template = template.replace('{{scorers_placeholder}}', """
            <div class="empty-state reveal">
                <i class="fas fa-futbol fa-bounce"></i>
                <h3>No goals scored yet</h3>
                <p>Leaderboard updates automatically after match inputs.</p>
                <button class="btn-expand" disabled>Show All Scorers</button>
            </div>""")
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(template)

def main():
    teams_data, results_data = load_data()
    
    standings = calculate_standings(teams_data['teams'], results_data['matches'])
    render_html(teams_data, standings, results_data['matches'])
    print(f"Successfully updated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
