import streamlit as st
import requests

# Config épurée
st.set_page_config(page_title="BETCORE AI v5.0", page_icon="⚡", layout="wide")

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'

# 1. SELECTION STRICTE DES CHAMPIONNATS FIABLES (Évite les surprises)
TRUSTED_LEAGUES = [
    'soccer_epl',                  # Angleterre Premier League
    'soccer_la_liga_spain',         # Espagne LaLiga
    'soccer_italy_serie_a',         # Italie Serie A
    'soccer_germany_bundesliga',    # Allemagne Bundesliga
    'soccer_france_ligue_1',        # France Ligue 1
    'soccer_brazil_campeonato',     # Brésil Série A (Très actif)
    'soccer_uefa_champions_league', # Ligue des Champions
    'soccer_uefa_europa_league'     # Europa League
]

@st.cache_data(ttl=3600)  # Sauvegarde les données 1 heure pour ne pas griller le quota
def fetch_intelligent_data():
    all_valid_predictions = []
    
    # On scanne uniquement notre liste de confiance pour préserver l'API
    for league in TRUSTED_LEAGUES:
        url = f'https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,double_chance&oddsFormat=decimal'
        try:
            response = requests.get(url, timeout=7)
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    home_team = event.get('home_team')
                    away_team = event.get('away_team')
                    match_name = f"{home_team} vs {away_team}"
                    league_title = event.get('sport_title', 'Football')
                    
                    for bookmaker in event.get('bookmakers', []):
                        # On se base uniquement sur les leaders du marché mondial pour le consensus
                        if bookmaker['key'] in ['unibet', 'betclic', 'pinnacle']:
                            for market in bookmaker.get('markets', []):
                                for outcome in market.get('outcomes', []):
                                    cote = outcome.get('price', 1.0)
                                    outcome_name = outcome.get('name', '')
                                    
                                    # ── REGLES D'INTELLIGENCE MATHEMATIQUE STRICTES ──
                                    # Règle 1: On élimine les cotes trop basses (<1.38) qui gâchent les packs et n'ont pas de valeur
                                    # Règle 2: On élimine les cotes trop spéculatives (>2.10) pour les packs de confiance
                                    if cote < 1.38 or cote > 2.10:
                                        continue
                                    
                                    # Règle 3: Alerte piège à l'extérieur (Pénalisation si le favori se déplace)
                                    is_away_favorite = (outcome_name == away_team and cote < 1.60)
                                    
                                    # Calcul de l'indice de confiance BetCore (pondéré)
                                    base_prob = (1 / cote) * 100
                                    confidence_score = base_prob - 8 if is_away_favorite else base_prob
                                    
                                    # Traduction propre
                                    prono_clean = outcome_name
                                    if market['key'] == 'double_chance':
                                        if outcome_name == 'HomeOrDraw': prono_clean = f"1X ({home_team} ou Nul)"
                                        elif outcome_name == 'AwayOrDraw': prono_clean = f"X2 (Nul ou {away_team})"
                                        elif outcome_name == 'HomeOrAway': prono_clean = "12 (Pas de match nul)"

                                    uid = f"{event['id']}_{prono_clean}"
                                    
                                    all_valid_predictions.append({
                                        'id': event['id'],
                                        'match': match_name,
                                        'league': league_title,
                                        'prono': prono_clean,
                                        'cote': cote,
                                        'score': round(confidence_score, 1)
                                    })
        except:
            pass
            
    # Suppression des doublons et tri par le score d'intelligence le plus élevé
    unique_preds = {p['id']: p for p in sorted(all_valid_predictions, key=lambda x: x['score'], reverse=True)}
    return list(unique_preds.values())

# 2. CONSTRUCTEUR DE PACKS INTELLIGENTS (SANS AUCUN DOUBLON)
def build_smart_pack(predictions, target_odds):
    pack = []
    total_odds = 1.0
    
    for pred in predictions:
        if total_odds >= target_odds:
            break
        pack.append(pred)
        total_odds *= pred['cote']
        
    if total_odds >= (target_odds * 0.9):
        return pack, round(total_odds, 2)
    return [], 0.0

# ── INTERFACE GRAPHIQUE NATIVE ──
st.title("⚡ BETCORE INTELLIGENCE v5.0")
st.subheader("Filtre d'exclusion des pièges et sécurisation des packs")
st.divider()

data = fetch_intelligent_data()

if not data:
    st.warning("⚠️ Aucun match hautement sécurisé ne passe les filtres de l'IA en ce moment. Revenez plus tard ou attendez les matchs du week-end.")
else:
    col1, col2 = st.columns([3, 2], gap="large")
    
    with col1:
        st.header("📦 Packs Sécurisés Recommandés")
        
        for cible in [2.0, 3.5, 5.0]:
            pack_matches, final_cote = build_smart_pack(data, cible)
            if pack_matches:
                with st.container(border=True):
                    st.success(f"🎯 PACK OBJECTIF ×{cible} (Cote Réelle : {final_cote}×)")
                    for m in pack_matches:
                        st.markdown(f"**{m['match']}** | `{m['league']}`")
                        st.markdown(f"👉 Sélection : **{m['prono']}** | Cote : `@ {m['cote']}` (Indice de confiance : {m['score']}/100)")
                        st.divider()
            else:
                st.info(f"📦 Pack ×{cible} suspendu : Pas assez de matchs à très haute fiabilité aujourd'hui.")

    with col2:
        st.header("📋 Top Matchs Filtrés")
        for m in data[:6]:
            with st.container(border=True):
                st.markdown(f"⚽ **{m['match']}**")
                st.caption(f"{m['league']}")
                st.markdown(f"🔥 Sélection : **{m['prono']}** | `@ {m['cote']}`")
