import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WinHand AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #07090f;
    color: #e8eaf0;
}
.block-container { padding: 1.5rem 2rem; max-width: 1300px; }

.wh-header {
    display: flex; align-items: baseline; gap: 14px;
    border-bottom: 1px solid #151d30; padding-bottom: 1rem; margin-bottom: 1.5rem;
}
.wh-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem; letter-spacing: 0.1em; color: #00e5a0; line-height: 1;
}
.wh-sub { color: #3a4a6a; font-size: 0.85rem; font-weight: 300; }

/* Badges marché */
.badge {
    display: inline-block; font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 2px 9px; border-radius: 20px;
}
.badge-h2h   { background: rgba(0,229,160,0.12); color: #00e5a0; }
.badge-dc    { background: rgba(77,159,255,0.12); color: #4d9fff; }
.badge-btts  { background: rgba(255,180,0,0.12);  color: #ffb400; }
.badge-over  { background: rgba(200,100,255,0.12);color: #c864ff; }
.badge-under { background: rgba(255,90,90,0.12);  color: #ff5a5a; }

/* Pack card */
.pack-card {
    background: #0d1220; border: 1px solid #151d30;
    border-radius: 14px; padding: 18px 22px; margin-bottom: 14px;
    position: relative; overflow: hidden;
}
.pack-card::before {
    content:''; position:absolute; top:0; left:0;
    width:4px; height:100%;
    background: linear-gradient(180deg,#00e5a0,#0077ff);
}
.pack-top {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 10px;
}
.pack-name {
    font-family:'Bebas Neue',sans-serif; font-size:1.3rem;
    letter-spacing:0.08em; color:#e8eaf0;
}
.pack-meta { font-size:0.72rem; color:#3a4a6a; margin-top:2px; }
.pack-cote {
    font-family:'Bebas Neue',sans-serif; font-size:2.5rem;
    color:#ffd700; line-height:1;
}
.pack-cote small { font-size:1rem; color:#5a6a8a; }

/* Sélection dans pack */
.sel-row {
    background: #111827; border:1px solid #1a2540;
    border-radius:8px; padding:10px 14px; margin-top:8px;
}
.sel-match { font-weight:600; font-size:0.88rem; color:#c8d0e0; }
.sel-league { font-size:0.7rem; color:#3a4a6a; margin-bottom:5px; }
.sel-bottom {
    display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:4px;
}
.cote-pill {
    font-family:'Bebas Neue',sans-serif; font-size:1.1rem;
    background:rgba(0,229,160,0.08); color:#00e5a0;
    padding:1px 10px; border-radius:4px;
}
.prob-wrap { background:#0a0f1a; border-radius:3px; height:3px; margin-top:6px; }
.prob-fill  { height:3px; border-radius:3px; background:linear-gradient(90deg,#0077ff,#00e5a0); }

/* Stat box */
.stat-box {
    background:#0d1220; border:1px solid #151d30;
    border-radius:10px; padding:14px 16px; text-align:center;
}
.stat-val  { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00e5a0; line-height:1; }
.stat-lbl  { font-size:0.7rem; color:#3a4a6a; margin-top:3px; }

/* Pack indispo */
.pack-off {
    background:#0a0d15; border:1px dashed #151d30;
    border-radius:14px; padding:14px 22px;
    margin-bottom:14px; color:#2a3550; font-size:0.8rem;
}

/* Recap */
.rec-row {
    background:#0d1220; border:1px solid #151d30;
    border-radius:8px; padding:10px 13px; margin-bottom:7px;
}
.rec-match { font-size:0.83rem; font-weight:600; color:#c8d0e0; }
.rec-meta  { font-size:0.68rem; color:#3a4a6a; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTES ────────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20]

MARCHE_INFO = {
    'h2h':           ('1X2 (Victoire)',        'badge-h2h'),
    'double_chance': ('Double Chance',          'badge-dc'),
    'btts':          ('Les 2 Équipes Marquent', 'badge-btts'),
    'totals_over':   ('Over (Plus de buts)',    'badge-over'),
    'totals_under':  ('Under (Moins de buts)',  'badge-under'),
}

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")

    marches_actifs = st.multiselect(
        "Marchés à analyser",
        options=list(MARCHE_INFO.keys()),
        default=['h2h', 'double_chance', 'btts', 'totals_over', 'totals_under'],
        format_func=lambda x: MARCHE_INFO[x][0]
    )

    point_totals = st.selectbox(
        "Seuil Over/Under",
        [1.5, 2.5, 3.5, 4.5],
        index=1,
        help="Nombre de buts pour le marché Over/Under"
    )

    cote_max = st.slider("Cote max par sélection", 1.10, 4.0, 2.20, 0.05)
    cote_min = st.slider("Cote min par sélection", 1.05, 2.0, 1.10, 0.05)
    bk_min   = st.slider("Bookmakers minimum",     1, 10, 2)
    fenetre  = st.selectbox(
        "Fenêtre temporelle",
        [24, 48, 72, 168],
        index=3,
        format_func=lambda x: f"{x}h ({x//24}j)"
    )
    st.divider()
    if st.button("↻ Vider le cache et actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if not marches_actifs:
    st.warning("Sélectionnez au moins un marché.")
    st.stop()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wh-header">
  <span class="wh-title">WinHand AI</span>
  <span class="wh-sub">1X2 · Double Chance · BTTS · Over · Under — Score IA multi-bookmakers</span>
</div>
""", unsafe_allow_html=True)

# ─── 1. FETCH ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_ligues():
    try:
        r = requests.get(
            f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}',
            timeout=10
        )
        r.raise_for_status()
        return [s['key'] for s in r.json() if 'soccer' in s.get('group','').lower()]
    except Exception as e:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_selections(marches_tuple, fenetre_h, c_max, c_min, bk_minimum, point_over_under):
    """
    Récupère les matchs de toutes les ligues foot disponibles.
    Calcule pour chaque match et chaque marché le score IA de chaque issue.
    Retourne la liste de toutes les sélections valides, triées par score IA.
    """
    ligues = get_ligues()
    if not ligues:
        return [], "Impossible de récupérer les ligues (API inaccessible)."

    # On appelle l'API avec h2h + double_chance + btts + totals
    # On sépare over/under côté Python après
    api_markets = set()
    for m in marches_tuple:
        if m in ('totals_over', 'totals_under'):
            api_markets.add('totals')
        else:
            api_markets.add(m)
    markets_str = ','.join(api_markets)

    maintenant  = datetime.now(timezone.utc)
    fin_fenetre = maintenant + timedelta(hours=fenetre_h)
    raw         = {}  # id → match

    pb = st.progress(0, text="Scan des ligues de foot...")
    ligues_scan = ligues[:25]

    for i, ligue in enumerate(ligues_scan):
        url = (
            f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/'
            f'?apiKey={API_KEY}&regions=eu&markets={markets_str}&oddsFormat=decimal'
        )
        try:
            r = requests.get(url, timeout=8)
            if r.status_code in [401, 403]:
                pb.empty()
                return [], f"Erreur API {r.status_code} — vérifiez votre clé ou quota."
            if r.status_code == 200:
                for m in r.json():
                    raw[m['id']] = m
        except:
            pass
        pb.progress((i+1)/len(ligues_scan), text=f"Ligue {i+1}/{len(ligues_scan)}...")

    pb.empty()

    selections = []

    for match in raw.values():
        try:
            date_m = datetime.fromisoformat(match['commence_time'].replace('Z','+00:00'))
        except:
            continue
        if not (maintenant <= date_m <= fin_fenetre):
            continue

        home     = match.get('home_team','')
        away     = match.get('away_team','')
        league   = match.get('sport_title','?')
        match_id = match['id']

        dj = (date_m.date() - maintenant.date()).days
        if dj == 0:   label_d = "Auj. " + date_m.strftime('%H:%M')
        elif dj == 1: label_d = "Dem. " + date_m.strftime('%H:%M')
        else:         label_d = date_m.strftime('%d/%m %H:%M')

        # Agréger cotes par marché et par issue
        agreg = defaultdict(lambda: defaultdict(list))
        for bk in match.get('bookmakers',[]):
            for mkt in bk.get('markets',[]):
                mk = mkt.get('key','')
                for out in mkt.get('outcomes',[]):
                    if mk == 'totals':
                        pt   = out.get('point', point_over_under)
                        # On ne garde que le seuil choisi par l'utilisateur
                        if float(pt) != float(point_over_under):
                            continue
                        nom = f"{out['name']} {pt}"
                        # Clé interne : totals_over ou totals_under
                        sous_cle = f"totals_{out['name'].lower()}"
                        agreg[sous_cle][nom].append(out['price'])
                    else:
                        agreg[mk][out['name']].append(out['price'])

        # Pour chaque marché actif, calculer score IA et garder la meilleure issue
        for mkt_key in marches_tuple:
            if mkt_key not in agreg:
                continue

            issues      = agreg[mkt_key]
            stats       = []
            total_prob  = 0

            for nom, cotes in issues.items():
                if len(cotes) < bk_minimum:
                    continue
                cote_moy = round(sum(cotes)/len(cotes), 3)
                if not (c_min <= cote_moy <= c_max):
                    continue
                pb_brut = 1 / cote_moy
                total_prob += pb_brut
                stats.append({'nom': nom, 'cote': cote_moy, 'pb': pb_brut, 'nb_bk': len(cotes)})

            if not stats or total_prob == 0:
                continue

            for s in stats:
                prob_c       = s['pb'] / total_prob
                bonus        = min(s['nb_bk'] / 12.0, 0.15)
                s['score_ia'] = round(prob_c + bonus, 4)
                s['prob_pct'] = round(prob_c * 100, 1)

            stats.sort(key=lambda x: x['score_ia'], reverse=True)
            best = stats[0]

            lbl, css = MARCHE_INFO.get(mkt_key, (mkt_key, 'badge-h2h'))
            selections.append({
                'match_id':  match_id,
                'match':     f"{home} vs {away}",
                'league':    league,
                'date':      label_d,
                'mkt':       mkt_key,
                'mkt_lbl':   lbl,
                'mkt_css':   css,
                'prono':     best['nom'],
                'cote':      best['cote'],
                'prob':      best['prob_pct'],
                'score_ia':  best['score_ia'],
                'nb_bk':     best['nb_bk'],
            })

    selections.sort(key=lambda x: x['score_ia'], reverse=True)
    return selections, None

# ─── 2. CONSTRUCTION TICKET ───────────────────────────────────────────────────
def construire_ticket(sels, cote_cible, cles_utilisees):
    """
    Trouve la meilleure combinaison (1–6 sélections) dont la cote combinée
    est la plus proche de cote_cible.
    Une sélection = match_id + mkt (donc même match possible sur 2 marchés différents).
    """
    candidats = [s for s in sels if f"{s['match_id']}_{s['mkt']}" not in cles_utilisees][:12]
    if not candidats:
        return [], 0.0

    best_ticket = []
    best_cote   = 0.0
    best_diff   = float('inf')

    for r in range(1, min(7, len(candidats)+1)):
        for combo in itertools.combinations(candidats, r):
            ct = 1.0
            for s in combo: ct *= s['cote']
            if ct < cote_cible * 0.75: continue
            diff = abs(ct - cote_cible)
            if ct > cote_cible * 1.45:
                diff += (ct - cote_cible * 1.45) * 3
            if diff < best_diff:
                best_diff   = diff
                best_cote   = round(ct, 2)
                best_ticket = list(combo)

    return best_ticket, best_cote

# ─── 3. CHARGEMENT ────────────────────────────────────────────────────────────
with st.spinner("Analyse multi-marchés en cours..."):
    sels, err = fetch_selections(
        tuple(marches_actifs), fenetre, cote_max, cote_min, bk_min, point_totals
    )

if err:
    st.error(f"❌ {err}")
    st.stop()
if not sels:
    st.warning("⚠️ Aucune sélection. Essayez d'élargir la cote max, réduire le BK min, ou augmenter la fenêtre.")
    st.stop()

# Statistiques globales
nb_matchs  = len(set(s['match_id'] for s in sels))
nb_sels    = len(sels)
score_moy  = round(sum(s['score_ia'] for s in sels)/nb_sels*100, 1)
mkt_counts = defaultdict(int)
for s in sels: mkt_counts[s['mkt']] += 1

# ─── 4. STATS ─────────────────────────────────────────────────────────────────
cols = st.columns(5)
stats_display = [
    (nb_matchs,  "Matchs analysés"),
    (nb_sels,    "Sélections IA"),
    (f"{score_moy}%", "Fiabilité moy."),
    (f"×{point_totals}", "Seuil Over/Under"),
    (len(marches_actifs), "Marchés actifs"),
]
for col, (val, lbl) in zip(cols, stats_display):
    with col:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-val">{val}</div>
            <div class="stat-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 5. PACKS + RÉCAP ─────────────────────────────────────────────────────────
col_packs, col_recap = st.columns([3, 2], gap="large")
cles_utilisees = set()

with col_packs:
    st.markdown("### 📦 Tickets du jour")

    for cible in PACK_CIBLES:
        ticket, cote_r = construire_ticket(sels, cible, cles_utilisees)

        if not ticket:
            restantes = [s for s in sels if f"{s['match_id']}_{s['mkt']}" not in cles_utilisees]
            if not restantes:
                raison = "Toutes les sélections ont été utilisées."
            else:
                cotes_r = sorted([s['cote'] for s in restantes], reverse=True)[:6]
                max_a = 1.0
                for c in cotes_r: max_a *= c
                raison = f"×{cible} non atteignable — max ≈ ×{round(max_a,1)} avec les sélections restantes."
            st.markdown(f"""<div class="pack-off">
                📦 <b>Pack ×{cible}</b> — ⚠️ {raison}
            </div>""", unsafe_allow_html=True)
            continue

        nb_s      = len(ticket)
        fiab      = round(sum(s['score_ia'] for s in ticket)/nb_s*100, 1)
        risque    = "🟢 Faible" if cote_r<=3 else "🟡 Modéré" if cote_r<=7 else "🟠 Élevé" if cote_r<=12 else "🔴 Très élevé"

        rows_html = ""
        for s in ticket:
            bw = min(int(s['prob']), 100)
            rows_html += f"""
            <div class="sel-row">
                <div class="sel-league">{s['league']} — {s['date']}</div>
                <div class="sel-match">{s['match']}</div>
                <div class="sel-bottom">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="font-size:0.82rem;color:#e8eaf0">▶ {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                    <span style="margin-left:auto;font-size:0.68rem;color:#3a4a6a">{s['prob']}% · {s['nb_bk']} BK</span>
                </div>
                <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
            </div>"""
            cles_utilisees.add(f"{s['match_id']}_{s['mkt']}")

        st.markdown(f"""
        <div class="pack-card">
            <div class="pack-top">
                <div>
                    <div class="pack-name">PACK ×{cible}</div>
                    <div class="pack-meta">{nb_s} sélection(s) · Fiabilité IA {fiab}% · {risque}</div>
                </div>
                <div class="pack-cote">{cote_r}<small>×</small></div>
            </div>
            {rows_html}
        </div>
        """, unsafe_allow_html=True)

# ─── 6. RÉCAP DROITE ──────────────────────────────────────────────────────────
with col_recap:
    st.markdown("### 📋 Toutes les sélections")

    filtre_mkt = st.selectbox(
        "Filtrer marché",
        ['Tous'] + [MARCHE_INFO[m][0] for m in marches_actifs]
    )

    for s in sels:
        if filtre_mkt != 'Tous' and s['mkt_lbl'] != filtre_mkt:
            continue
        used = " ✓" if f"{s['match_id']}_{s['mkt']}" in cles_utilisees else ""
        bw   = min(int(s['prob']), 100)
        st.markdown(f"""
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="rec-match">{s['match']}{used}</span>
                <span class="cote-pill">@{s['cote']}</span>
            </div>
            <div class="rec-meta">{s['league']} · {s['date']}</div>
            <div style="display:flex;gap:6px;align-items:center;margin-top:5px">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="font-size:0.79rem;color:#c8d0e0">▶ {s['prono']}</span>
            </div>
            <div class="prob-wrap" style="margin-top:5px">
                <div class="prob-fill" style="width:{bw}%"></div>
            </div>
            <div style="font-size:0.65rem;color:#3a4a6a;margin-top:2px">
                {s['prob']}% prob · {s['nb_bk']} bookmakers · score IA {s['score_ia']}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;color:#1a2035;font-size:0.7rem;margin-top:2rem">
WinHand AI — The Odds API — Pariez de façon responsable
</div>
""", unsafe_allow_html=True)
