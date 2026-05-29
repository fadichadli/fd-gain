import streamlit as st
import requests

st.set_page_config(page_title="BETCORE AI FINAL", layout="wide")

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

# Cette version simplifie le filtrage au maximum pour garantir l'affichage
@st.cache_data(ttl=600)
def fetch_data_permissive():
    # On cible une liste large de ligues
    leagues = ['soccer_brazil_campeonato', 'soccer_usa_mls', 'soccer_chile_campeonato', 'soccer_conmebol_copa_sudamericana']
    all_data = []
    
    for league in leagues:
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu,uk,us&markets=h2h&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                events = r.json()
                for e in events:
                    if e.get('bookmakers'):
                        # On prend le 1er bookmaker trouvé sans faire de tri complexe
                        bm = e['bookmakers'][0]
                        outcome = bm['markets'][0]['outcomes'][0]
                        all_data.append({
                            'match': f"{e['home_team']} vs {e['away_team']}",
                            'prono': outcome['name'],
                            'cote': outcome['price'],
                            'bookmaker': bm['title']
                        })
        except: continue
    return all_data

st.title("🚀 BETCORE AI - MODE PERMISSIF")
data = fetch_data_permissive()

if data:
    st.success(f"Récupération réussie : {len(data)} matchs trouvés.")
    st.table(data) # Affichage sous forme de tableau simple pour éviter les erreurs de rendu
else:
    st.warning("Aucune donnée trouvée. Vérifiez que la clé API est bien active.")
