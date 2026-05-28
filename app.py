import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── CONFIGURATION DE LA PAGE STREAMLIT ────────────────────────────────────────
st.set_page_config(
    page_title="BetCore AI Platinum",
    page_icon="🤖",
    layout="centered", # Centré pour un rendu parfait sur écran de smartphone
    initial_sidebar_state="collapsed"
)

# Style CSS personnalisé pour donner un look "App Mobile VIP"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #1f2937;
        border-radius: 8px;
        color: #9ca3af;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #059669 !important; 
        color: white !important;
        font-weight: bold;
    }
    .pack-box {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
    }
    .match-card {
        background-color: #111827;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 8px 0;
    }
    </style>
""", unsafe_unsafe_rendering=True)

# ─── CONFIG BACKEND ────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
MARKETS     = 'h2h'
PACK_CIBLES = [2, 3, 5, 10, 20]
FENETRE_H   = 168

# ─── MOTEUR DE DONNÉES (FONCTIONS REPRISES ET SÉCURISÉES) ──────────────────────
@st.cache_data(ttl=1800) # Cache de 30 minutes pour économiser tes requêtes API
def fetch_tous_les_matchs_ui():
    url_sports = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r_sports = requests.get(url_sports, timeout=10)
        r_sports.raise_for_status()
        toutes_ligues = [
            s['key'] for s in r_sports.json() 
            if 'soccer' in s.get('group', '').lower() or 'soccer' in s.get('key', '').lower()
        ]
    except Exception:
        return []

    if not toutes_ligues:
        return []

    raw_total = {}
    ligues_a_interroger = toutes_ligues[:15]

    for ligue in ligues_a_interroger:
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={MARKETS}&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=12)
            if r.status_code == 401: break
            r.raise_for_status()
            for m in r.json():
                raw_total[m['id']] = m
        except Exception:
            continue

    maintenant  = datetime.now(timezone.utc)
    fin_fenetre = maintenant + timedelta(hours=FENETRE_H)
    matchs      = []

    for match in raw_total.values():
        try:
            date_match = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
        except ValueError: continue

        if not (maintenant - timedelta(minutes=15) <= date_match <= fin_fenetre):
            continue

        home, away, league = match.get('home_team', ''), match.get('away_team', ''), match.get('sport_title', 'Inconnu')
        delta_j = (date_match.date() - maintenant.date()).days
        label_date = f"Auj. {date_match.strftime('%H:%M')}" if delta_j == 0 else (f"Dem. {date_match.strftime('%H:%M')}" if delta_j == 1 else date_match.strftime('%d/%m %H:%M'))

        cotes_par_issue = defaultdict(list)
        for bk in match.get('bookmakers', []):
            for mkt in bk.get('markets', []):
                if mkt.get('key') == 'h2h':
                    for out in mkt.get('outcomes', []):
                        cotes_par_issue[out['name']].append(out['price'])

        if not cotes_par_issue: continue

        selections = []
        total_prob_brut = 0
        for issue, cotes in cotes_par_issue.items():
            cote_moy = round(sum(cotes) / len(cotes), 3)
            prob_brut = 1 / cote_moy
            total_prob_brut += prob_brut
            selections.append({'equipe': issue, 'cote': cote_moy, 'prob': prob_brut, 'nb_bk': len(cotes)})

        for s in selections:
            prob_corr = s['prob'] / total_prob_brut
            bonus_consensus = min(s['nb_bk'] / 12.0, 0.15)
            s['score_ia'] = round(prob_corr + bonus_consensus, 4)
            s['prob_pct'] = round(prob_corr * 100, 1)

        selections.sort(key=lambda x: x['score_ia'], reverse=True)
        best = selections[0]

        matchs.append({
            'id': match['id'], 'match': f"{home} vs {away}", 'league': league, 'date': label_date,
            'prono': best['equipe'], 'cote': best['cote'], 'prob': best['prob_pct']
        })

    matchs.sort(key=lambda x: x['prob'], reverse=True)
    return matchs

def construire_ticket(matchs_dispo, cote_cible, ids_utilises):
    candidats = [m for m in matchs_dispo if m['id'] not in ids_utilises and m['cote'] <= 1.65][:20]
    if not candidats: return [], 0.0

    meilleur = []
    meilleure_cote = 0.0
    meilleure_securite_moyenne = 0.0

    for r in range(1, min(8, len(candidats) + 1)):
        for combo in itertools.combinations(candidats, r):
            cote_tot = 1.0
            for m in combo: cote_tot *= m['cote']

            if not (cote_cible * 0.80 <= cote_tot <= cote_cible * 1.50): continue
            securite_moyenne = sum(m['prob'] for m in combo) / len(combo)

            if securite_moyenne > meilleure_securite_moyenne:
                meilleure_securite_moyenne = securite_moyenne
                meilleure_cote = round(cote_tot, 2)
                meilleur = list(combo)
            elif abs(securite_moyenne - meilleure_securite_moyenne) < 0.01:
                if abs(cote_tot - cote_cible) < abs(meilleure_cote - cote_cible):
                    meilleure_cote = round(cote_tot, 2)
                    meilleur = list(combo)

    return meilleur, meilleure_cote

# ─── INTERFACE GRAPHIQUE (UI) ──────────────────────────────────────────────────
st.title("🤖 BETCORE AI PLATINUM")
st.caption("Analyses algorithmiques basées sur le consensus mondial des bookmakers.")

# Bouton de rafraîchissement manuel
if st.button("🔄 Actualiser les pronostics", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Chargement de la data
with st.spinner("Analyse du marché mondial en cours..."):
    matchs_analyses = fetch_tous_les_matchs_ui()

if not matchs_analyses:
    st.error("Aucun match de football disponible ou erreur de clé API.")
else:
    # Création des onglets pour une navigation fluide sur mobile
    tab1, tab2 = st.tabs(["🎯 PACKS SÉCURISÉS", "📊 TOUS LES MATCHS"])

    # --- ONGLET 1 : LES PACKS ---
    with tab1:
        ids_utilises = set()
        
        for cible in PACK_CIBLES:
            ticket, cote_reelle = construire_ticket(matchs_analyses, cible, ids_utilises)
            
            # Conteneur principal du pack
            with st.container():
                st.markdown(f"<div class='pack-box'>", unsafe_allow_html=True)
                
                # En-tête du pack avec colonnes (Cible vs Cote Réelle)
                col_title, col_stat = st.columns([2, 1])
                with col_title:
                    st.subheader(f"📦 Pack Objectif ×{cible}")
                with col_stat:
                    if ticket:
                        st.metric(label="Cote Finale", value=f"×{cote_reelle}")
                
                if not ticket:
                    st.info("⚠️ Aucun pack ultra-fiable disponible pour cet objectif actuellement.")
                else:
                    # Affichage de chaque match du pack sous forme de sous-carte
                    for m in ticket:
                        st.markdown(f"""
                            <div class='match-card'>
                                <span style='color: #10b981; font-weight: bold;'>⚽ {m['match']}</span><br>
                                <small style='color: #9ca3af;'>🏆 {m['league']} | 📅 {m['date']}</small><br>
                                <div style='display: flex; justify-content: space-between; margin-top: 5px;'>
                                    <span>👉 Prono : <b>{m['prono']}</b></span>
                                    <span style='color: #34d399;'>@{m['cote']} ({m['prob']}%)</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        ids_utilises.add(m['id'])
                
                st.markdown("</div>", unsafe_allow_html=True)

    # --- ONGLET 2 : LA BASE DE DONNÉES EN DIRECT ---
    with tab2:
        st.write(f"💡 Liste des **{len(matchs_analyses)}** matchs classés par ordre de fiabilité brute :")
        for m in matchs_analyses:
            with st.expander(f"🟢 {m['match']} (@{m['cote']})"):
                st.write(f"**Compétition :** {m['league']}")
                st.write(f"**Date du coup d'envoi :** {m['date']}")
                st.write(f"**Conseil de l'IA :** Victoire de **{m['prono']}**")
                st.write(f"**Indice de confiance :** {m['prob']}%")
