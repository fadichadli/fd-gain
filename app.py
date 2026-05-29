import streamlit as st
import requests
from typing import List, Dict

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

if 'api_remaining' not in st.session_state:
    st.session_state['api_remaining'] = "Non vérifié"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:linear-gradient(135deg, #07090f 0%, #0a0e1a 100%); color:#e8eaf0; }
.block-container { padding:2rem 2.5rem; max-width:1400px; }
.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3.5rem; color:#00e5a0; letter-spacing:0.15em; }
.wh-sub { color:#3a4a6a; font-size:0.9rem; }
.pack-card { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:2px solid #ffd700; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 8px 32px rgba(255,215,0,0.3); position:relative; }
.pack-badge { position:absolute; top:16px; right:16px; background:linear-gradient(135deg, #ffd700 0%, #ffb700 100%); color:#07090f; font-family:'Bebas Neue'; font-size:2rem; padding:10px 20px; border-radius:8px; font-weight:700; box-shadow:0 4px 16px rgba(255,215,0,0.5); }
.pack-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
.pack-name { font-family:'Bebas Neue'; font-size:2.2rem; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,0.5); }
.pack-meta { font-size:0.85rem; color:#6b7a9a; margin-top:8px; }
.sel-row { background:linear-gradient(90deg, #111827 0%, #1a2332 100%); border:1px solid #2a3550; border-left:5px solid #ffd700; border-radius:10px; padding:18px; margin-top:12px; }
.sel-league { font-size:0.75rem; color:#ffd700; font-weight:700; text-transform:uppercase; }
.sel-match { font-weight:700; font-size:1.1rem; color:#fff; margin:10px 0; }
.sel-details { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.badge { font-size:0.75rem; font-weight:700; padding:5px 14px; border-radius:20px; border:2px solid; background:rgba(255,215,0,0.1); }
.b-h2h { color:#ffd700; border-color:#ffd700; }
.cote-pill { font-family:'Bebas Neue'; font-size:1.6rem; background:linear-gradient(135deg, #ffd700 0%, #ffb700 100%); color:#07090f; padding:6px 18px; border-radius:8px; font-weight:700; }
.stat-box { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:1px solid #2a3550; border-radius:12px; padding:20px; text-align:center; }
.stat-val { font-family:'Bebas Neue'; font-size:2.6rem; color:#ffd700; }
.stat-lbl { font-size:0.8rem; color:#5a6a8a; margin-top:6px; }
.pack-off { background:#0a0d15; border:2px dashed #2a3550; border-radius:16px; padding:24px; color:#4a5570; text-align:center; }
.rec-row { background:#0f1623; border:1px solid #2a3550; border-radius:10px; padding:16px; margin-bottom:10px; }
.sidebar-success { color:#ffd700; font-weight:600; }
</style>
""", unsafe_allow_html=True)

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 8, 12]

@st.cache_data(ttl=3600, show_spinner=False)
def get_active_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            data = r.json()
            soccer_leagues = [s for s in data if s.get('group') == 'Soccer' and not s.get('has_outrights')]
            return soccer_leagues
    except:
        pass
    return []

@st.cache_data(ttl=300, show_spinner=False)
def check_api_health():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
        return {'status': r.status_code == 200, 'remaining': r.headers.get('x-requests-remaining', 'N/A')}
    except:
        return {'status': False, 'remaining': 'N/A'}

def fetch_all_matches_optimized(leagues_list):
    all_selections = []
    logs = []
    stats = {'ligues': 0, 'succes': 0, 'echec': 0, 'matchs_total': 0}
    
    if not leagues_list:
        return [], ["Aucune ligue"], stats
    
    pb = st.progress(0, text="🔍 Scan maximisé...")
    
    for idx, ligue in enumerate(leagues_list):
        ligue_key = ligue['key']
        nom_court = ligue_key.replace('soccer_', '').replace('_', ' ').upper()
        stats['ligues'] += 1
        
        url = f'https://api.the-odds-api.com/v4/sports/{ligue_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&bookmakers=all&oddsFormat=decimal'
        
        try:
            r = requests.get(url, timeout=15)
            
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            
            if r.status_code == 200:
                data = r.json()
                
                if isinstance(data, list) and len(data) > 0:
                    logs.append(f"🟢 {nom_court}: {len(data)} matchs")
                    stats['succes'] += 1
                    stats['matchs_total'] += len(data)
                    
                    for match in data:
                        match_id = match['id']
                        home = match.get('home_team', 'Inconnu')
                        away = match.get('away_team', 'Inconnu')
                        
                        best_outcomes = {}
                        
                        for bk in match.get('bookmakers', []):
                            for mkt in bk.get('markets', []):
                                if mkt.get('key') != 'h2h':
                                    continue
                                
                                for out in mkt.get('outcomes', []):
                                    name = out.get('name', '')
                                    cote = out.get('price', 0)
                                    
                                    if name not in best_outcomes or cote > best_outcomes[name]:
                                        best_outcomes[name] = cote
                        
                        for name, cote in best_outcomes.items():
                            if cote < 1.25 or cote > 3.80:
                                continue
                            
                            prob = round((1/cote)*100, 1)
                            
                            if prob < 42:
                                continue
                            
                            if name.lower() == 'draw':
                                prono = "Nul"
                            elif name == home:
                                prono = f"1 - {home}"
                            elif name == away:
                                prono = f"2 - {away}"
                            else:
                                continue
                            
                            all_selections.append({
                                'match_id': match_id,
                                'match': f"{home} vs {away}",
                                'league': nom_court,
                                'mkt': 'h2h',
                                'mkt_lbl': '1X2',
                                'mkt_css': 'b-h2h',
                                'prono': prono,
                                'cote': cote,
                                'prob': prob,
                                'confidence': 'high' if prob >= 58 else 'medium' if prob >= 50 else 'low'
                            })
                else:
                    logs.append(f"⚪ {nom_court}: 0 matchs")
            else:
                logs.append(f"🔴 {nom_court}: Erreur {r.status_code}")
                stats['echec'] += 1
        
        except Exception as e:
            logs.append(f"💥 {nom_court}: Erreur")
            stats['echec'] += 1
        
        pb.progress((idx + 1) / len(leagues_list))
    
    pb.empty()
    
    all_selections.sort(key=lambda x: (x['prob'], x['cote']), reverse=True)
    
    return all_selections, logs, stats

def generer_pack_sans_repetition(selections, cible):
    if not selections:
        return [], 0.0, 0.0
    
    ticket = []
    cote_total = 1.0
    matches_used = set()
    leagues_used = set()
    
    for s in selections:
        if s['match_id'] in matches_used:
            continue
        
        if s['league'] in leagues_used:
            continue
        
        ticket.append(s)
        cote_total *= s['cote']
        matches_used.add(s['match_id'])
        leagues_used.add(s['league'])
        
        if cote_total >= cible * 0.90:
            break
    
    if cote_total >= cible * 0.50:
        avg_prob = round(sum(s['prob'] for s in ticket) / len(ticket), 1)
        return ticket, round(cote_total, 2), avg_prob
    return [], 0.0, 0.0

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Contrôle")
    
    api_health = check_api_health()
    if api_health['status']:
        st.markdown("<div class='sidebar-success'>✅ API Opérationnelle</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-success'>📊 {api_health['remaining']} requêtes</div>", unsafe_allow_html=True)
    else:
        st.markdown("❌ API Hors ligne", unsafe_allow_html=True)
    
    st.divider()
    
    active_leagues = get_active_leagues()
    
    if active_leagues:
        options_leagues = {l['key']: l['title'] for l in active_leagues}
        default_sel = list(options_leagues.keys())[:20]
        
        leagues_choisies = st.multiselect(
            "🏆 Ligues (20 sélectionnées par défaut)",
            options=list(options_leagues.keys()),
            default=default_sel,
            format_func=lambda x: options_leagues[x]
        )
        
        st.success(f"💡 {len(active_leagues)} ligues disponibles → {len(leagues_choisies)} sélectionnées")
    else:
        st.error("❌ Échec récupération ligues")
        leagues_choisies = []
    
    st.divider()
    st.markdown(f"💳 **Quota :** `{st.session_state['api_remaining']}`")
    
    if st.button("↻ LANCER SCAN MAXIMISÉ", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #2a3550;padding-bottom:1.2rem;margin-bottom:1.8rem">
  <span class="wh-title">BETCORE AI GOLD v5.0</span><br>
  <span class="wh-sub">20+ ligues · Meilleures cotes · ZÉRO répétition</span>
</div>
""", unsafe_allow_html=True)

if not leagues_choisies:
    st.info("💡 Sélectionnez des ligues")
    st.stop()

# ─── ANALYSE ──────────────────────────────────────────────────────────────────
with st.spinner(f"🔍 Scan de {len(leagues_choisies)} ligues..."):
    sels, logs, stats = fetch_all_matches_optimized([l for l in active_leagues if l['key'] in leagues_choisies])

# DEBUG
with st.expander("🔍 DEBUG - Stats complètes", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Ligues scannées", f"{stats['ligues']}")
    with c2: st.metric("Succès", f"{stats['succes']} ✓")
    with c3: st.metric("Échecs", f"{stats['echec']} 🔴")
    with c4: st.metric("Matchs totaux", f"{stats['matchs_total']}")
    
    st.divider()
    for log in logs[:20]:
        if "🟢" in log:
            st.success(log)
        elif "🔴" in log or "💥" in log:
            st.error(log)
        else:
            st.info(log)

if not sels:
    st.error(f"""
    ❌ **AUCUNE SÉLECTION**
    
    Quota API: `{st.session_state['api_remaining']}`
    
    **Solutions :**
    ✅ Clique **↻ LANCER SCAN**
    ✅ Choisis **20+ ligues**
    """)
    st.stop()

# STATS
unique_matches = len(set(s["match_id"] for s in sels))
unique_leagues = len(set(s["league"] for s in sels))
high_conf = len([s for s in sels if s['confidence'] == 'high'])
avg_prob = round(sum(s["prob"] for s in sels) / len(sels), 1)

c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_matches}</div><div class="stat-lbl">Matchs</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="stat-box"><div class="stat-val">{len(sels)}</div><div class="stat-lbl">Options</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_leagues}</div><div class="stat-lbl">Ligues</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="stat-box"><div class="stat-val">{high_conf}</div><div class="stat-lbl">Haute Conf</div></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="stat-box"><div class="stat-val">@{avg_prob}%</div><div class="stat-lbl">Prob Moy</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# PACKS
st.markdown("### 🎯 PACKS OPTIMISÉS - ZÉRO Répétition")

packs_generes = 0
col_gauche, col_droite = st.columns([3, 2], gap="large")

with col_gauche:
    for cible in PACK_CIBLES:
        tk, total_cote, avg_prob_pack = generer_pack_sans_repetition(sels, cible)
        
        if not tk:
            st.markdown(f'<div class="pack-off">📦 <b>PACK ×{cible}</b> — Indisponible</div>', unsafe_allow_html=True)
            continue
        
        packs_generes += 1
        
        st.markdown(f'''
        <div class="pack-card">
            <div class="pack-badge">{total_cote}×</div>
            <div class="pack-top">
                <div>
                    <div class="pack-name">🎯 PACK GOLD ×{cible}</div>
                    <div class="pack-meta">
                        <strong>{len(tk)} matchs</strong> · {avg_prob_pack}% confiance · 
                        {len(set(s["match_id"] for s in tk))} uniques · 
                        {len(set(s["league"] for s in tk))} ligues
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        for i, s in enumerate(tk, 1):
            st.markdown(f'''
            <div class="sel-row">
                <div class="sel-league">#{i} {s['league']}</div>
                <div class="sel-match">{s['match']}</div>
                <div class="sel-details">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="color:#c8d0e0;font-weight:600">👉 {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                    <span style="color:#5a6a8a;font-size:0.75rem;">({s['prob']}%)</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with col_droite:
    st.markdown("### 🔥 TOP 20")
    for i, s in enumerate(sels[:20], 1):
        st.markdown(f'''
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-weight:700;color:#ffd700">#{i} {s['match']}</span>
                <span class="cote-pill" style="font-size:1.2rem">@{s['cote']}</span>
            </div>
            <div style="font-size:0.75rem;color:#ffd700;margin:6px 0;font-weight:700;">{s['league']}</div>
            <div style="display:flex;gap:10px;align-items:center;">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="color:#fff;font-weight:600;">🎯 {s['prono']}</span>
                <span style="color:#5a6a8a;font-size:0.8rem;">({s['prob']}%)</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.success(f"✅ {packs_generes}/{len(PACK_CIBLES)} packs | {len(sels)} sélections | {unique_matches} matchs | {high_conf} haute confiance")
