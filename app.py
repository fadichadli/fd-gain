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
.sel-row { background:linear-gradient(90deg, #111827 0%, #1a2332 100%); border:1px solid #2a3550; border-left:5px solid #ffd700; border-radius:10px; padding:18px; margin-top:12px; transition:all 0.3s; }
.sel-row:hover { transform:translateX(5px); border-color:#ffd700; box-shadow:0 4px 16px rgba(255,215,0,0.2); }
.sel-league { font-size:0.75rem; color:#ffd700; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; }
.sel-match { font-weight:700; font-size:1.1rem; color:#fff; margin:10px 0; text-shadow:0 1px 4px rgba(0,0,0,0.5); }
.sel-details { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.badge { font-size:0.75rem; font-weight:700; padding:5px 14px; border-radius:20px; border:2px solid; background:rgba(255,215,0,0.1); }
.b-h2h { color:#ffd700; border-color:#ffd700; }
.cote-pill { font-family:'Bebas Neue'; font-size:1.6rem; background:linear-gradient(135deg, #ffd700 0%, #ffb700 100%); color:#07090f; padding:6px 18px; border-radius:8px; font-weight:700; box-shadow:0 4px 12px rgba(255,215,0,0.4); }
.stat-box { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:1px solid #2a3550; border-radius:12px; padding:20px; text-align:center; box-shadow:0 4px 16px rgba(0,0,0,0.3); }
.stat-val { font-family:'Bebas Neue'; font-size:2.6rem; color:#ffd700; text-shadow:0 2px 8px rgba(255,215,0,0.3); }
.stat-lbl { font-size:0.8rem; color:#5a6a8a; margin-top:6px; }
.pack-off { background:#0a0d15; border:2px dashed #2a3550; border-radius:16px; padding:24px; color:#4a5570; text-align:center; }
.rec-row { background:#0f1623; border:1px solid #2a3550; border-radius:10px; padding:16px; margin-bottom:10px; }
.sidebar-success { color:#ffd700; font-weight:600; }
.info-box { background:rgba(255,215,0,0.1); border:1px solid rgba(255,215,0,0.3); border-radius:8px; padding:14px; margin:10px 0; color:#ffd700; }
.success-box { background:rgba(0,229,160,0.1); border:1px solid rgba(0,229,160,0.3); border-radius:8px; padding:14px; margin:10px 0; color:#00e5a0; }
</style>
""", unsafe_allow_html=True)

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 8, 12]

st.markdown("""
<div class="info-box">
    <strong>⚠️ REALITÉ API GRATUITE :</strong> Le plan gratuit de The Odds API ne donne que <strong>h2h (1X2)</strong>.
    BTTS, Over/Under, Double Chance sont réservés au plan PAYANT ($150/mois).
    <br><br>
    <strong>✅ NOTRE SOLUTION :</strong> Maximiser les matchs 1X2 avec 20+ ligues + Algorithme optimisé pour ZÉRO répétition.
</div>
""", unsafe_allow_html=True)

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
            return soccer_leagues  # TOUTES les ligues, pas de limite
    except Exception as e:
        st.error(f"Erreur: {e}")
    return []

@st.cache_data(ttl=300, show_spinner=False)
def check_api_health():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
        return {'status': r.status_code == 200, 'remaining': r.headers.get('x-requests-remaining', 'N/A')}
    except:
        return {'status': False, 'remaining': 'N/A'}

def fetch_all_matches_optimized(leagues_list):
    """
    Optimisation maximale :
    - h2h avec TOUS les bookmakers (bookmakers=all)
    - Filtre cotes 1.25-3.80 (zone optimale)
    - Probabilité minimum 42% (plus bas = plus de matchs)
    """
    all_selections = []
    logs = []
    stats = {'ligues': 0, 'succes': 0, 'echec': 0, 'matchs_total': 0}
    
    if not leagues_list:
        return [], ["Aucune ligue"], stats
    
    pb = st.progress(0, text="🔍 Scan maximisé...")
    
    for idx, ligue in enumerate(leagues_list):
        ligue_key = ligue['key']
        ligue_title = ligue['title']
        nom_court = ligue_key.replace('soccer_', '').replace('_', ' ').upper()
        stats['ligues'] += 1
        
        # h2h + TOUS bookmakers pour avoir PLUS de cotes
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
                        
                        # Prendre le MEILLEUR bookmaker (cote la plus haute)
                        best_outcomes = {}
                        
                        for bk in match.get('bookmakers', []):
                            for mkt in bk.get('markets', []):
                                if mkt.get('key') != 'h2h':
                                    continue
                                
                                for 
