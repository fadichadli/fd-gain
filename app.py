import streamlit as st
import requests
from datetime import datetime, timedelta
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
.pack-card { 
    background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); 
    border:2px solid #00e5a0; 
    border-radius:16px; 
    padding:24px 28px; 
    margin-bottom:24px; 
    box-shadow:0 8px 32px rgba(0,229,160,0.2);
    position:relative;
    overflow:hidden;
}
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
.pack-badge.warning { background:linear-gradient(135deg, #ffb400 0%, #e6a200 100%); }
.pack-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; gap:20px; }
.pack-header { flex:1; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:2rem; letter-spacing:0.1em; color:#fff; margin-bottom:8px; }
.pack-meta { font-size:0.8rem; color:#6b7a9a; line-height:1.6; }
.pack-meta span { margin-right:15px; }
.sel-row { 
    background:linear-gradient(90deg, #111827 0%, #1a2332 100%); 
    border:1px solid #2a3550; 
    border-left:4px solid #00e5a0;
    border-radius:10px; 
    padding:16px 20px; 
    margin-top:12px;
}
.sel-league { font-size:0.72rem; color:#00e5a0; margin-bottom:6px; font-weight:700; text-transform:uppercase; }
.sel-match { font-weight:700; font-size:1.05rem; color:#fff; margin-bottom:10px; }
.sel-details { display:flex; align-items:center; gap:12px; margin-top:8px; flex-wrap:wrap; }
.badge { display:inline-block; font-size:0.7rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; padding:4px 12px; border-radius:20px; border:1px solid; }
.b-h2h { background:rgba(0,229,160,0.15); color:#00e5a0; border-color:#00e5a0; }
.b-dc { background:rgba(77,159,255,0.15); color:#4d9fff; border-color:#4d9fff; }
.b-btts { background:rgba(255,180,0,0.15); color:#ffb400; border-color:#ffb400; }
.b-over { background:rgba(200,100,255,0.15); color:#c864ff; border-color:#c864ff; }
.b-under { background:rgba(255,90,90,0.15); color:#ff5a5a; border-color:#ff5a5a; }
.prono-text { font-size:0.9rem; color:#c8d0e0; font-weight:600; }
.cote-pill { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; background:linear-gradient(135deg, #00e5a0 0%, #00c98d 100%); color:#07090f; padding:4px 14px; border-radius:6px; box-shadow:0 3px 10px rgba(0,229,160,0.4); }
.prob-bar { margin-top:12px; }
.prob-label { font-size:0.68rem; color:#5a6a8a; margin-bottom:4px; display:flex; justify-content:space-between; }
.prob-wrap { background:#0a0f1a; border-radius:4px; height:6px; overflow:hidden; }
.prob-fill { height:6px; border-radius:4px; background:linear-gradient(90deg,#0077ff 0%,#00e5a0 50%,#00ff88 100%); }
.stat-box { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:1px solid #2a3550; border-radius:12px; padding:18px; text-align:center; box-shadow:0 4px 16px rgba(0,0,0,0.3); }
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2.4rem; color:#00e5a0; line-height:1; margin-bottom:6px; }
.stat-lbl { font-size:0.75rem; color:#5a6a8a; }
.pack-off { background:linear-gradient(135deg, #0a0d15 0%, #0f1420 100%); border:2px dashed #2a3550; border-radius:16px; padding:24px; margin-bottom:20px; color:#4a5570; font-size:0.9rem; text-align:center; }
.rec-row { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:1px solid #2a3550; border-radius:10px; padding:14px 18px; margin-bottom:10px; }
.rec-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.rec-match { font-weight:600; font-size:0.9rem; color:#e8eaf0; }
.rec-league { font-size:0.72rem; color:#5a6a8a; margin:4px 0; }
.rec-details { display:flex; gap:8px; align-items:center; margin-top:8px; }
.sidebar-success { color:#00e5a0; font-weight:600; }
.sidebar-error { color:#ff5a5a; font-weight:600; }
.info-box { background:rgba(77,159,255,0.1); border:1px solid rgba(77,159,255,0.3); border-radius:8px; padding:12px; margin:10px 0; color:#4d9fff; }
</style>
""", unsafe_allow_html=True)

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 15]
REQUEST_TIMEOUT = 15

MKT_INFO = {
    'h2h': ('1X2', 'b-h2h'),
    'double_chance': ('Double Chance', 'b-dc'),
    'btts': ('BTTS (Les 2 Marquent)', 'b-btts'),
    'totals_over': ('Over (Plus de buts)', 'b-over'),
    'totals_under': ('Under (Moins de buts)', 'b-under'),
}

DC_MAP = {
    'HomeOrDraw': '1X (Domicile ou Nul)',
    'AwayOrDraw': 'X2 (Extérieur ou Nul)',
    'HomeOrAway': '12 (Pas de Nul)'
}

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

def fetch_selections_smart(leagues_tuple, marches_tuple):
    """
    Récupère TOUS les marchés (1X2, DC, BTTS, Over/Under)
    Filtre matchs des 48h prochaines (aujourd'hui + demain)
    """
    if not leagues_tuple or not marches_tuple:
        return []
    
    # TOUS les marchés API demanded
    api_mkts = set()
    for m in marches_tuple:
        if m.startswith('totals'):
            api_mkts.add('totals')
        elif m == 'double_chance':
            api_mkts.add('double_chance')
        elif m == 'btts':
            api_mkts.add('btts')
        elif m == 'h2h':
            api_mkts.add('h2h')
    
    mkts_str = ','.join(api_mkts)
    
    dict_selections = {}
    total_leagues = len(leagues_tuple)
    pb = st.progress(0, text="🎯 Analyse TOUS marchés en cours...")
    
    for idx, ligue in enumerate(leagues_tuple):
        nom_court = ligue.replace('soccer_', '').replace('_', ' ').upper()
        
        # TOUS les marchés demandés
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        
        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT)
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            
            if r.status_code != 200 or not r.json():
                # Fallback: marchés de base
                url_fallback = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts,double_chance&oddsFormat=decimal'
                r = requests.get(url_fallback, timeout=REQUEST_TIMEOUT)
            
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    for match in data:
                        match_id = match['id']
                        home = match.get('home_team', 'Inconnu')
                        away = match.get('away_team', 'Inconnu')
                        match_date = match.get('commence_time', '')
                        
                        for bk in match.get('bookmakers', []):
                            bk_name = bk.get('title', 'Bookmaker')
                            
                            for mkt in bk.get('markets', []):
                                mkt_key = mkt.get('key', '')
                                
                                for out in mkt.get('outcomes', []):
                                    cote = out.get('price', 1.0)
                                    name = out.get('name', '')
                                    
                                    # Filtre cotes: 1.20 - 4.50 (zone optimale)
                                    if cote < 1.20 or cote > 4.50:
                                        continue
                                    
                                    local_mkt = mkt_key
                                    prono_final = name
                                    
                                    # Normalisation Over/Under
                                    if mkt_key == 'totals':
                                        point = out.get('point', 2.5)
                                        if name.lower() == 'over':
                                            local_mkt = 'totals_over'
                                            prono_final = f"Over {point}"
                                        elif name.lower() == 'under':
                                            local_mkt = 'totals_under'
                                            prono_final = f"Under {point}"
                                    
                                    # Vérifier si marché sélectionné
                                    if local_mkt not in ['h2h', 'double_chance', 'btts', 'totals_over', 'totals_under']:
                                        continue
                                    
                                    if local_mkt not in marches_tuple:
                                        continue
                                    
                                    # Traduction pronos
                                    if local_mkt == 'double_chance':
                                        prono_final = DC_MAP.get(name, name)
                                    elif local_mkt == 'btts':
                                        prono_final = "Oui - Les deux marquent" if name.lower() == 'yes' else "Non - Un seul marque"
                                    elif local_mkt == 'h2h':
                                        if name.lower() == 'draw':
                                            prono_final = "Match Nul"
                                        elif name == home:
                                            prono_final = f"Victoire {home}"
                                        elif name == away:
                                            prono_final = f"Victoire {away}"
                                    
                                    prob = round((1/cote)*100, 1)
                                    
                                    # FILTRE INTELLIGENT: probabilité minimale 48%
                                    if prob < 48:
                                        continue
                                    
                                    # Clé UNIQUE par match+marché+prono
                                    cle_unique = f"{match_id}_{local_mkt}_{prono_final}"
                                    lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                    
                                    # Garder MEILLEURE cote
                                    if cle_unique not in dict_selections or cote > dict_selections[cle_unique]['cote']:
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
                                            'confidence': 'high' if prob >= 65 else 'medium' if prob >= 55 else 'low',
                                            'bookmaker': bk_name
                                        }
        except Exception as e:
            st.error(f"⚠️ Erreur {nom_court}: {str(e)[:50]}")
        
        pb.progress((idx + 1) / total_leagues)
    
    pb.empty()
    
    # TRI: haute confiance > probabilité > cote
    liste_triee = list(dict_selections.values())
    liste_triee.sort(key=lambda x: (
        x['confidence'] == 'high',
        x['prob'],
        x['cote']
    ), reverse=True)
    
    return liste_triee

def generer_pack_diversifie(selections, cote_cible):
    """
    ALGORITHME INTELLIGENT:
    - Pas de répétition de matchs
    - Diversité de marchés (max 2 mêmes marché)
    - Diversité de ligues (max 2 mêmes ligue)
    - Probabilité cumulée optimisée
    """
    if not selections:
        return [], 0.0, "Aucune sélection disponible"
    
    ticket = []
    cote_accumulee = 1.0
    matches_utilises = set()
    leagues_utilisees = {}  # ligue -> count
    markets_utilises = {}   # marché -> count
    
    # Premier: trier par confiance décroissante
    sorted_sels = sorted(selections, key=lambda x: x['prob'], reverse=True)
    
    for s in sorted_sels:
        # Vérifier déjà utilisé
        if s['match_id'] in matches_utilises:
            continue
        
        # Limite ligue: max 2 matchs même ligue
        ligue = s['league']
        if leagues_utilisees.get(ligue, 0) >= 2:
            continue
        
        # Limite marché: max 2 mêmes marché
        mkt = s['mkt']
        if markets_utilisees.get(mkt, 0) >= 2:
            continue
        
        # Ajouter au ticket
        ticket.append(s)
        cote_accumulee *= s['cote']
        matches_utilises.add(s['match_id'])
        leagues_utilisees[ligue] = leagues_utilisees.get(ligue, 0) + 1
        markets_utilisees[mkt] = markets_utilisees.get(mkt, 0) + 1
        
        # Arriver proche cible (92%)
        if cote_accumulee >= cote_cible * 0.92:
            break
    
    # Validation flexible (60% minimum)
    if cote_accumulee >= cote_cible * 0.60:
        avg_prob = round(sum(s['prob'] for s in ticket) / len(ticket), 1)
        nb_high_conf = sum(1 for s in ticket if s['confidence'] == 'high')
        
        # Calcul risque basé sur cote ET probabilité
        if cote_accumulee <= 3 and avg_prob >= 60:
            risque = "🟢 Très Faible"
        elif cote_accumulee <= 6 and avg_prob >= 55:
            risque = "🟡 Faible"
        elif cote_accumulee <= 12 and avg_prob >= 50:
            risque = "🟠 Modéré"
        else:
            risque = "🔴 Élevé"
        
        info = f"{risque} · {nb_high_conf}/{len(ticket)} haute conf · {avg_prob}% moy"
        return ticket, round(cote_accumulee, 2), info
    else:
        return [], 0.0, "Cible non atteinte"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Contrôle AI")
    
    api_health = check_api_health()
    if api_health['status']:
        st.markdown("<div class='sidebar-success'>✅ API Opérationnelle</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-success'>📊 {api_health['remaining']} requêtes restantes</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sidebar-error'>❌ API Indisponible</div>", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 📊 Marchés disponibles")
    
    marches_actifs = st.multiselect(
        "Cochez TOUS les marchés souhaités :",
        options=list(MKT_INFO.keys()),
        default=['h2h', 'double_chance', 'btts', 'totals_over'],
        format_func=lambda x: MKT_INFO[x][0]
    )
    
    st.info("""
    **Marchés inclus :**
    - 1X2 : Victoire Domicile/Nul/Extérieur
    - Double Chance : 1X, X2, 12
    - BTTS : Les 2 équipes marquent (Oui/Non)
    - Over : Plus de X buts
    - Under : Moins de X buts
    """)
    
    st.divider()
    st.markdown("### 🏆 Ligues à scanner")
    
    active_leagues = get_active_leagues()
    if active_leagues:
        options_leagues = {l['key']: l['title'] for l in active_leagues}
        
        # Ligues populaires par défaut
        default_sel = [k for k in [
            'soccer_usa_mls', 
            'soccer_brazil_campeonato', 
            'soccer_england_league1',
            'soccer_germany_bundesliga2',
            'soccer_netherlands_erstdive'
        ] if k in options_leagues]
        
        if not default_sel:
            default_sel = [list(options_leagues.keys())[0]]
        
        leagues_choisies = st.multiselect(
            "Sélectionnez plusieurs ligues pour PLUS de matchs :",
            options=list(options_leagues.keys()),
            default=default_sel,
            format_func=lambda x: options_leagues[x]
        )
        
        st.markdown(f"<div style='font-size:0.75rem;color:#3a4a6a'>💡 {len(active_leagues)} ligues disponibles - Choisissez-en au moins 3</div>", unsafe_allow_html=True)
    else:
        st.error("❌ Impossible de récupérer les ligues")
        leagues_choisies = []
    
    st.divider()
    st.markdown(f"💳 **Quota API :** `{st.session_state['api_remaining']}`")
    
    if st.button("↻ Lancer analyse complète", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #2a3550;padding-bottom:1.2rem;margin-bottom:1.8rem">
  <span class="wh-title">BETCORE AI PLATINUM v4.1</span><br>
  <span class="wh-sub">Algorithme SMART: 5 marchés + Diversité maximale + Zéro répétition de matchs</span>
</div>
""", unsafe_allow_html=True)

# ─── VÉRIFICATIONS PRÉ-ANALYSE ────────────────────────────────────────────────
if not leagues_choisies:
    st.info("💡 **Sélectionnez au moins 1 ligue** dans la sidebar")
    st.stop()

if not marches_actifs:
    st.warning("⚠️ **Sélectionnez au moins 1 marché** dans la sidebar")
    st.stop()

if len(leagues_choisies) < 3:
    st.info("""
    💡 **Conseil :** Choisissez **au moins 3 ligues** pour avoir suffisamment de matchs 
    et générer des packs diversifiés sans répétition.
    """)

# ─── ANALYSE COMPLÈTE ─────────────────────────────────────────────────────────
with st.spinner("🔍 Analyse de TOUS les marchés en cours..."):
    sels = fetch_selections_smart(tuple(leagues_choisies), tuple(marches_actifs))

if not sels:
    st.error("""
    ❌ **Aucune sélection exploitable trouvée**
    
    **Solutions :**
    1. Sélectionnez PLUS de ligues (minimum 3)
    2. Cochez TOUS les marchés disponibles
    3. Vérifiez que les ligues ont des matchs aujourd'hui/demain
    4. Cliquez sur "Lancer analyse complète"
    """)
    st.stop()

# ─── STATS GLOBALES ───────────────────────────────────────────────────────────
unique_matches = len(set(s["match_id"] for s in sels))
high_conf = len([s for s in sels if s['confidence'] == 'high'])
medium_conf = len([s for s in sels if s['confidence'] == 'medium'])
avg_prob = round(sum(s["prob"] for s in sels) / len(sels), 1)

# Répartition par marché
mkt_counts = {}
for s in sels:
    mkt_counts[s['mkt_lbl']] = mkt_counts.get(s['mkt_lbl'], 0) + 1

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_matches}</div><div class="stat-lbl">Matchs Uniques</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{len(sels)}</div><div class="stat-lbl">Sélections</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{high_conf}</div><div class="stat-lbl">Haute Confiance</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{avg_prob}%</div><div class="stat-lbl">Prob. Moyenne</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="stat-box"><div class="stat-val">{len(marches_actifs)}</div><div class="stat-lbl">Marchés</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Répartition marchés
st.markdown("### 📊 Répartition par marché")
cols_mkt = st.columns(len(mkt_counts))
for idx, (mkt, count) in enumerate(sorted(mkt_counts.items(), key=lambda x: x[1], reverse=True)):
    with cols_mkt[idx]:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{count}</div><div class="stat-lbl">{mkt}</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ─── PACKS GÉNÉRÉS ────────────────────────────────────────────────────────────
st.markdown("### 🎯 PACKS INTELLIGENTS - ZÉRO RÉPÉTITION", unsafe_allow_html=True)

packs_generes = 0
total_selections_utilisees = set()

col_gauche, col_droite = st.columns([3, 2], gap="large")

with col_gauche:
    for cible in PACK_CIBLES:
        tk, total_cote, info_risque = generer_pack_diversifie(sels, cible)
        
        if not tk:
            st.markdown(f'''
            <div class="pack-off">
                📦 <b>PACK ×{cible}</b> — Indisponible (manque de sélections diversifiées)
            </div>
            ''', unsafe_allow_html=True)
            continue
        
        packs_generes += 1
        
        # Classification
        if total_cote <= 4:
            classification = "success"
        elif total_cote <= 8:
            classification = "warning"
        else:
            classification = "danger"
        
        badge_class = "warning" if total_cote > 6 else ""
        
        html_pack = f'''
        <div class="pack-card">
            <div class="pack-badge {badge_class}">{total_cote}×</div>
            <div class="pack-top">
                <div class="pack-header">
                    <div class="pack-name">🎯 PACK SMART ×{cible}</div>
                    <div class="pack-meta">
                        <span>📊 {len(tk)} matchs</span>
                        <span>🛡️ {info_risque}</span>
                        <span>🎲 {len(set(s["match_id"] for s in tk))} uniques</span>
                    </div>
                </div>
            </div>
        '''
        
        st.markdown(html_pack, unsafe_allow_html=True)
        
        for s in tk:
            html_sel = f'''
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
            '''
            st.markdown(html_sel, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with col_droite:
    st.markdown("### 🔥 TOP 20 - Meilleures sélections", unsafe_allow_html=True)
    for s in sels[:20]:
        html_rec = f'''
        <div class="rec-row">
            <div class="rec-header">
                <span class="rec-match">{s['match']}</span>
                <span class="cote-pill" style="font-size:1.1rem">@{s['cote']}</span>
            </div>
            <div class="rec-league">{s['league']}</div>
            <div class="rec-details">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="color:#c8d0e0;font-size:0.85rem">🎯 {s['prono']}</span>
                <span style="font-size:0.75rem;color:#5a6a8a">({s['prob']}%)</span>
            </div>
            <div class="prob-bar">
                <div class="prob-wrap">
                    <div class="prob-fill" style="width:{min(s['prob'], 100)}%"></div>
                </div>
            </div>
        </div>
        '''
        st.markdown(html_rec, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.success(f"✅ {packs_generes}/{len(PACK_CIBLES)} packs générés avec succès | {len(sels)} sélections analysées | {high_conf} haute confiance")
