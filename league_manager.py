import json
import os

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def calculate_standings(teams, matches):
    standings = {team['name']: {
        'pos': 0, 'team': team['name'], 'mp': 0, 'w': 0, 'd': 0, 'l': 0,
        'gp': 0, 'ga': 0, 'gd': 0, 'pts': 0
    } for team in teams}

    completed_matches = [m for m in matches if m['status'] == 'Completed']

    for m in completed_matches:
        t1, t2 = m['team1'], m['team2']
        s1, s2 = m['score1'], m['score2']

        standings[t1]['mp'] += 1
        standings[t2]['mp'] += 1

        # GP is now Goal Difference for the match
        standings[t1]['gp'] += (s1 - s2)
        standings[t2]['gp'] += (s2 - s1)

        if s1 == s2:
            standings[t1]['d'] += 1
            standings[t1]['pts'] += 1
            standings[t2]['d'] += 1
            standings[t2]['pts'] += 1
        else:
            if s1 > s2:
                standings[t1]['w'] += 1
                standings[t1]['pts'] += 3
                standings[t2]['l'] += 1
            else:
                standings[t2]['w'] += 1
                standings[t2]['pts'] += 3
                standings[t1]['l'] += 1
        
        # Keep internal GD synced for logic (though GP is used for display)
        standings[t1]['gd'] = standings[t1]['gp']
        standings[t2]['gd'] = standings[t2]['gp']

    # Sort by Pts, then GD, then GP, then MP (lower MP is better? user didn't say, I'll use MP as tie-breaker too)
    sorted_standings = sorted(standings.values(), key=lambda x: (x['pts'], x['gd'], x['gp'], -x['mp']), reverse=True)
    
    current_pos = 1
    for i, team in enumerate(sorted_standings):
        if i > 0:
            prev = sorted_standings[i-1]
            # Check if tied with previous
            is_tied = (team['pts'] == prev['pts'] and 
                       team['gd'] == prev['gd'] and 
                       team['gp'] == prev['gp'] and 
                       team['mp'] == prev['mp'])
            if not is_tied:
                current_pos = i + 1
        team['pos'] = current_pos
        
    return sorted_standings

def format_scorers_ui(s_list):
    if not s_list: return ""
    counts = {}
    for s in s_list:
        counts[s] = counts.get(s, 0) + 1
    parts = []
    for name, count in counts.items():
        parts.append(f"{name}({count})" if count > 1 else name)
    return ", ".join(parts)

def generate_fixtures_html(matches):
    html = ""
    for m in matches:
        status_class = m['status'].lower()
        locked_overlay = ""
        if m['status'] == "Locked":
            locked_overlay = '<div class="locked-overlay"><i class="fas fa-lock"></i><span>Locked</span></div>'
        elif m['status'] == "Awaiting":
             locked_overlay = '<div class="locked-overlay"><i class="fas fa-lock"></i><span>Awaiting Results</span></div>'

        scorers_html1 = f'<div class="goal-scorers">{format_scorers_ui(m.get("scorers1", []))}</div>' if m.get("scorers1") else ""
        scorers_html2 = f'<div class="goal-scorers">{format_scorers_ui(m.get("scorers2", []))}</div>' if m.get("scorers2") else ""

        status_label_class = f"status-{m['status'].lower()}"
        stage_class = f"stage-{m['stage'].lower().replace(' ', '-')}"

        penalty_html = ""
        vs_content = f"{m['score1']} - {m['score2']}" if m['status'] == 'Completed' else "VS"
        
        # Special handling for Final with Penalties
        if m['stage'] == 'Final' and m['status'] == 'Completed' and (m.get('penalty1') or m.get('penalty2')):
            p1_raw = m.get('penalty1', '0')
            p2_raw = m.get('penalty2', '0')
            # Extract just the numbers for the vs-box
            import re
            p1_num = re.search(r'(\d+)', str(p1_raw)).group(1) if re.search(r'(\d+)', str(p1_raw)) else "0"
            p2_num = re.search(r'(\d+)', str(p2_raw)).group(1) if re.search(r'(\d+)', str(p2_raw)) else "0"
            vs_content = f"{m['score1']} - {m['score2']}<br><span style='font-size: 0.9rem; opacity: 0.9;'>(Pen: {p1_num}-{p2_num})</span>"
            
            # Show full penalty names as "scorers"
            scorers_html1 = f'<div class="goal-scorers" style="color: #FFD700; font-weight: bold;">{p1_raw}</div>'
            scorers_html2 = f'<div class="goal-scorers" style="color: #FFD700; font-weight: bold;">{p2_raw}</div>'
        elif m.get('penalty1') or m.get('penalty2'):
            p1 = m.get('penalty1', '0')
            p2 = m.get('penalty2', '0')
            penalty_html = f'<div class="penalty-score" style="text-align: center; font-family: \'Barlow Condensed\', sans-serif; font-size: 1.1rem; color: #fff; margin-top: 10px; background: rgba(255,255,255,0.1); padding: 5px; border-radius: 4px;">Penalties: {p1} - {p2}</div>'

        # Adjust vs-box width for penalty text
        vs_style = 'style="min-width: 150px; font-size: 1.2rem;"' if "Penalties" in vs_content else ""

        html += f"""
                <div class="fixture-card reveal {status_class} {stage_class}">
                    <div class="fixture-header">
                        <span class="fixture-date">{m['date']}</span>
                        <span>{m['time']} ({m['session']})</span>
                    </div>
                    <div class="fixture-main">
                        <div class="match-teams">
                            <div class="team-side">
                                <div class="team-name">{m['team1']}</div>
                                {scorers_html1}
                            </div>
                            <div class="vs-box" {vs_style}>{vs_content}</div>
                            <div class="team-side">
                                <div class="team-name">{m['team2']}</div>
                                {scorers_html2}
                            </div>
                        </div>
                        {penalty_html}
                    </div>
                    <div class="fixture-footer">
                        <div class="match-meta">
                            <span><i class="fas fa-trophy"></i> {m['stage']}</span>
                            <span class="{status_label_class}"><i class="fas fa-circle-info"></i> {m['status']}</span>
                        </div>
                    </div>
                    {locked_overlay}
                </div>"""
    return html

def generate_standings_html(standings):
    html = ""
    for team in standings:
        zone_class = ""
        if team['pos'] == 1: zone_class = "zone-final"
        elif team['pos'] in [2, 3]: zone_class = "zone-sf"
        
        html += f"""
                        <tr class="{zone_class}">
                            <td class="pos">{team['pos']}</td>
                            <td class="team-cell">{team['team']}</td>
                            <td class="stat">{team['mp']}</td>
                            <td class="stat">{team['w']}</td>
                            <td class="stat">{team['d']}</td>
                            <td class="stat">{team['l']}</td>
                            <td class="stat">{team['gp']}</td>
                            <td class="pts">{team['pts']}</td>
                        </tr>"""
    return html

def generate_squads_html(teams):
    html = ""
    for t in teams:
        players_html = ""
        # Sort players: Captain first
        sorted_players = sorted(t['players'], key=lambda p: p.get('isCaptain', False), reverse=True)
        for i, p in enumerate(sorted_players, 1):
            star_class = "star-captain" if p.get('isCaptain') else ""
            players_html += f"""
                                <div class="player-item {star_class}"><span class="player-num">{i}</span> {p['name']}</div>"""
        
        html += f"""
                <div class="squad-card reveal">
                    <div class="squad-card-inner">
                        <div class="squad-front glass-card">
                            <div class="squad-accent" style="background: {t['accent']};"></div>
                            <div class="squad-logo-placeholder">{t['name'][0]}</div>
                            <div class="squad-name-main">{t['name']}</div>
                            <div class="captain-badge">{t['captain']} (C)</div>
                            <div class="player-count">{len(t['players'])} Official Players</div>
                            <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 10px;">Click to view roster</p>
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
    return html

def calculate_top_scorers(matches, teams, standings):
    def clean_name(n):
        return n.split(' (')[0].strip()

    # Map player to team and team MP
    player_to_team = {}
    team_mp = {s['team']: s['mp'] for s in standings}
    for t in teams:
        for p in t['players']:
            player_to_team[clean_name(p['name'])] = t['name']

    scorers = {}
    for m in matches:
        if m['status'] == 'Completed':
            for s in m.get('scorers1', []):
                if "(OG)" not in s:
                    scorers[s] = scorers.get(s, 0) + 1
            for s in m.get('scorers2', []):
                if "(OG)" not in s:
                    scorers[s] = scorers.get(s, 0) + 1
    
    # Format: list of {'name', 'goals', 'mp'}
    scorer_list = []
    for name, goals in scorers.items():
        team = player_to_team.get(clean_name(name))
        mp = team_mp.get(team, 0) if team else 0
        scorer_list.append({'name': name, 'goals': goals, 'mp': mp})

    # Sort by goals (desc), then MP (desc)
    sorted_scorers = sorted(scorer_list, key=lambda x: (-x['goals'], x['mp']))
    return sorted_scorers

def generate_top_scorers_html(scorers):
    if not scorers:
        return """
            <div class="empty-state reveal">
                <i class="fas fa-futbol fa-bounce"></i>
                <h3>No goals scored yet</h3>
                <p>The leaderboard will light up once the first whistle blows. Check back after Match 1!</p>
                <button class="btn-expand" disabled>Show All Scorers</button>
            </div>"""
    
    rows = ""
    current_rank = 1
    for i, s in enumerate(scorers):
        if i > 0:
            prev = scorers[i-1]
            if not (s['goals'] == prev['goals'] and s['mp'] == prev['mp']):
                current_rank = i + 1
        
        rank_icon = ""
        if current_rank == 1: rank_icon = '<i class="fas fa-crown" style="color: var(--gold); margin-right: 10px;"></i>'
        
        row_class = "hidden-row" if i >= 5 else ""
        
        rows += f"""
                    <tr class="{row_class}">
                        <td class="pos">{current_rank}</td>
                        <td class="team-cell">{rank_icon}{s['name']}</td>
                        <td class="stat" style="text-align: center;">{s['mp']}</td>
                        <td class="pts" style="text-align: center;">{s['goals']}</td>
                    </tr>"""
    
    toggle_btn = ""
    if len(scorers) > 5:
        toggle_btn = f"""
                <div class="table-actions reveal">
                    <button id="toggle-scorers" class="btn-show-more">
                        <span>Show All Scorers</span>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>"""

    return f"""
                <div class="table-responsive reveal" id="scorers-table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th class="pos">Rank</th>
                                <th>Player</th>
                                <th class="stat">MP</th>
                                <th class="pts" style="text-align: center;">Goals</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows}
                        </tbody>
                    </table>
                </div>
                {toggle_btn}"""
def main():
    teams = load_json('teams.json')
    matches = load_json('matches.json')
    
    if not teams or not matches:
        print("Error: Missing data files.")
        return

    # Add Semis and Final placeholders if not present
    if not any(m['stage'] == 'Semifinal' for m in matches):
        matches.append({
            "id": "sf", "date": "TBD", "time": "TBD", "session": "TBD",
            "team1": "2nd Place", "team2": "3rd Place", "score1": 0, "score2": 0,
            "status": "Locked", "stage": "Semifinal"
        })
        matches.append({
            "id": "final", "date": "TBD", "time": "TBD", "session": "TBD",
            "team1": "1st Place", "team2": "SF Winner", "score1": 0, "score2": 0,
            "status": "Locked", "stage": "Grand Final"
        })

    standings = calculate_standings(teams, matches)
    top_scorers = calculate_top_scorers(matches, teams, standings)
    
    # Generate HTML chunks
    fixtures_html = generate_fixtures_html(matches)
    standings_html = generate_standings_html(standings)
    squads_html = generate_squads_html(teams)
    scorers_html = generate_top_scorers_html(top_scorers)
    
    # Generate Highlights Ticker
    highlights_text = "UMFA LEAGUE - 1 IS COMPLETED | WAIT FOR LEAGUE 2 | "
    latest_completed = [m for m in matches if m['status'] == 'Completed']
    if latest_completed:
        latest = max(latest_completed, key=lambda x: int(x['id']))
        match_label = f"MATCH {latest['id']}" if latest['stage'] == 'League Match' else latest['stage'].upper()
        scorers_info = f" | SCORERS: {latest['team1']} - {format_scorers_ui(latest.get('scorers1', []))} | {latest['team2']} - {format_scorers_ui(latest.get('scorers2', []))}"
        highlights_text += f"LATEST RESULT: {match_label} - {latest['team1']} {latest['score1']} - {latest['score2']} {latest['team2']}{scorers_info} | "
    
    next_match = next((m for m in matches if m['status'] == 'Upcoming'), None)
    if next_match:
        highlights_text += f"NEXT UP: {next_match['team1']} VS {next_match['team2']} ({next_match['date']} {next_match['time']}) | "
    
    highlights_text += "MITS COLLEGE PLAYGROUND | DESIGNED FOR CHAMPIONS"

    completed_league = len([m for m in matches if m['status'] == 'Completed' and m['stage'] == 'League Match'])
    any_sf_upcoming = any(m['status'] != 'Locked' and m['stage'] == 'Semifinal' for m in matches)
    any_sf_completed = any(m['status'] == 'Completed' and m['stage'] == 'Semifinal' for m in matches)
    any_final_upcoming = any(m['status'] != 'Locked' and m['stage'] == 'Final' for m in matches)
    any_final_completed = any(m['status'] == 'Completed' and m['stage'] == 'Final' for m in matches)

    stage_group_active = "active"
    stage_sf_active = "active" if (completed_league >= 10 or any_sf_upcoming or any_sf_completed) else ""
    stage_final_active = "active" if (any_sf_completed or any_final_upcoming or any_final_completed) else ""
    stage_champion_active = "active" if any_final_completed else ""

    # Progress bar percentage (10 league + 1 SF + 1 Final = 12 matches)
    total_matches = 12
    completed_total = len([m for m in matches if m['status'] == 'Completed'])
    progress_percent = (completed_total / total_matches) * 100

    # Identify Champion and Runner Up
    final_match = next((m for m in matches if m['stage'] == 'Final'), None)
    champion_name = "TBD"
    runner_up_name = "TBD"
    
    if final_match and final_match['status'] == 'Completed':
        # Logic to determine winner from penalties if score is tied
        p1_score = 0
        p2_score = 0
        if final_match.get('penalty1'):
            import re
            p1_match = re.search(r'(\d+)', final_match['penalty1'])
            if p1_match: p1_score = int(p1_match.group(1))
        if final_match.get('penalty2'):
            import re
            p2_match = re.search(r'(\d+)', final_match['penalty2'])
            if p2_match: p2_score = int(p2_match.group(1))
            
        if final_match['score1'] > final_match['score2'] or p1_score > p2_score:
            champion_name = final_match['team1']
            runner_up_name = final_match['team2']
        elif final_match['score2'] > final_match['score1'] or p2_score > p1_score:
            champion_name = final_match['team2']
            runner_up_name = final_match['team1']

    # Load template
    if not os.path.exists('template.html'):
        print("Error: template.html not found.")
        return
        
    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    # Replace placeholders
    output = template.replace('{{FIXTURES}}', fixtures_html)
    output = output.replace('{{STAGE_CHAMPION_ACTIVE}}', stage_champion_active)
    output = output.replace('{{CHAMPION_NAME}}', champion_name)
    output = output.replace('{{RUNNER_UP_NAME}}', runner_up_name)
    output = output.replace('{{STANDINGS}}', standings_html)
    output = output.replace('{{SQUADS}}', squads_html)
    output = output.replace('{{TOP_SCORERS}}', scorers_html)
    output = output.replace('{{HIGHLIGHTS}}', highlights_text)

    # Write final HTML
    with open('umfa.html', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Successfully updated umfa.html. Progress: {completed_league}/10 matches.")

if __name__ == "__main__":
    main()
