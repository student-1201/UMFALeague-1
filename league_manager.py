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
        'gf': 0, 'ga': 0, 'gd': 0, 'pts': 0
    } for team in teams}

    completed_matches = [m for m in matches if m['status'] == 'Completed']

    for m in completed_matches:
        t1, t2 = m['team1'], m['team2']
        s1, s2 = m['score1'], m['score2']

        standings[t1]['mp'] += 1
        standings[t2]['mp'] += 1
        standings[t1]['gf'] += s1
        standings[t1]['ga'] += s2
        standings[t2]['gf'] += s2
        standings[t2]['ga'] += s1
        standings[t1]['gd'] = standings[t1]['gf'] - standings[t1]['ga']
        standings[t2]['gd'] = standings[t2]['gf'] - standings[t2]['ga']

        if s1 > s2:
            standings[t1]['w'] += 1
            standings[t1]['pts'] += 3
            standings[t2]['l'] += 1
        elif s2 > s1:
            standings[t2]['w'] += 1
            standings[t2]['pts'] += 3
            standings[t1]['l'] += 1
        else:
            standings[t1]['d'] += 1
            standings[t1]['pts'] += 1
            standings[t2]['d'] += 1
            standings[t2]['pts'] += 1

    # Sort by Pts, then GD, then GF
    sorted_standings = sorted(standings.values(), key=lambda x: (x['pts'], x['gd'], x['gf']), reverse=True)
    
    for i, team in enumerate(sorted_standings):
        team['pos'] = i + 1
        
    return sorted_standings

def generate_fixtures_html(matches):
    html = ""
    for m in matches:
        status_class = "locked" if m['status'] == "Locked" else ""
        locked_overlay = ""
        if m['status'] == "Locked":
            locked_overlay = '<div class="locked-overlay"><i class="fas fa-lock"></i><span>Locked</span></div>'
        elif m['status'] == "Awaiting":
             locked_overlay = '<div class="locked-overlay"><i class="fas fa-lock"></i><span>Awaiting Results</span></div>'

        html += f"""
                <div class="fixture-card reveal {status_class}">
                    <div class="fixture-header">
                        <span class="fixture-date">{m['date']}</span>
                        <span>{m['time']} ({m['session']})</span>
                    </div>
                    <div class="fixture-main">
                        <div class="match-teams">
                            <div class="team-side"><div class="team-name">{m['team1']}</div></div>
                            <div class="vs-box">{"VS" if m['status'] != 'Completed' else f"{m['score1']} - {m['score2']}"}</div>
                            <div class="team-side"><div class="team-name">{m['team2']}</div></div>
                        </div>
                    </div>
                    <div class="fixture-footer">
                        <div class="match-meta">
                            <span><i class="fas fa-trophy"></i> {m['stage']}</span>
                            <span><i class="fas fa-circle-info"></i> {m['status']}</span>
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
                            <td class="stat">{team['gf']}</td>
                            <td class="stat">{team['ga']}</td>
                            <td class="stat">{team['gd']}</td>
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
    
    # Generate HTML chunks
    fixtures_html = generate_fixtures_html(matches)
    standings_html = generate_standings_html(standings)
    squads_html = generate_squads_html(teams)
    
    completed_count = len([m for m in matches if m['status'] == 'Completed' and m['stage'] == 'League Match'])
    progress_percent = (completed_count / 10) * 100

    # Load template
    if not os.path.exists('template.html'):
        print("Error: template.html not found.")
        return
        
    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    # Replace placeholders
    output = template.replace('{{FIXTURES}}', fixtures_html)
    output = output.replace('{{STANDINGS}}', standings_html)
    output = output.replace('{{SQUADS}}', squads_html)
    output = output.replace('{{COMPLETED_MATCHES}}', str(completed_count))
    output = output.replace('{{PROGRESS_PERCENT}}', str(progress_percent))

    # Write final HTML
    with open('umfa.html', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Successfully updated umfa.html. Progress: {completed_count}/10 matches.")

if __name__ == "__main__":
    main()
