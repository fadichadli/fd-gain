import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── CONFIGURATION & PACKS ────────────────────────────────────────────────────
API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20] # Tes objectifs de cote

st.set_page_config(page_title="WinHand AI", layout="wide")

# Injection CSS (Raccourci pour la lisibilité)
st.markdown("<style>.pack-card { background:#0d1220; padding:20px; border-radius:15px; margin-bottom:15px; border:1px solid #1a2540; }</style>", unsafe_allow_html=True)

# ─── FONCTION FETCH OPTIMISÉE (Évite le blocage) ──────────────────────────────
@st.cache_data(ttl=3600)
def fetch_selections():
    # On se limite aux ligues majeures pour garantir une réponse rapide
    ligues = ['soccer_france_ligue_one', 'soccer_england_premier_league', 'soccer_germany_bundesliga']
    all_matches = []
    
    for ligue in ligues:
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                for m in data:
                    # Extraction simplifiée pour garantir la donnée
                    all_matches.append({
                        'id': m['id'],
                        'match': f"{m['home_team']} vs {m['away_team']}",
                        'prono': m['bookmakers'][0]['markets'][0]['outcomes'][0]['name'],
                        'cote': m['bookmakers'][0]['markets'][0]['outcomes'][0]['price']
                    })
        except: continue
    return all_matches

# ─── LOGIQUE DE CONSTRUCTION DE PACKS ─────────────────────────────────────────
def construire_pack(data, cible):
    # Algorithme glouton simple pour trouver des cotes proches de la cible
    combinaison = []
    cote_actuelle = 1.0
    for match in data:
        if cote_actuelle * match['cote'] <= cible * 1.2: # Tolérance 20%
            combinaison.append(match)
            cote_actuelle *= match['cote']
        if cote_actuelle >= cible * 0.9:
            break
    return combinaison, round(cote_actuelle, 2)

# ─── UI PRINCIPALE ────────────────────────────────────────────────────────────
st.title("🏆 WinHand AI - Générateur de Packs")

if st.button("Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

data = fetch_selections()

if not data:
    st.error("Aucune donnée récupérée. Vérifiez votre quota API ou votre connexion.")
else:
    st.success(f"{len(data)} matchs analysés avec succès.")
    
    # Affichage des packs 2, 3, 5, 10, 20
    for cible in PACK_CIBLES:
        pack, cote_reelle = construire_pack(data, cible)
        
        with st.expander(f"📦 Pack Objectif ×{cible} (Cote réelle : {cote_reelle}×)", expanded=True):
            for item in pack:
                st.markdown(f"**{item['match']}** : {item['prono']} (@{item['cote']})")
