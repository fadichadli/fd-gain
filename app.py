import streamlit as st
import requests

# Configuration de l'interface
st.set_page_config(page_title="BETCORE AI v6.0", page_icon="🌍", layout="wide")

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

# 1. DETECTION DES LIGUES ACTIVES
@st.cache_data(ttl=3600)
def get_live_active_soccer_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            all_leagues = [sport['key'] for sport in r.json() if sport.get('group') == 'Soccer' and not sport.get('has_outrights')]
            priority_keywords = ['brazil', 'usa', 'mls', 'chile', 'argentina', 'league']
            sorted_leagues = sorted(all_leagues, key=lambda x: any(kw in x for kw in priority_keywords), reverse=True)
            return sorted_leagues[:10] # On limite à 10 pour préserver le quota
    except:
        pass
    return ['soccer_brazil_campeonato', 'soccer_usa_mls']

# 2. ANALYSE ET FILTRAGE GLOBAL (Le correctif est ici)
@st.cache_data(ttl=1800)
def fetch_global_pool(active_leagues):
    all_valid_predictions = []
    
    for league in active_leagues:
        # On ouvre aux régions US, UK et EU pour capter un maximum de bookmakers internationaux
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu,uk,us&markets=h2h,double_chance&oddsFormat=decimal'
        try:
            response = requests.get(url, timeout=7)
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    home_team = event.get('home_team')
                    away_team = event.get('away_team')
                    match_name = f"{home_team} vs {away_team}"
                    league_title = event.get('sport_title', league.upper())
                    
                    if not event.get('bookmakers'):
                        continue
                        
                    # On prend le premier bookmaker qui propose des cotes pour ce match (bypass du filtre strict)
                    bookmaker = event['bookmakers'][0]
                    
                    for market in bookmaker.get('markets', []):
                        for outcome in market.get('outcomes', []):
                            cote = outcome.get('price', 1.0)
                            outcome_name = outcome.get('name', '')
                            
                            # FILTRE DE SÉCURITÉ : Cotes raisonnables
                            if cote < 1.30 or cote > 2.30:
                                continue
                                
                            # ÉVALUATION DU RISQUE 
                            is_away_favorite = (outcome_name == away_team and cote < 1.65)
                            base_prob = (1 / cote) * 100
                            score_fiabilite = base_prob - 10 if is_away_favorite else base_prob
                            
                            # Traduction propre
                            prono_clean = outcome_name
                            if market['key'] == 'double_chance':
                                if outcome_name == 'HomeOrDraw': prono_clean = "1X (Victoire Domicile ou Nul)"
                                elif outcome_name == 'AwayOrDraw': prono_clean = f"X2 (Nul ou Victoire {away_team})"
                                elif outcome_name == 'HomeOrAway': prono_clean = "12 (Pas de match nul)"

                            uid = f"{event['id']}_{prono_clean}"
                            
                            all_valid_predictions.append({
                                'uid': uid,
                                'match_id': event['id'],
                                'match': match_name,
                                'league': league_title,
                                'prono': prono_clean,
                                'cote': cote,
                                'score': round(score_fiabilite, 1),
                                'bookmaker': bookmaker['title']
                            })
        except:
            continue
            
    # Nettoyage pour garder la meilleure option par pronostic
    pool_nettoye = {}
    for p in all_valid_predictions:
        if p['uid'] not in pool_nettoye or p['score'] > pool_nettoye[p['uid']]['score']:
            pool_nettoye[p['uid']] = p
            
    return sorted(list(pool_nettoye.values()), key=lambda x: x['score'], reverse=True)

# 3. CRÉATION DES PACKS SÉCURISÉS SANS DOUBLONS
def build_secure_pack(predictions, target_odds):
    pack = []
    total_odds = 1.0
    used_match_ids = set() 
    
    for pred in predictions:
        if total_odds >= target_odds:
            break
        # Bloque les matchs déjà présents dans le pack pour éviter les doublons
        if pred['match_id'] in used_match_ids:
            continue
            
        pack.append(pred)
        total_odds *= pred['cote']
        used_match_ids.add(pred['match_id'])
        
    if total_odds >= (target_odds * 0.85):
        return pack, round(total_odds, 2)
    return [], 0.0

# ─── INTERFACE UTILISATEUR ──────────────────────────────────────────────────

st.title("🌍 BETCORE AI - GLOBAL EDITION v6.0")
st.subheader("Analyse multi-marchés internationale et création de packs sécurisés")
st.divider()

with st.spinner("Analyse des flux mondiaux en cours..."):
    active_leagues = get_live_active_soccer_leagues()
    data_pool = fetch_global_pool(active_leagues)

if not data_pool:
    st.error("⚠️ Aucun match n'a pu être extrait. Vérifiez votre connexion ou réessayez plus tard.")
else:
    st.success(f"✅ {len(data_pool)} opportunités qualifiées détectées sur le marché mondial.")
    
    col1, col2 = st.columns([3, 2], gap="large")
    
    with col1:
        st.header("📦 Packs Combinés")
        
        for cible in [2.0, 3.5, 5.0]:
            pack_matches, final_cote = build_secure_pack(data_pool, cible)
            
            if pack_matches:
                with st.container(border=True):
                    st.markdown(f"### 🎯 PACK OBJECTIF ×{cible}")
                    st.caption(f"Cote Réelle : {final_cote}× | {len(pack_matches)} sélections uniques")
                    
                    for m in pack_matches:
                        st.markdown(f"**{m['match']}** — *{m['league']}*")
                        st.markdown(f"👉 Choix : **{m['prono']}** | Cote : `@ {m['cote']}` *(via {m['bookmaker']})*")
                        st.divider()
            else:
                st.info(f"📦 Pack ×{cible} indisponible : volume de matchs insuffisant.")

    with col2:
        st.header("📋 Flux Principal")
        st.caption("Top 10 des sélections classées par indice de fiabilité")
        
        for m in data_pool[:10]:
            with st.container(border=True):
                st.markdown(f"⚽ **{m['match']}**")
                st.caption(f"{m['league']} | {m['bookmaker']}")
                st.markdown(f"🔥 Choix : **{m['prono']}** | `@ {m['cote']}`")
