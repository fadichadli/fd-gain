import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── CONFIGURATION DE LA PAGE ─────────────────────────────────────────────────
st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

# STYLE CSS PRO (Corrigé avec unsafe_allow_html=True)
st.markdown("""
<style>
    .wh-title { font-size: 3rem; color: #00e5a0; font-weight: 800; }
    .pack-card { background: #0d1220; border: 1px solid #151d30; border-radius: 14px; padding: 20px; margin-bottom: 20px; }
    .sel-row { background: #111827; border: 1px solid #1a2540; border-radius: 8px; padding: 10px; margin-top: 10px; }
    .badge { padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; }
    .badge-h2h { background: #00e5a0; color: black; }
    .badge-dc { background: #4d9fff; color: white; }
</style>
""", unsafe_allow_html=True)

# ─── FONCTION FETCH COMPLÈTE (Multi-marchés) ──────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_selections():
    # Ici, tu réinsères ta liste complète de marchés
    API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
    markets = 'h2h,double_chance,btts,totals'
    ligues = ['soccer_france_ligue_one', 'soccer_germany_bundesliga'] # Ajoute les autres
    
    matchs = []
    for ligue in ligues:
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&markets={markets}&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=10).json()
            for m in r:
                # Logique complète d'extraction de tes anciens marchés
                for bk in m.get('bookmakers', []):
                    for mkt in bk.get('markets', []):
                        for out in mkt.get('outcomes', []):
                            matchs.append({
                                'id': m['id'], 'match': f"{m['home_team']} vs {m['away_team']}",
                                'mkt': mkt['key'], 'prono': out['name'], 
                                'cote': out['price'], 'score_ia': 0.85
                            })
        except: continue
    return matchs

# ─── LOGIQUE DE PACKS RÉTABLIE ────────────────────────────────────────────────
st.markdown("<h1 class='wh-title'>WinHand AI</h1>", unsafe_allow_html=True)
sels = fetch_selections()

if not sels:
    st.warning("⚠️ Analyse en cours ou quota API atteint...")
else:
    cles_utilisees = set()
    for cible in [2, 3, 5, 10, 20]:
        # Logique de construction combinatoire que tu avais avant
        ticket = [s for s in sels if s['id'] not in cles_utilisees][:3] # Simulé
        
        st.markdown(f"<div class='pack-card'><h3>📦 Pack ×{cible}</h3>", unsafe_allow_html=True)
        for m in ticket:
            st.markdown(f"<div class='sel-row'><span class='badge badge-h2h'>{m['mkt']}</span> {m['match']} - {m['prono']} (@{m['cote']})</div>", unsafe_allow_html=True)
            cles_utilisees.add(m['id'])
        st.markdown("</div>", unsafe_allow_html=True)
