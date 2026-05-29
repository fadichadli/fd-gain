import streamlit as st
import requests

# Configuration de l'interface
st.set_page_config(page_title="BETCORE AI v5.5", page_icon="⚽", layout="wide")

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

# 1. DETECTION DYNAMIQUE DES LIGUES ACTIVES (Évite le piège des championnats à l'arrêt)
@st.cache_data(ttl=3600)
def get_live_active_soccer_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            # On récupère toutes les ligues de football (Soccer) qui ont des matchs programmés
            all_leagues = [sport['key'] for sport in r.json() if sport.get('group') == 'Soccer' and not sport.get('has_outrights')]
            
            # On priorise les championnats majeurs ou ultra-actifs actuellement (ex: Brésil, USA, Islande, etc.)
            priority_keywords = ['brazil', 'usa', 'mls', 'premium', 'league', 'championship']
            sorted_leagues = sorted(all_leagues, key=lambda x: any(kw in x for kw in priority_keywords), reverse=True)
            return sorted_leagues
    except:
        pass
    return ['soccer_brazil_campeonato', 'soccer_usa_mls'] # Secours automatique

# 2. ANALYSE ET FILTRAGE INTELLIGENT DU POOL DE MATCHS
@st.cache_data(ttl=1800)
def fetch_intelligent_pool(active_leagues):
    all_valid_predictions = []
    
    # On limite le scan aux 12 premières ligues actives pour protéger ton quota API
    leagues_to_scan = active_leagues[:12]
    
    for league in leagues_to_scan:
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,double_chance&oddsFormat=decimal'
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    home_team = event.get('home_team')
                    away_team = event.get('away_team')
                    match_name = f"{home_team} vs {away_team}"
                    league_title = event.get('sport_title', league.upper())
                    
                    for bookmaker in event.get('bookmakers', []):
                        if bookmaker['key'] in ['unibet', 'betclic', 'pinnacle']:
                            for market in bookmaker.get('markets', []):
                                for outcome in market.get('outcomes', []):
                                    cote = outcome.get('price', 1.0)
                                    outcome_name = outcome.get('name', '')
                                    
                                    # FILTRE DE SÉCURITÉ : Exclusion des cotes trop basses (pièges) ou trop hautes
                                    if cote < 1.35 or cote > 2.20:
                                        continue
                                        
                                    # ÉVALUATION DU RISQUE : Pénalisation automatique du favori s'il joue à l'extérieur
                                    is_away_favorite = (outcome_name == away_team and cote < 1.65)
                                    base_prob = (1 / cote) * 100
                                    score_fiabilite = base_prob - 10 if is_away_favorite else base_prob
                                    
                                    # Traduction et mise au propre des libellés
                                    prono_clean = outcome_name
                                    if market['key'] == 'double_chance':
                                        if outcome_name == 'HomeOrDraw': prono_clean = "1X (Victoire Domicile ou Nul)"
                                        elif outcome_name == 'AwayOrDraw': prono_clean = f"X2 (Nul ou Victoire {away_team})"
                                        elif outcome_name == 'HomeOrAway': prono_clean = "12 (Pas de match nul)"

                                        # ID Unique par PRONOSTIC pour ne pas écraser les différentes options d'un même match
                                    uid = f"{event['id']}_{prono_clean}"
                                    
                                    all_valid_predictions.append({
                                        'uid': uid,
                                        'match_id': event['id'],
                                        'match': match_name,
                                        'league': league_title,
                                        'prono': prono_clean,
                                        'cote': cote,
                                        'score': round(score_fiabilite, 1)
                                    })
        except:
            pass
            
    # Filtrage des doublons stricts pour le flux général
    pool_nettoye = {}
    for p in all_valid_predictions:
        if p['uid'] not in pool_nettoye or p['score'] > pool_nettoye[p['uid']]['score']:
            pool_nettoye[p['uid']] = p
            
    return sorted(list(pool_nettoye.values()), key=lambda x: x['score'], reverse=True)

# 3. ALGORITHME DE SÉCURISATION DES PACKS (SANS AUCUN DOUBLON DE MATCH)
def build_secure_pack(predictions, target_odds):
    pack = []
    total_odds = 1.0
    used_match_ids = set() # Sécurité absolue : un match ne peut pas être utilisé deux fois dans le même pack
    
    for pred in predictions:
        if total_odds >= target_odds:
            break
        # Si le match est déjà utilisé dans ce pack, on passe au suivant
        if pred['match_id'] in used_match_ids:
            continue
            
        pack.append(pred)
        total_odds *= pred['cote']
        used_match_ids.add(pred['match_id'])
        
    if total_odds >= (target_odds * 0.85):
        return pack, round(total_odds, 2)
    return [], 0.0

# ─── INTERFACE UTILISATEUR ──────────────────────────────────────────────────

st.title("⚡ BETCORE AI - VERSION 5.5")
st.subheader("Analyse prédictive multi-ligues dynamique et anti-doublons")
st.divider()

# Analyse des ligues disponibles en temps réel
active_leagues = get_live_active_soccer_leagues()
data_pool = fetch_intelligent_pool(active_leagues)

if not data_pool:
    st.warning("⚠️ Aucun match ne valide les critères de sécurité de l'IA actuellement. Les bases de données se synchronisent.")
else:
    col1, col2 = st.columns([3, 2], gap="large")
    
    with col1:
        st.header("📦 Packs Combinés Sécurisés")
        
        for cible in [2.0, 3.5, 5.0]:
            pack_matches, final_cote = build_secure_pack(data_pool, cible)
            
            if pack_matches:
                with st.container(border=True):
                    st.success(f"🎯 PACK OBJECTIF ×{cible} (Cote Réelle : {final_cote}×)")
                    st.caption(f"Composé de {len(pack_matches)} matchs différents rigoureusement sélectionnés.")
                    
                    for m in pack_matches:
                        st.markdown(f"**{m['match']}** — *{m['league']}*")
                        st.markdown(f"👉 Choix : **{m['prono']}** | Cote : `@ {m['cote']}` *(Indice de confiance : {m['score']}/100)*")
                        st.divider()
            else:
                st.info(f"📦 Pack ×{cible} momentanément indisponible : volume de matchs sécurisés insuffisant pour atteindre cet objectif.")

    with col2:
        st.header("📋 Flux des Opportunités Détectées")
        st.caption("Sélections éligibles classées par indice de robustesse mathématique")
        
        for m in data_pool[:10]:
            with st.container(border=True):
                st.markdown(f"⚽ **{m['match']}**")
                st.caption(f"{m['league']}")
                st.markdown(f"🔥 Choix : **{m['prono']}** | Option cotée à `@ {m['cote']}`")
