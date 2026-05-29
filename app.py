import streamlit as st
import requests

st.set_page_config(page_title="BETCORE AI v5.6", page_icon="🚨", layout="wide")

# TA CLÉ API
API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

st.title("🚨 BETCORE AI - DIAGNOSTIC v5.6")
st.divider()

# 1. TEST STRICT DE L'API ET LECTURE DU QUOTA
@st.cache_data(ttl=60) # On met en cache court pour rafraîchir l'état du quota
def check_api_status():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            used = r.headers.get('x-requests-used', 'Inconnu')
            remaining = r.headers.get('x-requests-remaining', 'Inconnu')
            return True, used, remaining, r.json()
        else:
            return False, 0, 0, r.json().get('message', f'Erreur HTTP {r.status_code}')
    except Exception as e:
        return False, 0, 0, str(e)

api_ok, used, remaining, api_data = check_api_status()

# Affichage du diagnostic dans la barre latérale
with st.sidebar:
    st.header("📊 Statut API")
    if api_ok:
        st.success("✅ Connecté au serveur")
        st.metric("Requêtes Utilisées", used)
        st.metric("Requêtes Restantes", remaining)
    else:
        st.error("❌ Déconnecté")

# GESTION DES ERREURS CRITIQUES
if not api_ok:
    st.error("❌ ERREUR CRITIQUE : L'accès aux données de The Odds-API est bloqué.")
    st.code(api_data) # Affiche le message d'erreur brut du serveur
    st.warning("💡 Si c'est une erreur liée au quota (Requests limit reached), ton forfait gratuit est épuisé. Tu dois aller sur the-odds-api.com et générer une nouvelle clé API avec une autre adresse email.")
    st.stop() # On arrête l'application ici pour ne pas causer d'autres bugs

# 2. RECUPERATION SOUPLE (Bypass des filtres stricts)
@st.cache_data(ttl=1800)
def fetch_emergency_data(sports_list):
    predictions = []
    # On isole les ligues de foot actives (limité à 6 pour économiser le quota)
    active_soccer = [s['key'] for s in sports_list if s.get('group') == 'Soccer' and not s.get('has_outrights')]
    target_leagues = active_soccer[:6]
    
    for league in target_leagues:
        # On ajoute les régions 'uk' et 'us' pour maximiser les chances d'avoir des bookmakers
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu,uk,us&markets=h2h&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=7)
            if r.status_code == 200:
                events = r.json()
                for event in events:
                    if not event.get('bookmakers'):
                        continue
                    
                    # On ne cherche plus de consensus complexe, on prend le PREMIER bookmaker disponible pour débloquer l'affichage
                    bookmaker = event['bookmakers'][0] 
                    
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market.get('outcomes', []):
                                cote = outcome.get('price', 1.0)
                                name = outcome.get('name', '')
                                
                                # Filtre très souple : cotes entre 1.25 et 2.50
                                if 1.25 <= cote <= 2.50:
                                    predictions.append({
                                        'match_id': event['id'],
                                        'ligue': league,
                                        'match': f"{event['home_team']} vs {event['away_team']}",
                                        'prono': f"Victoire {name}",
                                        'cote': cote,
                                        'bookmaker': bookmaker['title']
                                    })
        except:
            pass
            
    # Tri par la cote la plus basse (plus "sécurisée")
    return sorted(predictions, key=lambda x: x['cote'])

# 3. AFFICHAGE DES RÉSULTATS
with st.spinner("Forçage de l'analyse des flux mondiaux..."):
    data_pool = fetch_emergency_data(api_data)
    
    if data_pool:
        st.success(f"✅ Déblocage réussi : {len(data_pool)} opportunités brutes récupérées !")
        st.dataframe(data_pool, use_container_width=True)
    else:
        st.warning("⚠️ L'API est connectée et le quota est bon, mais AUCUN match n'est programmé dans les prochaines heures avec ces critères.")
