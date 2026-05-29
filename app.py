import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Tuple, Set

st.set_page_config(page_title="WinHand AI - BetCore Platinum", page_icon="⚽", layout="wide")

if 'api_remaining' not in st.session_state:
    st.session_state['api_remaining'] = "Non vérifié"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { 
    font-family:'DM Sans',sans-serif; 
    background:linear-gradient(135deg, #07090f 0%, #0a0e1a 100%); 
    color:#e8eaf0; 
}
.block-container { padding:2rem 2.5rem; max-width:1400px; }
.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3.5rem; color:#00e5a0; letter-spacing:0.15em; text-shadow:0 0 30px rgba(0,229,160,0.4); }
.wh-sub { color:#3a4a6a; font-size:0.9rem; }

/* PACK CARDS - VISIBILITÉ OPTIMALE */
.pack-card { 
    background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); 
    border:2px solid #00e5a0; 
    border-radius:16px; 
    padding:24px 28px; 
    margin-bottom:24px; 
    box-shadow:0 8px 32px rgba(0,229,160,0.2), inset 0 0 40px rgba(0,229,160,0.05);
    position:relative;
    overflow:hidden;
}
.pack-card::before {
    content:'';
    position:absolute;
    top:-50%;
    right:-50%;
    width:200%;
    height:200%;
    background:radial-gradient(circle, rgba(0,229,160,0.08) 0%, transparent 70%);
    animation:pulse 3s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity:0.5; transform:scale(1); }
    50% { opacity:0.8; transform:scale(1.05); }
}
.pack-card.success { border-color:#00e5a0; }
.pack-card.warning { border-color:#ffb400; box-shadow:0 8px 32px rgba(255,180,0,0.2); }
.pack-card.danger { border-color:#ff5a5a; box-shadow:0 8px 32px rgba(255,90,90,0.2); }

.pack-badge {
    position:absolute;
    top:16px;
    right:16px;
    background:linear-gradient(135deg, #00e5a0 0%, #00c98d 100%);
    color:#07090f;
    font-family:'Bebas Neue',sans-serif;
    font-size:1.8rem;
    padding:8px 16px;
    border-radius:8px;
    z-index:10;
    box-shadow:0 4px 12px rgba(0,229,160,0.4);
}
.pack-badge.warning { background:linear-gradient(135deg, #ffb400 0%, #e6a200 100%); color:#07090f; }
.pack-badge.danger { background:linear-gradient(135deg, #ff5a5a 0%, #e04545 100%); color:#fff; }

.pack-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; gap:20px; }
.pack-header { flex:1; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:2rem; letter-spacing:0.1em; color:#fff; margin-bottom:8px; text-shadow:0 2px 10px rgba(0,0,0,0.5); }
.pack-meta { font-size:0.8rem; color:#6b7a9a; line-height:1.6; }
.pack-meta span { margin-right:15px; }
.pack-cote-badge { 
    background:linear-gradient(135deg, #ffd700 0%, #ffb700 100%); 
    color:#07090f;
    font-family:'Bebas Neue',sans-serif; 
    font-size:2.8rem; 
    padding:12px 24px;
    border-radius:12px;
    box-shadow:0 6px 20px rgba(255,215,0,0.4);
    text-shadow:0 2px 8px rgba(0,0,0,0.3);
    white-space:nowrap;
}

/* SELECTION ROWS - HAUTE VISIBILITÉ */
.sel-row { 
    background:linear-gradient(90deg, #111827 0%, #1a2332 100%); 
    border:1px solid #2a3550; 
    border-left:4px solid #00e5a0;
    border-radius:10px; 
    padding:16px 20px; 
    margin-top:12px;
    transition:all 0.3s ease;
    position:relative;
}
.sel-row:hover { 
    background:linear-gradient(90deg, #151d30 0%, #202d40 100%);
    border-color:#00e5a0;
    transform:translateX(5px);
    box-shadow:0 4px 16px rgba(0,229,160,0.2);
}
.sel-league { 
    font-size:0.72rem; 
    color:#00e5a0; 
    margin-bottom:6px;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:0.05em;
}
.sel-match { 
    font-weight:700; 
    font-size:1.05rem; 
    color:#fff; 
    margin-bottom:10px;
    text-shadow:0 1px 4px rgba(0,0,0,0.5);
}
.sel-details { display:flex; align-items:center; gap:12px; margin-top:8px; flex-wrap:wrap; }
.badge { 
    display:inline-block; 
    font-size:0.7rem; 
    font-weight:700; 
    letter-spacing:0.12em; 
    text-transform:uppercase; 
    padding:4px 12px; 
    border-radius:20px;
    border:1px solid;
}
.b-h2h { background:rgba(0,229,160,0.15); color:#00e5a0; border-color:#00e5a0; }
.b-dc { background:rgba(77,159,255,0.15); color:#4d9fff; border-color:#4d9fff; }
.b-btts { background:rgba(255,180,0,0.15); color:#ffb400; border-color:#ffb400; }
.b-over { background:rgba(200,100,255,0.15); color:#c864ff; border-color:#c864ff; }
.b-under { background:rgba(255,90,90,0.15); color:#ff5a5a; border-color:#ff5a5a; }
.prono-text { font-size:0.9rem; color:#c8d0e0; font-weight:600; }
.cote-pill { 
    font-family:'Bebas Neue',sans-serif; 
    font-size:1.4rem; 
    background:linear-gradient(135deg, #00e5a0 0%, #00c98d 100%);
    color:#07090f;
    padding:4px 14px; 
    border-radius:6px; 
    display:inline-block;
    box-shadow:0 3px 10px rgba(0,229,160,0.4);
    font-weight:700;
}
.prob-bar { margin-top:12px; }
.prob-label { font-size:0.68rem; color:#5a6a8a; margin-bottom:4px; display:flex; justify-content:space-between; }
.prob-wrap { background:#0a0f1a; border-radius:4px; height:6px; overflow:hidden; }
.prob-fill { height:6px; border-radius:4px; background:linear-gradient(90deg,#0077ff 0%,#00e5a0 50%,#00ff88 100%); transition:width 0.8s ease; }

/* STATS BOXES */
.stat-box { 
    background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); 
    border:1px solid #2a3550; 
    border-radius:12px; 
    padding:18px; 
    text-align:center;
    box-shadow:0 4px 16px rgba(0,0,0,0.3);
    transition:transform 0.2s;
}
.stat-box:hover { transform:translateY(-3px); box-shadow:0 6px 24px rgba(0,229,160,0.15); }
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2.4rem; color:#00e5a0; line-height:1; margin-bottom:6px; }
.stat-lbl { font-size:0.75rem; color:#5a6a8a; }

/* EMPTY PACK */
.pack-off { 
    background:linear-gradient(135deg, #0a0d15 0%, #0f1420 100%); 
    border:2px dashed #2a3550; 
    border-radius:16px; 
    padding:24px; 
    margin-bottom:20px; 
    color:#4a5570; 
    font-size:0.9rem;
    text-align:center;
}

/* RECOMMENDATIONS */
.rec-row { 
    background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); 
    border:1px solid #2a3550; 
    border-radius:10px; 
    padding:14px 18px; 
    margin-bottom:10px;
    transition:all 0.2s;
}
.rec-row:hover { border-color:#4d9fff; background:#151d30; }
.rec-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.rec-match { font-weight:600; font-size:0.9rem; color:#e8eaf0; }
.rec-league { font-size:0.72rem; color:#5a6a8a; margin:4px 0; }
.rec-details { display:flex; gap:8px; align-items:center; margin-top:8px; }

/* SIDEBAR */
.sidebar-success { color:#00e5a0; font-weight:600; }
.sidebar-error { color:#ff5a5a; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 15]
REQUEST_TIMEOUT = 12

MKT_INFO = {
    'h2h': ('1X2', 'b-h2h'),
    'double_chance': ('Double Chance', 'b-dc'),
    'btts': ('Les 2 Marquent', 'b-btts'),
    'totals_over': ('Over Buts+', 'b-over'),
    'totals_under': ('Under Buts-', 'b-under'),
}

DC_MAP = {
    'HomeOrDraw': '1X (Gagnant ou Nul)',
    'AwayOrDraw': 'X2 (Nul ou Gagnant)',
    'HomeOrAway': '12 (Match non Nul)'
}

# ─── FONCTIONS ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_active_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            return [s for s in r.json() if s.get('group') == 'Soccer' and not s.get('has_outrights')]
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

def fetch_selections_smart(leagues_tuple: Tuple, marches_tuple: Tuple) -> List[Dict]:
    """Algorithme intelligent: priorise haute confiance, diversité, faible corrélation"""
    if not leagues_tuple or not marches_tuple:
        return []
    
    api_mkts = set()
    for m in marches_tuple:
        api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)
    
    dict_selections = {}
    total_leagues = len(leagues_tuple)
    pb = st.progress(0, text="🎯 Analyse intelligente en cours...")
    
    for idx, ligue in enumerate(leagues_tuple):
        nom_court = ligue.replace('soccer_', '').replace('_', ' ').upper()
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        
        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT)
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            
            if r.status_code != 200 or not r.json():
                url_fallback = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal'
                r = requests.get(url_fallback, timeout=REQUEST_TIMEOUT)
            
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    for match in data:
                        match_id = match['id']
                        home = match.get('home_team', 'Inconnu')
                        away = match.get('away_team', 'Inconnu')
                        
                        for bk in match.get('bookmakers', []):
                            for mkt in bk.get('markets', []):
                                mkt_key = mkt.get('key', '')
                                
                                for out in mkt.get('outcomes', []):
                                    cote = out.get('price', 1.0)
                                    name = out.get('name', '')
                                    
                                    if cote <= 1.15 or cote > 5.0:
                                        continue
                                    
                                    local_mkt = mkt_key
                                    prono_final = name
                                    
                                    if mkt_key == 'totals':
                                        point = out.get('point', 2.5)
                                        if name.lower() == 'over':
                                            local_mkt = 'totals_over'
                                            prono_final = f"Over {point}"
                                        elif name.lower() == 'under':
                                            local_mkt = 'totals_under'
                                            prono_final = f"Under {point}"
                                    
                                    if local_mkt not in marches_tuple:
                                        continue
                                    
                                    if local_mkt == 'double_chance':
                                        prono_final = DC_MAP.get(name, name)
                                    elif local_mkt == 'btts':
                                        prono_final = "Oui" if name.lower() == 'yes' else "Non"
                                    elif local_mkt == 'h2h':
                                        if name.lower() == 'draw':
                                            prono_final = "Nul"
                                        elif name == home:
                                            prono_final = f"1 ({home})"
                                        elif name == away:
                                            prono_final = f"2 ({away})"
                                    
                                    prob = round((1/cote)*100, 1)
                                    
                                    # FILTRE INTELLIGENT: priorité haute confiance
                                    if prob < 50:
                                        continue
                                    
                                    cle_unique = f"{match_id}_{local_mkt}_{prono_final}"
                                    lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                    
                                    if cle_unique not in dict_selections or prob > dict_selections[cle_unique]['prob']:
                                        dict_selections[cle_unique] = {
                                            'match_id': match_id,
                                            'match': f"{home} vs {away}",
                                            'league': nom_court,
                                            'mkt': local_mkt,
                                            'mkt_lbl': lbl,
                                            'mkt_css': css,
                                            'prono': prono_final,
                                            'cote': cote,
                                            'prob': prob,
                                            'confidence': 'high' if prob >= 65 else 'medium' if prob >= 55 else 'low'
                                        }
        except:
            pass
        
        pb.progress((idx + 1) / total_leagues)
    
    pb.empty()
    
    # TR INTELLIGENT: confiance > probabilité > cote
    liste_triee = list(dict_selections.values())
    liste_triee.sort(key=lambda x: (x['confidence'] == 'high', x['prob'], x['cote']), reverse=True)
    
    return liste_triee

def generer_pack_intelligent(selections: List[Dict], cote_cible: float) -> Tuple[List[Dict], float, str]:
    """Algorithme de pack SMART: maximise confiance, diversité, minimise corrélation"""
    if not selections:
        return [], 0.0, "Aucune sélection"
    
    ticket = []
    cote_accumulee = 1.0
    matches_utilises = set()
    leagues_utilisees = set()
    
    # Stratégie: prioriser haute confiance et diversité de ligues
    for s in selections:
        if s['match_id'] in matches_utilises:
            continue
        
        # Diversité: max 3 matchs même ligue
        if s['league'] in leagues_utilisees and len([m for m in ticket if m['league'] == s['league']]) >= 3:
            continue
        
        ticket.append(s)
        cote_accumulee *= s['cote']
        matches_utilises.add(s['match_id'])
        leagues_utilisees.add(s['league'])
        
        if cote_accumulee >= cote_cible * 0.88:
            break
    
    # Validation flexible
    if cote_accumulee >= cote_cible * 0.65:
        avg_conf = sum(1 for s in ticket if s['confidence'] == 'high') / len(ticket) * 100
        risque = "🟢 Très Faible" if cote_accumulee <= 3 else "🟡 Faible" if cote_accumulee <= 6 else "🟠 Modéré" if cote_accumulee <= 12 else "🔴 Élevé"
        return ticket, round(cote_accumulee, 2), f"{risque} · {avg_conf:.0f}% haute confiance"
    else:
        return [], 0.0, "Insuffisant"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Contrôle AI")
    
    api_health = check_api_health()
    if api_health['status']:
        st.markdown("<div class='sidebar-success'>✅ API OK</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-success'>📊 {api_health['remaining']} req</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sidebar-error'>❌ API Hors ligne</div>", unsafe_allow_html=True)
    
    st.divider()
    
    marches_actifs = st.multiselect(
        "📈 Marchés",
        options=list(MKT_INFO.keys()),
        default=['h2h', 'double_chance', 'btts'],
        format_func=lambda x: MKT_INFO[x][0]
    )
    
    active_leagues = get_active_leagues()
    if active_leagues:
        options_leagues = {l['key']: l['title'] for l in active_leagues}
        default_sel = [k for k in ['soccer_usa_mls', 'soccer_brazil_campeonato', 'soccer_england_league1'] if k in options_leagues]
        if not default_sel:
            default_sel = [list(options_leagues.keys())[0]]
        
        leagues_choisies = st.multiselect(
            "🏆 Ligues",
            options=list(options_leagues.keys()),
            default=default_sel,
            format_func=lambda x: options_leagues[x]
        )
    else:
        st.error("❌ API lues indisponibles")
        leagues_choisies = []
    
    st.divider()
    st.markdown(f"💳 Quota: `{st.session_state['api_remaining']}`")
    
    if st.button("↻ Actualiser", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #2a3550;padding-bottom:1.2rem;margin-bottom:1.8rem">
  <span class="wh-title">BETCORE AI PLATINUM v4.0</span><br>
  <span class="wh-sub">Algorithme SMART: Haute Confiance · Diversité · Minimisation Risque</span>
</div>
""", unsafe_allow_html=True)

if not leagues_choisies:
    st.info("💡 Sélectionnez une ligue dans la sidebar")
    st.stop()

if not marches_actifs:
    st.warning("⚠️ Sélectionnez un marché")
    st.stop()

# ─── ANALYSE ──────────────────────────────────────────────────────────────────
sels = fetch_selections_smart(tuple(leagues_choisies), tuple(marches_actifs))

if not sels:
    st.error("❌ Aucun match exploitable. Changez de ligues/marchés.")
    st.stop()

# ─── STATS ────────────────────────────────────────────────────────────────────
unique_matches = len(set(s["match_id"] for s in sels))
high_conf = len([s for s in sels if s['confidence'] == 'high'])
avg_prob = round(sum(s["prob"] for s in sels) / len(sels), 1)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_matches}</div><div class="stat-lbl">Matchs</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{len(sels)}</div><div class="stat-lbl">Options</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{high_conf}</div><div class="stat-lbl">Haute Confiance</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{avg_prob}%</div><div class="stat-lbl">Prob. Moy</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ─── PACKS GÉNÉRÉS ────────────────────────────────────────────────────────────
st.markdown("### 🎯 PACKS INTELLIGENTS GÉNÉRÉS", unsafe_allow_html=True)

global_used_keys = set()
packs_generes = 0

col_gauche, col_droite = st.columns([3, 2], gap="large")

with col_gauche:
    for cible in PACK_CIBLES:
        tk, total_cote, info_risque = generer_pack_intelligent(sels, cible)
        
        if not tk:
            st.markdown(f'''
            <div class="pack-off">
                📦 <b>PACK ×{cible}</b> — Indisponible aujourd'hui (manque de sélections haute confiance)
            </div>
            ''', unsafe_allow_html=True)
            continue
        
        packs_generes += 1
       的分类 = total_cote <= 4 ? "success" : (total_cote <= 8 ? "warning" : "danger")
        
        st.markdown(f'''
        <div class="pack-card {classification}">
            <div class="pack-badge {'warning' if total_cote > 6 else ''}">{total_cote}×</div>
            <div class="pack-top">
                <div class="pack-header">
                    <div class="pack-name">🎯 PACK SMART OBJECTIF ×{cible}</div>
                    <div class="pack-meta">
                        <span>📊 {len(tk)} matchs</span>
                        <span>🛡️ {info_risque}</span>
                        <span>⭐ Confiance: {round(sum(s['prob'] for s in tk)/len(tk))}%</span>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        for s in tk:
            st.markdown(f'''
            <div class="sel-row">
                <div class="sel-league">{s['league']}</div>
                <div class="sel-match">{s['match']}</div>
                <div class="sel-details">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span class="prono-text">👉 {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                </div>
                <div class="prob-bar">
                    <div class="prob-label">
                        <span>Probabilité</span>
                        <span>{s['prob']}%</span>
                    </div>
                    <div class="prob-wrap">
                        <div class="prob-fill" style="width:{min(s['prob'], 100)}%"></div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with col_droite:
    st.markdown("### 🔥 Top 15 Opportunités", unsafe_allow_html=True)
    for s in sels[:15]:
        st.markdown(f'''
        <div class="rec-row">
            <div class="rec-header">
                <span class="rec-match">{s['match']}</span>
                <span class="cote-pill" style="font-size:1.1rem">@{s['cote']}</span>
            </div>
            <div class="rec-league">{s['league']}</div>
            <div class="rec-details">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="color:#c8d0e0;font-size:0.85rem">🎯 {s['prono']}</span>
            </div>
            <div class="prob-bar">
                <div class="prob-wrap">
                    <div class="prob-fill" style="width:{min(s['prob'], 100)}%"></div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# Footer statistique
st.markdown("<br><br>", unsafe_allow_html=True)
st.success(f"✅ {packs_generes}/{len(PACK_CIBLES)} packs générés avec succès - Algorithme SMART actif")
