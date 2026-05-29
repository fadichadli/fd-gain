import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

if 'api_remaining' not in st.session_state:
    st.session_state['api_remaining'] = "Non vérifié"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:#07090f; color:#e8eaf0; }
.block-container { padding:1.5rem 2rem; max-width:1300px; }
.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3rem; color:#00e5a0; letter-spacing:0.1em; }
.wh-sub   { color:#3a4a6a; font-size:0.85rem; }
.pack-card { background:#0d1220; border:1px solid #1a2540; border-radius:14px; padding:18px 22px; margin-bottom:14px; border-left:4px solid #00e5a0; }
.pack-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:0.08em; color:#e8eaf0; }
.pack-meta { font-size:0.72rem; color:#3a4a6a; margin-top:2px; }
.pack-cote { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#ffd700; line-height:1; }
.sel-row { background:#111827; border:1px solid #1e2a40; border-radius:8px; padding:11px 15px; margin-top:8px; }
.sel-match  { font-weight:600; font-size:0.88rem; color:#c8d0e0; }
.sel-league { font-size:0.7rem; color:#3a4a6a; margin-bottom:5px; }
.cote-pill  { font-family:'Bebas Neue',sans-serif; font-size:1.15rem; background:rgba(0,229,160,0.1); color:#00e5a0; padding:1px 10px; border-radius:4px; display:inline-block; }
.badge { display:inline-block; font-size:0.67rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:2px 9px; border-radius:20px; }
.b-h2h   { background:rgba(0,229,160,0.12); color:#00e5a0; }
.b-dc    { background:rgba(77,159,255,0.12); color:#4d9fff; }
.b-btts  { background:rgba(255,180,0,0.12);  color:#ffb400; }
.b-over  { background:rgba(200,100,255,0.12);color:#c864ff; }
.b-under { background:rgba(255,90,90,0.12);  color:#ff5a5a; }
.stat-box { background:#0d1220; border:1px solid #1a2540; border-radius:10px; padding:14px; text-align:center; }
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00e5a0; line-height:1; }
.stat-lbl { font-size:0.7rem; color:#3a4a6a; margin-top:3px; }
.pack-off { background:#0a0d15; border:1px dashed #1a2035; border-radius:14px; padding:14px 22px; margin-bottom:14px; color:#2a3550; font-size:0.8rem; }
.rec-row { background:#0d1220; border:1px solid #151d30; border-radius:8px; padding:10px 13px; margin-bottom:6px; }
.prob-wrap { background:#0a0f1a; border-radius:3px; height:3px; margin-top:5px; }
.prob-fill { height:3px; border-radius:3px; background:linear-gradient(90deg,#0077ff,#00e5a0); }
</style>
""", unsafe_allow_html=True)

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20]

MKT_INFO = {
    'h2h':           ('1X2',            'b-h2h'),
    'double_chance': ('Double Chance',   'b-dc'),
    'btts':          ('Les 2 Marquent',  'b-btts'),
    'totals_over':   ('Over (Buts+)',    'b-over'),
    'totals_under':  ('Under (Buts-)',   'b-under'),
}

DC_MAP = {
    'HomeOrDraw': '1X (Gagnant ou Nul)',
    'AwayOrDraw': 'X2 (Nul ou Gagnant)',
    'HomeOrAway': '12 (Match non Nul)'
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_active_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return [s for s in r.json() if s.get('group') == 'Soccer' and not s.get('has_outrights')]
    except: pass
    return []

active_leagues_list = get_active_leagues()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Zone de Contrôle AI")
    
    marches_actifs = st.multiselect(
        "Marchés d'analyse", 
        options=list(MKT_INFO.keys()), 
        default=['h2h', 'double_chance', 'btts', 'totals_over'], 
        format_func=lambda x: MKT_INFO[x][0]
    )
    
    if active_leagues_list:
        options_leagues = {l['key']: l['title'] for l in active_leagues_list}
        default_sel = [k for k in ['soccer_usa_mls', 'soccer_brazil_campeonato', 'soccer_finland_veikkausliiga'] if k in options_leagues]
        if not default_sel: default_sel = [list(options_leagues.keys())[0]]
        
        leagues_choisies = st.multiselect(
            "Ligues à scanner", 
            options=list(options_leagues.keys()), 
            default=default_sel, 
            format_func=lambda x: options_leagues[x]
        )
    else:
        st.error("Impossible de joindre l'API pour lister les ligues.")
        leagues_choisies = []

    st.divider()
    st.markdown(f"💳 **Quota API Restant :** `{st.session_state['api_remaining']}`")
    
    st.markdown("### 📊 Console d'état API")
    status_box = st.empty() # Console de débug en direct
    
    if st.button("↻ Forcer l'actualisation", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #151d30;padding-bottom:1rem;margin-bottom:1.5rem">
  <span class="wh-title">BETCORE AI PLATINUM v3.6</span><br>
  <span class="wh-sub">Algorithme de secours tolérant aux pannes de l'offre API Standard</span>
</div>
""", unsafe_allow_html=True)

# ─── MOTEUR SÉCURISÉ AVEC FALLBACK AUTOMATIQUE ───────────────────────────────
def fetch_selections_secure(leagues_tuple, marches_tuple):
    if not leagues_tuple or not marches_tuple: return []
    
    api_mkts = set()
    for m in marches_tuple: 
        api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)
    
    dict_selections = {}
    logs_sidebar = []
    
    pb = st.progress(0, text="Analyse dynamique en cours...")
    
    for idx, ligue in enumerate(leagues_tuple):
        nom_court = ligue.replace('soccer_', '').replace('_', ' ').upper()
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        
        try:
            r = requests.get(url, timeout=12)
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
                
            # STRATÉGIE DE REPLI : Si l'offre gratuite bloque les marchés complexes (Code 400 ou vide)
            if r.status_code != 200 or not r.json():
                logs_sidebar.append(f"⚠️ {nom_court} : Repli sur les marchés de base...")
                url_fallback = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal'
                r = requests.get(url_fallback, timeout=12)
                
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    logs_sidebar.append(f"🟢 {nom_court} : {len(data)} matchs trouvés")
                    
                    for match in data:
                        match_id = match['id']
                        home, away = match.get('home_team',''), match.get('away_team','')
                        
                        for bk in match.get('bookmakers', []):
                            for mkt in bk.get('markets', []):
                                mkt_key = mkt.get('key','')
                                
                                for out in mkt.get('outcomes', []):
                                    cote = out.get('price', 1.0)
                                    name = out.get('name', '')
                                    if cote <= 1.15: continue
                                    
                                    local_mkt = mkt_key
                                    prono_final = name
                                    
                                    if mkt_key == 'totals':
                                        point = out.get('point', 2.5)
                                        if name.lower() == 'over':
                                            local_mkt = 'totals_over'
                                            prono_final = f"Over {point} Buts"
                                        elif name.lower() == 'under':
                                            local_mkt = 'totals_under'
                                            prono_final = f"Under {point} Buts"
                                    
                                    if local_mkt not in marches_tuple: continue
                                    
                                    if local_mkt == 'double_chance':
                                        prono_final = DC_MAP.get(name, name)
                                    elif local_mkt == 'btts':
                                        prono_final = "Les 2 marquent" if name.lower() == 'yes' else "Pas de but des 2 côtés"
                                    elif local_mkt == 'h2h':
                                        if name.lower() == 'draw': prono_final = "Match Nul"
                                        elif name == home: prono_final = f"Victoire {home}"
                                        elif name == away: prono_final = f"Victoire {away}"
                                    
                                    cle_unique = f"{match_id}_{local_mkt}_{prono_final}"
                                    
                                    if cle_unique not in dict_selections or cote > dict_selections[cle_unique]['cote']:
                                        lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                        dict_selections[cle_unique] = {
                                            'match_id': match_id,
                                            'match': f"{home} vs {away}",
                                            'league': nom_court,
                                            'mkt': local_mkt,
                                            'mkt_lbl': lbl,
                                            'mkt_css': css,
                                            'prono': prono_final,
                                            'cote': cote,
                                            'prob': round((1/cote)*100, 1)
                                        }
                else:
                    logs_sidebar.append(f"⚪ {nom_court} : Aucun match ouvert")
            else:
                logs_sidebar.append(f"🔴 {nom_court} : Erreur API {r.status_code}")
        except Exception as e:
            logs_sidebar.append(f"💥 {nom_court} : Erreur réseau")
            
        pb.progress((idx + 1) / len(leagues_tuple))
        
    pb.empty()
    # Affichage des logs dans la sidebar
    with status_box.container():
        for log in logs_sidebar:
            st.caption(log)
            
    liste_triee = list(dict_selections.values())
    liste_triee.sort(key=lambda x: x['prob'], reverse=True)
    return liste_triee

# ─── ALGORITHME DE PACKS ──────────────────────────────────────────────────────
def generer_pack(selections_dispo, cote_cible, cles_utilisees):
    ticket = []
    cote_accumulee = 1.0
    matches_du_ticket = set()
    
    for s in selections_dispo:
        id_unique = f"{s['match_id']}_{s['mkt']}_{s['prono']}"
        if id_unique in cles_utilisees or s['match_id'] in matches_du_ticket:
            continue
            
        ticket.append(s)
        cote_accumulee *= s['cote']
        matches_du_ticket.add(s['match_id'])
        cles_utilisees.add(id_unique)
        
        if cote_accumulee >= cote_cible * 0.92:
            break
            
    if cote_accumulee >= cote_cible * 0.75:
        return ticket, round(cote_accumulee, 2)
    else:
        for s in ticket:
            cles_utilisees.remove(f"{s['match_id']}_{s['mkt']}_{s['prono']}")
        return [], 0.0

# ─── RENDU DE L'INTERFACE ─────────────────────────────────────────────────────
if not leagues_choisies:
    st.info("💡 Sélectionnez au moins une ligue active dans le panneau de gauche pour commencer l'analyse.")
    st.stop()

sels = fetch_selections_secure(tuple(leagues_choisies), tuple(marches_actifs))

if not sels:
    st.error("❌ Aucun match exploitable trouvé. Les ligues sélectionnées n'ont aucun match programmé par les bookmakers dans les prochaines 48 heures.")
    st.stop()

# Tableau de bord
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="stat-box"><div class="stat-val">{len(set(s["match_id"] for s in sels))}</div><div class="stat-lbl">Matchs Analysés</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="stat-box"><div class="stat-val">{len(sels)}</div><div class="stat-lbl">Options Identifiées</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="stat-box"><div class="stat-val">{round(sum(s["prob"] for s in sels[:5])/5, 1)}%</div><div class="stat-lbl">Indice Max</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="stat-box"><div class="stat-val">{len(marches_actifs)}</div><div class="stat-lbl">Filtres</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_gauche, col_droite = st.columns([3, 2], gap="large")
global_used_keys = set()

with col_gauche:
    st.markdown("### 📦 Générateur de Packs Combinés")
    for cible in PACK_CIBLES:
        tk, total_cote = generer_pack(sels, cible, global_used_keys)
        
        if not tk:
            st.markdown(f'<div class="pack-off">📦 <b>PACK OBJECTIF ×{cible}</b> — Pas assez de sélections différentes disponibles pour ce niveau de cote aujourd\'hui.</div>', unsafe_allow_html=True)
            continue
            
        avg_prob = round(sum(i['prob'] for i in tk)/len(tk), 1)
        statut_risque = "🟢 Faible" if total_cote <= 3.5 else "🟡 Modéré" if total_cote <= 9.0 else "🟠 Élevé"
        
        lignes_html = ""
        for s in tk:
            lignes_html += f"""
            <div class="sel-row">
                <div class="sel-league">{s['league']}</div>
                <div class="sel-match">{s['match']}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-top:5px;flex-wrap:wrap;">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="font-size:0.85rem;color:#e8eaf0">👉 {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                </div>
                <div class="prob-wrap"><div class="prob-fill" style="width:{min(s['prob'],100)}%"></div></div>
            </div>"""
            
        st.markdown(f"""
        <div class="pack-card">
            <div class="pack-top">
                <div>
                    <div class="pack-name">PACK UNIQUE OBJECTIF ×{cible}</div>
                    <div class="pack-meta">{len(tk)} matchs · Confiance Moyenne {avg_prob}% · Risque : {statut_risque}</div>
                </div>
                <div class="pack-cote">{total_cote}×</div>
            </div>
            {lignes_html}
        </div>""", unsafe_allow_html=True)

with col_droite:
    st.markdown("### 📋 Flux des opportunités (Top 15)")
    for s in sels[:15]:
        st.markdown(f"""
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;font-size:0.85rem;color:#c8d0e0">{s['match']}</span>
                <span class="cote-pill">@{s['cote']}</span>
            </div>
            <div style="font-size:0.7rem;color:#3a4a6a;margin-top:2px;">{s['league']}</div>
            <div style="display:flex;gap:6px;align-items:center;margin-top:5px;">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="font-size:0.8rem;color:#e8eaf0">🎯 {s['prono']}</span>
            </div>
            <div class="prob-wrap"><div class="prob-fill" style="width:{min(s['prob'],100)}%"></div></div>
        </div>""", unsafe_allow_html=True)
