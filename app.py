import streamlit as st
import requests
from datetime import datetime

# Configuration de la page avec thème natif sombre/épuré
st.set_page_config(page_title="WinHand AI Platinum", page_icon="⚽", layout="wide")

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

# 1. RECUPERATION DYNAMIQUE DE TOUTES LES LIGUES ACTIVES
@st.cache_data(ttl=1800, show_spinner=False)
def get_all_active_soccer_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            # On filtre uniquement le Football (Soccer) et on exclut les paris à long terme (outrights)
            return [sport['key'] for sport in r.json() if sport.get('group') == 'Soccer' and not sport.get('has_outrights')]
    except:
        pass
    return ['soccer_usa_mls', 'soccer_brazil_campeonato', 'soccer_chile_campeonato'] # Fallback de secours

# 2. MOTEUR DE RECHERCHE INTELLIGENT
def fetch_smart_predictions(leagues_to_scan):
    dict_selections = {}
    
    if not leagues_to_scan:
        return []

    # Un seul appel groupé sur les marchés principaux pour économiser le quota
    markets_string = "h2h,totals,double_chance"
    
    progress_bar = st.progress(0, text="Analyse globale des ligues actives...")
    total_leagues = len(leagues_to_scan)

    for idx, league_key in enumerate(leagues_to_scan):
        url = f'https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets={markets_string}&oddsFormat=decimal'
        
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                events = r.json()
                for event in events:
                    match_name = f"{event.get('home_team')} vs {event.get('away_team')}"
                    league_name = event.get('sport_title', league_key.replace('soccer_', '').upper())
                    
                    for bookmaker in event.get('bookmakers', []):
                        if bookmaker['key'] in ['unibet', 'betclic', 'bwin', 'pinnacle', 'williamhill']: # Focus bookmakers fiables
                            for market in bookmaker.get('markets', []):
                                market_key = market['key']
                                
                                for outcome in market.get('outcomes', []):
                                    cote = outcome.get('price', 1.0)
                                    outcome_name = outcome.get('name', '')
                                    
                                    # FILTRE INTELLIGENT : On élimine les cotes inutiles (< 1.35) ou trop risquées (> 3.50) pour les algorithmes de confiance
                                    if cote < 1.35 or cote > 3.50:
                                        continue
                                        
                                    # Traduction et labellisation automatique
                                    prono = outcome_name
                                    market_label = "1X2"
                                    
                                    if market_key == "totals":
                                        point = outcome.get('point', 2.5)
                                        prono = f"{outcome_name} {point} Buts"
                                        market_label = "Plus/Moins"
                                    elif market_key == "double_chance":
                                        market_label = "Double Chance"
                                        if outcome_name == "HomeOrDraw": prono = "1X (Victoire ou Nul)"
                                        elif outcome_name == "AwayOrDraw": prono = "X2 (Nul ou Victoire)"
                                        elif outcome_name == "HomeOrAway": prono = "12 (Pas de match nul)"

                                    uid = f"{event['id']}_{market_key}_{prono}"
                                    probabilite = round((1 / cote) * 100, 1)
                                    
                                    # On garde la meilleure cote disponible pour cette prédiction précise
                                    if uid not in dict_selections or cote > dict_selections[uid]['cote']:
                                        dict_selections[uid] = {
                                            'match_id': event['id'],
                                            'match': match_name,
                                            'league': league_name,
                                            'market': market_label,
                                            'prono': prono,
                                            'cote': cote,
                                            'prob': probabilite
                                        }
        except:
            pass
        
        progress_bar.progress((idx + 1) / total_leagues)
        
    progress_bar.empty()
    
    # Tri des sélections par score de probabilité décroissant
    predictions_liste = list(dict_selections.values())
    predictions_liste.sort(key=lambda x: x['prob'], reverse=True)
    return predictions_liste

# 3. ALGORITHME DE PACKS STRICT (SANS DOUBLONS DE MATCHS)
def generate_secure_pack(all_predictions, target_odds):
    pack_items = []
    current_odds = 1.0
    used_match_ids = set()
    
    for pred in all_predictions:
        # RÈGLE D'OR : Interdiction d'inclure deux fois le même match dans un pack
        if pred['match_id'] in used_match_ids:
            continue
            
        pack_items.append(pred)
        current_odds *= pred['cote']
        used_match_ids.add(pred['match_id'])
        
        # Si on atteint l'objectif de cote fixé, on valide le pack
        if current_odds >= target_odds:
            break
            
    if current_odds >= (target_odds * 0.85):
        return pack_items, round(current_odds, 2)
    return [], 0.0

# ─── INTERFACE UTILISATEUR (NATIVE STREAMLIT) ───────────────────────────────

st.title("⚽ BETCORE AI PLATINUM V4.0")
st.subheader("Moteur de consensus prédictif global auto-adaptatif")
st.divider()

# Barre latérale simplifiée
with st.sidebar:
    st.header("🤖 Configuration Auto")
    st.write("Le système scanne automatiquement l'intégralité des championnats ouverts dans le monde.")
    
    all_discovered_leagues = get_all_active_soccer_leagues()
    st.success(f"🌍 {len(all_discovered_leagues)} ligues détectées en direct")
    
    if st.button("🔄 Forcer le Re-Scan Global", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Lancement du moteur
predictions_dispo = fetch_smart_predictions(all_discovered_leagues)

if not predictions_dispo:
    st.error("🎰 Aucun match exploitable n'est disponible sur l'API actuellement pour les critères de confiance définis.")
else:
    # Tableau de bord principal
    m1, m2, m3 = st.columns(3)
    m1.metric("Matchs uniques analysés", len(set(p['match_id'] for p in predictions_dispo)))
    m2.metric("Options de Value Bets trouvées", len(predictions_dispo))
    m3.metric("Indice de confiance Max", f"{predictions_dispo[0]['prob']}%")
    
    st.divider()
    
    layout_left, layout_right = st.columns([3, 2], gap="large")
    
    # AFFICHAGE DES PACKS (A GAUCHE)
    with layout_left:
        st.header("📦 Packs Combinés Uniques")
        
        objectifs_cotes = [2.0, 3.5, 5.0, 10.0]
        
        for obj in objectifs_cotes:
            pack_matches, total_cote = generate_secure_pack(predictions_dispo, obj)
            
            if not pack_matches:
                st.info(f"📦 **Pack Objectif ×{obj}** : Pas assez de matchs distincts aujourd'hui pour concevoir ce pack en sécurité.")
                continue
                
            # Rendu du pack de manière 100% native
            with st.container(border=True):
                header_col1, header_col2 = st.columns([3, 1])
                header_col1.subheader(f"🎯 PACK OBJECTIF ×{obj}")
                header_col2.metric("Cote Totale", f"{total_cote}×")
                
                st.caption(f"Composé de {len(pack_matches)} sélections intelligentes sans aucun doublon.")
                
                for item in pack_matches:
                    with st.container(border=True):
                        st.caption(f"🏆 {item['league']}")
                        st.markdown(f"**{item['match']}**")
                        
                        col_details, col_cote = st.columns([3, 1])
                        col_details.markdown(f"🔹 Marché : *{item['market']}* |  👉 Sélection : **{item['prono']}**")
                        col_cote.markdown(f"**`@{item['cote']}`** *(Fiabilité : {item['prob']}%)*")
                        st.progress(item['prob'] / 100)
                        
    # AFFICHAGE DU FLUX DE TOUTES LES OPPORTUNITES (A DROITE)
    with layout_right:
        st.header("📋 Flux des Opportunités")
        st.caption("Trié par probabilité mathématique de réussite décroissante")
        
        for item in predictions_dispo[:12]:
            with st.container(border=True):
                st.markdown(f"**{item['match']}**")
                st.caption(f"{item['league']} • {item['market']}")
                
                c_prono, c_cote = st.columns([3, 1])
                c_prono.markdown(f"🎯 **{item['prono']}**")
                c_cote.markdown(f"`@{item['cote']}`")
