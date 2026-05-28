import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Configuration de la page
st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="centered")

# CSS personnalisé pour un look professionnel
st.markdown("""
<style>
    .pack-card { background-color: #0f172a; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #38bdf8; color: white; }
    .match-card { background-color: #1e293b; border-radius: 8px; padding: 12px; margin-top: 8px; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
MARKETS     = 'h2h,double_chance,totals,btts'
PACK_CIBLES = [2, 3, 5, 10, 20]
FENETRE_H   = 168

st.title("🏆 WinHand AI - Multi-Marchés")

# ─── 1. FETCH ET ANALYSE ──────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_tous_les_matchs():
    url_sports = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r_sports = requests.get(url_sports, timeout=10)
        toutes_ligues = [s['key'] for s in r_sports.json() if 'soccer' in s.get('group', '').lower()]
    except: return []

    raw_total = {}
    for ligue in toutes_ligues[:15]: # Scan 15 ligues
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={MARKETS}&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=5)
            for m in r.json(): raw_total[m['id']] = m
        except: continue

    matchs = []
    for match in raw_total.values():
        cotes_par_marche = defaultdict(lambda: defaultdict(list))
        for bk in match.get('bookmakers', []):
            for mkt in bk.get('markets', []):
                for out in mkt.get('outcomes', []):
                    name = f"{out['name']} {out.get('point', '')}" if mkt.get('key') == 'totals' else out['name']
                    cotes_par_marche[mkt.get('key')][name].append(out['price'])
        
        # Sélection simplifiée pour éviter le blocage
        for mkt_key, issues in cotes_par_marche.items():
            for issue_name, cotes in issues.items():
                cote_moy = sum(cotes) / len(cotes)
                matchs.append({
                    'id': match['id'], 'match': f"{match['home_team']} vs {match['away_team']}",
                    'prono': f"{mkt_key.upper()} : {issue_name}", 'cote': round(cote_moy, 2), 'prob': 70 # Valeur de test
                })
    return matchs

# ─── 2. CONSTRUIRE TICKET ────────────────────────────────────────────────────
def construire_ticket(matchs_dispo, cote_cible, ids_utilises):
    candidats = [m for m in matchs_dispo if m['id'] not in ids_utilises and m['cote'] <= 1.65][:15]
    for r in range(1, 6):
        for combo in itertools.combinations(candidats, r):
            cote_tot = 1.0
            for m in combo: cote_tot *= m['cote']
            if cote_cible * 0.9 <= cote_tot <= cote_cible * 1.3:
                return list(combo), round(cote_tot, 2)
    return [], 0.0

# ─── 3. AFFICHAGE ─────────────────────────────────────────────────────────────
liste_matchs = fetch_tous_les_matchs()

if not liste_matchs:
    st.warning("🔄 Analyse en cours... Actualisez si nécessaire.")
else:
    ids_utilises = set()
    for cible in PACK_CIBLES:
        ticket, cote = construire_ticket(liste_matchs, cible, ids_utilises)
        if ticket:
            st.markdown(f"<div class='pack-card'><h3>📦 Pack ×{cible} (Cote: {cote})</h3>", unsafe_allow_html=True)
            for m in ticket:
                st.markdown(f"<div class='match-card'><b>{m['match']}</b><br>👉 {m['prono']} (@{m['cote']})</div>", unsafe_allow_html=True)
                ids_utilises.add(m['id'])
            st.markdown("</div>", unsafe_allow_html=True)
