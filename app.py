import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:#07090f; color:#e8eaf0; }
.block-container { padding:1.5rem 2rem; max-width:1300px; }

.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3rem; color:#00e5a0; letter-spacing:0.1em; }
.wh-sub   { color:#3a4a6a; font-size:0.85rem; }

.pack-card {
    background:#0d1220; border:1px solid #1a2540;
    border-radius:14px; padding:18px 22px; margin-bottom:14px;
    border-left:4px solid #00e5a0;
}
.pack-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:0.08em; color:#e8eaf0; }
.pack-meta { font-size:0.72rem; color:#3a4a6a; margin-top:2px; }
.pack-cote { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#ffd700; line-height:1; }

.sel-row {
    background:#111827; border:1px solid #1e2a40;
    border-radius:8px; padding:11px 15px; margin-top:8px;
}
.sel-match  { font-weight:600; font-size:0.88rem; color:#c8d0e0; }
.sel-league { font-size:0.7rem; color:#3a4a6a; margin-bottom:5px; }
.cote-pill  { font-family:'Bebas Neue',sans-serif; font-size:1.15rem;
               background:rgba(0,229,160,0.1); color:#00e5a0;
               padding:1px 10px; border-radius:4px; display:inline-block; }
.badge { display:inline-block; font-size:0.67rem; font-weight:700;
          letter-spacing:0.1em; text-transform:uppercase;
          padding:2px 9px; border-radius:20px; }
.b-h2h   { background:rgba(0,229,160,0.12); color:#00e5a0; }
.b-dc    { background:rgba(77,159,255,0.12); color:#4d9fff; }
.b-btts  { background:rgba(255,180,0,0.12);  color:#ffb400; }
.b-over  { background:rgba(200,100,255,0.12);color:#c864ff; }
.b-under { background:rgba(255,90,90,0.12);  color:#ff5a5a; }

.stat-box { background:#0d1220; border:1px solid #1a2540; border-radius:10px;
             padding:14px; text-align:center; }
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00e5a0; line-height:1; }
.stat-lbl { font-size:0.7rem; color:#3a4a6a; margin-top:3px; }

.pack-off { background:#0a0d15; border:1px dashed #1a2035; border-radius:14px;
             padding:14px 22px; margin-bottom:14px; color:#2a3550; font-size:0.8rem; }

.rec-row { background:#0d1220; border:1px solid #151d30;
            border-radius:8px; padding:10px 13px; margin-bottom:6px; }
.prob-wrap { background:#0a0f1a; border-radius:3px; height:3px; margin-top:5px; }
.prob-fill { height:3px; border-radius:3px; background:linear-gradient(90deg,#0077ff,#00e5a0); }
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20]

MKT_INFO = {
    'h2h':           ('1X2',            'b-h2h'),
    'double_chance': ('Double Chance',   'b-dc'),
    'btts':          ('Les 2 Marquent',  'b-btts'),
    'totals_over':   ('Over',            'b-over'),
    'totals_under':  ('Under',           'b-under'),
}

# ─── SIDEBAR simplifiée ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")

    marches_actifs = st.multiselect(
        "Marchés",
        options=list(MKT_INFO.keys()),
        default=['h2h', 'double_chance', 'btts', 'totals_over', 'totals_under'],
        format_func=lambda x: MKT_INFO[x][0]
    )

    point_ou = st.selectbox("Seuil Over/Under", [1.5, 2.5, 3.5, 4.5], index=1)

    fenetre = st.selectbox(
        "Fenêtre temporelle",
        [24, 48, 72, 168], index=3,
        format_func=lambda x: f"{x}h ({x//24}j)"
    )

    st.divider()
    st.markdown("""
    **ℹ️ Comment ça marche**

    Les packs **×2, ×3, ×5, ×10, ×20** sont des **cotes combinées cibles**.
    L'IA sélectionne les pronos les plus fiables et les combine
    pour atteindre chaque cote cible.

    Aucun filtre de cote min/max — l'algorithme choisit lui-même
    les meilleures sélections.
    """)

    st.divider()
    if st.button("↻ Actualiser les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #151d30;padding-bottom:1rem;margin-bottom:1.5rem">
  <span class="wh-title">WinHand AI</span><br>
  <span class="wh-sub">1X2 · Double Chance · BTTS · Over · Under — Pronostics IA multi-bookmakers</span>
</div>
""", unsafe_allow_html=True)

# ─── FETCH ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_ligues():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
        r.raise_for_status()
        return [s['key'] for s in r.json() if 'soccer' in s.get('group','').lower()]
    except:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_selections(marches_tuple, fenetre_h, point_ou):
    """
    Récupère tous les matchs foot disponibles et calcule le score IA
    pour chaque issue de chaque marché.

    Score IA = probabilité corrigée (sans marge BK) + bonus consensus bookmakers
    → Plus le score est élevé, plus le prono est fiable

    AUCUN filtre de cote min/max : on laisse l'algorithme de combinaison
    choisir les meilleures sélections pour atteindre chaque cote cible.
    """
    ligues = get_ligues()
    if not ligues:
        return [], "API inaccessible — vérifiez votre connexion ou quota."

    # Marchés API nécessaires
    api_mkts = set()
    for m in marches_tuple:
        api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)

    maintenant  = datetime.now(timezone.utc)
    fin         = maintenant + timedelta(hours=fenetre_h)
    raw         = {}

    pb = st.progress(0, text="Analyse des ligues...")
    ligues_scan = ligues[:25]

    for i, ligue in enumerate(ligues_scan):
        url = (
            f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/'
            f'?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        )
        try:
            r = requests.get(url, timeout=8)
            if r.status_code in [401, 403]:
                pb.empty()
                return [], f"Erreur API {r.status_code} — quota épuisé ou clé invalide."
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
        if not (maintenant <= date_m <= fin):
            continue

        home, away = match.get('home_team',''), match.get('away_team','')
        league     = match.get('sport_title','?')
        match_id   = match['id']

        dj = (date_m.date() - maintenant.date()).days
        label_d = (
            "Auj. " + date_m.strftime('%H:%M') if dj == 0 else
            "Dem. " + date_m.strftime('%H:%M') if dj == 1 else
            date_m.strftime('%d/%m %H:%M')
        )

        # Agréger cotes par sous-marché
        agreg = defaultdict(lambda: defaultdict(list))
        for bk in match.get('bookmakers', []):
            for mkt in bk.get('markets', []):
                mk = mkt.get('key','')
                for out in mkt.get('outcomes', []):
                    if mk == 'totals':
                        pt = out.get('point', point_ou)
                        if float(pt) != float(point_ou):
                            continue
                        sous_cle = f"totals_{out['name'].lower()}"
                        agreg[sous_cle][f"{out['name']} {pt}"].append(out['price'])
                    else:
                        agreg[mk][out['name']].append(out['price'])

        # Pour chaque marché actif → score IA → meilleure issue
        for mkt_key in marches_tuple:
            if mkt_key not in agreg:
                continue

            issues     = agreg[mkt_key]
            stats      = []
            total_prob = 0

            for nom, cotes in issues.items():
                if len(cotes) < 1:  # Aucun filtre strict ici
                    continue
                cote_moy = round(sum(cotes)/len(cotes), 3)
                if cote_moy <= 1.0:
                    continue
                pb_brut    = 1 / cote_moy
                total_prob += pb_brut
                stats.append({
                    'nom':   nom,
                    'cote':  cote_moy,
                    'pb':    pb_brut,
                    'nb_bk': len(cotes)
                })

            if not stats or total_prob == 0:
                continue

            # Score IA
            for s in stats:
                prob_c       = s['pb'] / total_prob          # corrige marge BK
                bonus        = min(s['nb_bk'] / 10.0, 0.20) # bonus consensus
                s['score_ia'] = round(prob_c + bonus, 4)
                s['prob_pct'] = round(prob_c * 100, 1)

            # On garde TOUTES les issues triées — pas seulement la meilleure
            # Ça donne plus de candidats pour construire les packs
            stats.sort(key=lambda x: x['score_ia'], reverse=True)

            lbl, css = MKT_INFO.get(mkt_key, (mkt_key, 'b-h2h'))

            for s in stats:  # toutes les issues valides
                selections.append({
                    'match_id': match_id,
                    'match':    f"{home} vs {away}",
                    'league':   league,
                    'date':     label_d,
                    'mkt':      mkt_key,
                    'mkt_lbl':  lbl,
                    'mkt_css':  css,
                    'prono':    s['nom'],
                    'cote':     s['cote'],
                    'prob':     s['prob_pct'],
                    'score_ia': s['score_ia'],
                    'nb_bk':    s['nb_bk'],
                })

    selections.sort(key=lambda x: x['score_ia'], reverse=True)
    return selections, None


# ─── CONSTRUCTION TICKET ──────────────────────────────────────────────────────
def construire_ticket(sels, cote_cible, cles_utilisees):
    """
    Cherche la meilleure combinaison (1 à 6 sélections) dont la
    cote combinée est la plus proche de cote_cible.

    - Pas de filtre min/max sur les cotes individuelles
    - Tolérance : 75% à 160% de la cible
    - Pénalité si on dépasse trop (évite les tickets trop risqués)
    - Anti-doublon : même match+marché ne peut pas revenir
    - On autorise plusieurs marchés du même match (ex: BTTS + Over)
    """
    # Exclure déjà utilisés
    candidats = [
        s for s in sels
        if f"{s['match_id']}_{s['mkt']}_{s['prono']}" not in cles_utilisees
    ]

    if not candidats:
        return [], 0.0

    # Top 15 par score IA pour perf
    candidats = candidats[:15]

    best_t, best_c, best_d = [], 0.0, float('inf')

    for r in range(1, min(7, len(candidats)+1)):
        for combo in itertools.combinations(candidats, r):
            ct = 1.0
            for s in combo:
                ct *= s['cote']

            if ct < cote_cible * 0.75:
                continue

            diff = abs(ct - cote_cible)
            if ct > cote_cible * 1.60:
                diff += (ct - cote_cible * 1.60) * 2

            if diff < best_d:
                best_d = diff
                best_c = round(ct, 2)
                best_t = list(combo)

    return best_t, best_c


# ─── CHARGEMENT ───────────────────────────────────────────────────────────────
if not marches_actifs:
    st.warning("Sélectionnez au moins un marché.")
    st.stop()

with st.spinner("Analyse en cours..."):
    sels, err = fetch_selections(tuple(marches_actifs), fenetre, point_ou)

if err:
    st.error(f"❌ {err}")
    st.stop()

if not sels:
    st.warning("⚠️ Aucune sélection trouvée. Essayez d'augmenter la fenêtre temporelle ou ajoutez des marchés.")
    st.stop()

# Stats
nb_matchs = len(set(s['match_id'] for s in sels))
nb_sels   = len(sels)
score_moy = round(sum(s['score_ia'] for s in sels) / nb_sels * 100, 1)

# ─── STATS BAR ────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
for col, (v,l) in zip([c1,c2,c3,c4],[
    (nb_matchs,        "Matchs analysés"),
    (nb_sels,          "Sélections IA"),
    (f"{score_moy}%",  "Fiabilité moyenne"),
    (len(marches_actifs), "Marchés actifs"),
]):
    with col:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{v}</div><div class="stat-lbl">{l}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── PACKS + RÉCAP ────────────────────────────────────────────────────────────
col_packs, col_recap = st.columns([3, 2], gap="large")
cles_utilisees = set()

with col_packs:
    st.markdown("### 📦 Tickets du jour")

    for cible in PACK_CIBLES:
        ticket, cote_r = construire_ticket(sels, cible, cles_utilisees)

        if not ticket:
            restantes = [s for s in sels if f"{s['match_id']}_{s['mkt']}_{s['prono']}" not in cles_utilisees]
            if not restantes:
                raison = "Toutes les sélections ont été utilisées dans les packs précédents."
            else:
                top_cotes = sorted([s['cote'] for s in restantes], reverse=True)[:6]
                max_a = 1.0
                for c in top_cotes: max_a *= c
                raison = f"Cote ×{cible} non atteignable avec les matchs restants (max ≈ ×{round(max_a,1)})."
            st.markdown(f'<div class="pack-off">📦 <b>Pack ×{cible}</b> — ⚠️ {raison}</div>', unsafe_allow_html=True)
            continue

        nb_s   = len(ticket)
        fiab   = round(sum(s['score_ia'] for s in ticket)/nb_s*100, 1)
        risque = "🟢 Faible" if cote_r<=3 else "🟡 Modéré" if cote_r<=7 else "🟠 Élevé" if cote_r<=12 else "🔴 Très élevé"

        rows = ""
        for s in ticket:
            bw = min(int(s['prob']), 100)
            rows += f"""
            <div class="sel-row">
                <div class="sel-league">{s['league']} — {s['date']}</div>
                <div class="sel-match">{s['match']}</div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:5px">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="font-size:0.83rem;color:#e8eaf0">▶ {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                    <span style="margin-left:auto;font-size:0.68rem;color:#3a4a6a">{s['prob']}% · {s['nb_bk']} BK</span>
                </div>
                <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
            </div>"""
            cles_utilisees.add(f"{s['match_id']}_{s['mkt']}_{s['prono']}")

        st.markdown(f"""
        <div class="pack-card">
            <div class="pack-top">
                <div>
                    <div class="pack-name">PACK ×{cible}</div>
                    <div class="pack-meta">{nb_s} sélection(s) · Fiabilité IA {fiab}% · {risque}</div>
                </div>
                <div class="pack-cote">{cote_r}×</div>
            </div>
            {rows}
        </div>""", unsafe_allow_html=True)

# ─── RÉCAP ────────────────────────────────────────────────────────────────────
with col_recap:
    st.markdown("### 📋 Toutes les sélections")
    filtre = st.selectbox("Filtrer", ['Tous'] + [MKT_INFO[m][0] for m in marches_actifs])

    for s in sels:
        if filtre != 'Tous' and s['mkt_lbl'] != filtre:
            continue
        used = " ✓" if f"{s['match_id']}_{s['mkt']}_{s['prono']}" in cles_utilisees else ""
        bw = min(int(s['prob']), 100)
        st.markdown(f"""
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between">
                <span style="font-weight:600;font-size:0.85rem;color:#c8d0e0">{s['match']}{used}</span>
                <span class="cote-pill">@{s['cote']}</span>
            </div>
            <div style="font-size:0.7rem;color:#3a4a6a">{s['league']} · {s['date']}</div>
            <div style="display:flex;gap:6px;align-items:center;margin-top:5px">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="font-size:0.8rem;color:#e8eaf0">▶ {s['prono']}</span>
            </div>
            <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
            <div style="font-size:0.65rem;color:#3a4a6a;margin-top:2px">
                {s['prob']}% prob · {s['nb_bk']} BK · score IA {s['score_ia']}
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center;color:#1a2035;font-size:0.7rem;margin-top:2rem">WinHand AI — The Odds API — Pariez de façon responsable</div>', unsafe_allow_html=True)
