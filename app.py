import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Config de la page Streamlit (Pour éviter le bug visuel)
st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="centered")

# CSS d'intégration mobile propre
st.markdown("""
<style>
    .reportview-container .main .block-container { max-width: 100%; padding: 1rem; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #10172a; color: white; }
    .pack-card { background-color: #0f172a; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #38bdf8; }
    .match-card { background-color: #1e293b; border-radius: 8px; padding: 12px; margin-top: 8px; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
MARKETS     = 'h2h,double_chance,totals,btts'
PACK_CIBLES = [2, 3, 5, 10, 20]
FENETRE_H   = 168

st.title("🏆 WinHand AI - Multi-Marchés")

# ─── 1. FETCH ET ANALYSE MULTI-MARCHÉS ────────────────────────────────────────
@st.cache_data(ttl=3600)  # Cache d'une heure pour économiser les requêtes API
def fetch_tous_les_matchs():
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
    ligues_a_interroger = toutes_ligues[:20]  # Monté à 20 ligues pour avoir plus de matchs

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

        if not (maintenant - timedelta(minutes=15) <= date_match <= fin_fenetre): continue

        home, away, league = match.get('home_team', ''), match.get('away_team', ''), match.get('sport_title', 'Inconnu')
        delta_j = (date_match.date() - maintenant.date()).days
        label_date = f"Auj. {date_match.strftime('%H:%M')}" if delta_j == 0 else (f"Dem. {date_match.strftime('%H:%M')}" if delta_j == 1 else date_match.strftime('%d/%m %H:%M'))

        cotes_par_marche = defaultdict(lambda: defaultdict(list))

        for bk in match.get('bookmakers', []):
            for mkt in bk.get('markets', []):
                mkt_key = mkt.get('key')
                if mkt_key in ['h2h', 'double_chance', 'totals', 'btts']:
                    for out in mkt.get('outcomes', []):
                        name = out['name']
                        if mkt_key == 'totals':
                            name = f"{out['name']} {out.get('point', '')}"
                        cotes_par_marche[mkt_key][name].append(out['price'])

        selections = []

        for mkt_key, issues in cotes_par_marche.items():
            if not issues: continue
            total_prob_brut = sum(1 / (sum(cotes)/len(cotes)) for cotes in issues.values())
            
            for issue_name, cotes in issues.items():
                if not cotes: continue
                cote_moy = round(sum(cotes) / len(cotes), 3)
                prob_brut = 1 / cote_moy
                prob_corr = prob_brut / total_prob_brut
                
                label_affichage = issue_name
                if mkt_key == 'h2h': label_affichage = f"Victoire : {issue_name}"
                elif mkt_key == 'double_chance': label_affichage = f"Double Chance : {issue_name.replace('or', '/')}"
                elif mkt_key == 'btts': label_affichage = "Les deux équipes marquent : OUI" if issue_name.lower() == 'yes' else "Les deux équipes marquent : NON"
                elif mkt_key == 'totals': label_affichage = f"Buts : {issue_name.replace('Over', 'Plus de').replace('Under', 'Moins de')}"

                bonus_consensus = min(len(cotes) / 12.0, 0.15)
                score_ia = round(prob_corr + bonus_consensus, 4)
                prob_pct = round(prob_corr * 100, 1)

                selections.append({
                    'type_pari': label_affichage,
                    'cote': cote_moy,
                    'prob': prob_pct,
                    'score_ia': score_ia,
                    'nb_bk': len(cotes)
                })

        if not selections: continue
        selections.sort(key=lambda x: x['score_ia'], reverse=True)
        best = selections[0]

        matchs.append({
            'id': match['id'],
            'match': f"{home} vs {away}",
            'league': league,
            'date': label_date,
            'prono': best['type_pari'],
            'cote': best['cote'],
            'prob': best['prob'],
            'nb_bk': best['nb_bk']
        })

    matchs.sort(key=lambda x: x['prob'], reverse=True)
    return matchs

# ─── 2. CONSTRUIRE TICKET ────────────────────────────────────────────────────
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

            if not (cote_cible * 0.75 <= cote_tot <= cote_cible * 1.50): continue
            securite_moyenne = sum(m['prob'] for m in combo) / len(combo)

            # Ligne 150 corrigée avec le ":" à la fin !
            if securite_moyenne > meilleure_securite_moyenne:
                meilleure_securite_moyenne = securite_moyenne
                meilleure_cote = round(cote_tot, 2)
                meilleur = list(combo)

    return meilleur, meilleure_cote

# ─── 3. INTERFACE STREAMLIT AFFICHAGE ──────────────────────────────────────────
liste_matchs = fetch_tous_les_matchs()

if not liste_matchs:
    st.warning("⚠️ Aucun match disponible ou limite d'API atteinte. Réessayez plus tard.")
else:
    ids_utilises = set()
    for cible in PACK_CIBLES:
        ticket, cote_reelle = construire_ticket(liste_matchs, cible, ids_utilises)
        
        st.markdown(f"<div class='pack-card'><h3>📦 Pack Objectif ×{cible}</h3><p><b>Cote Combinée Réelle : ×{cote_reelle}</b></p>", unsafe_allow_html=True)
        
        if not ticket:
            st.write("🔒 Aucun match assez sûr pour ce profil de risque actuellement.")
        else:
            for m in ticket:
                st.markdown(f"""
                <div class='match-card'>
                    <b>⚽ {m['match']}</b> ({m['league']}) - <i>{m['date']}</i><br>
                    👉 <b>Prono :</b> {m['prono']} @{m['cote']} (Fiabilité : {m['prob']}%)
                </div>
                """, unsafe_allow_html=True)
                ids_utilises.add(m['id'])
        st.markdown("</div>", unsafe_allow_html=True)
