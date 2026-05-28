```python
import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="WinHand AI PRO",
    page_icon="⚽",
    layout="wide"
)

API_KEY = "VOTRE_API_KEY_ICI"

PACK_CIBLES = [2, 3, 5, 10, 20]

MARCHE_INFO = {
    'h2h': ('1X2', 'badge-h2h'),
    'double_chance': ('Double Chance', 'badge-dc'),
    'btts': ('BTTS', 'badge-btts'),
    'totals_over': ('Over', 'badge-over'),
    'totals_under': ('Under', 'badge-under'),
}

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0b1020;
    color: white;
}

.main-title {
    font-size: 55px;
    font-weight: bold;
    color: #00ffb3;
}

.card {
    background: #121a2b;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 15px;
    border: 1px solid #1f2b45;
}

.ticket-title {
    font-size: 28px;
    color: gold;
    font-weight: bold;
}

.match-row {
    background: #182338;
    padding: 12px;
    border-radius: 10px;
    margin-top: 10px;
}

.green {
    color: #00ff99;
}

.orange {
    color: orange;
}

.red {
    color: #ff5f5f;
}

.badge {
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: bold;
}

.badge-h2h {
    background: rgba(0,255,150,0.15);
    color: #00ff99;
}

.badge-dc {
    background: rgba(0,150,255,0.15);
    color: #3da5ff;
}

.badge-btts {
    background: rgba(255,180,0,0.15);
    color: #ffb400;
}

.badge-over {
    background: rgba(200,100,255,0.15);
    color: #d26bff;
}

.badge-under {
    background: rgba(255,80,80,0.15);
    color: #ff7070;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">⚽ WinHand AI PRO</div>',
    unsafe_allow_html=True
)

st.write("IA Football Predictions • Over/Under • BTTS • Double Chance")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Paramètres")

    marches_actifs = st.multiselect(
        "Marchés",
        options=list(MARCHE_INFO.keys()),
        default=[
            'double_chance',
            'totals_over',
            'btts',
            'h2h'
        ],
        format_func=lambda x: MARCHE_INFO[x][0]
    )

    point_totals = st.selectbox(
        "Over / Under",
        [1.5, 2.5, 3.5],
        index=1
    )

    cote_min = st.slider(
        "Cote minimum",
        1.05,
        2.0,
        1.10,
        0.05
    )

    cote_max = st.slider(
        "Cote maximum",
        1.10,
        5.0,
        2.20,
        0.05
    )

    bk_min = st.slider(
        "Minimum bookmakers",
        1,
        10,
        2
    )

    fenetre = st.selectbox(
        "Fenêtre matchs",
        [24, 48, 72, 168],
        index=2
    )

    mode_safe = st.toggle(
        "SAFE IA MODE",
        value=True
    )

# =========================================================
# API
# =========================================================

@st.cache_data(ttl=1800)
def get_ligues():

    try:

        url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"

        r = requests.get(url, timeout=10)

        sports = r.json()

        return [
            s['key']
            for s in sports
            if 'soccer' in s.get('group', '').lower()
        ]

    except:
        return []

# =========================================================
# FETCH MATCHES
# =========================================================

@st.cache_data(ttl=1800)
def fetch_predictions():

    ligues = get_ligues()

    selections = []

    now = datetime.now(timezone.utc)

    end_time = now + timedelta(hours=fenetre)

    api_markets = set()

    for m in marches_actifs:

        if m in ['totals_over', 'totals_under']:
            api_markets.add('totals')
        else:
            api_markets.add(m)

    markets_str = ",".join(api_markets)

    progress = st.progress(0)

    for idx, ligue in enumerate(ligues[:40]):

        try:

            url = (
                f"https://api.the-odds-api.com/v4/sports/{ligue}/odds/"
                f"?apiKey={API_KEY}"
                f"&regions=eu"
                f"&markets={markets_str}"
                f"&oddsFormat=decimal"
            )

            r = requests.get(url, timeout=10)

            if r.status_code != 200:
                continue

            matchs = r.json()

            for match in matchs:

                try:

                    match_time = datetime.fromisoformat(
                        match['commence_time'].replace("Z", "+00:00")
                    )

                except:
                    continue

                if not (now <= match_time <= end_time):
                    continue

                home = match.get("home_team", "")
                away = match.get("away_team", "")

                league = match.get("sport_title", "")

                agreg = defaultdict(lambda: defaultdict(list))

                for bk in match.get("bookmakers", []):

                    for market in bk.get("markets", []):

                        mk = market.get("key", "")

                        for out in market.get("outcomes", []):

                            if mk == "totals":

                                point = out.get("point", point_totals)

                                if float(point) != float(point_totals):
                                    continue

                                nom = f"{out['name']} {point}"

                                key = f"totals_{out['name'].lower()}"

                                agreg[key][nom].append(out['price'])

                            else:

                                agreg[mk][out['name']].append(out['price'])

                for mkt in marches_actifs:

                    if mkt not in agreg:
                        continue

                    issues = agreg[mkt]

                    stats = []

                    total_prob = 0

                    for nom, cotes in issues.items():

                        if len(cotes) < bk_min:
                            continue

                        cote = round(sum(cotes) / len(cotes), 2)

                        if not (cote_min <= cote <= cote_max):
                            continue

                        pb = 1 / cote

                        total_prob += pb

                        stats.append({
                            "nom": nom,
                            "cote": cote,
                            "pb": pb,
                            "bk": len(cotes)
                        })

                    if not stats:
                        continue

                    for s in stats:

                        prob = s['pb'] / total_prob

                        bonus_bk = min(s['bk'] / 10, 0.18)

                        bonus_safe = 0

                        if mode_safe:

                            if s['cote'] <= 1.35:
                                bonus_safe = 0.10

                            elif s['cote'] <= 1.60:
                                bonus_safe = 0.06

                            elif s['cote'] <= 2:
                                bonus_safe = 0.03

                        score = prob + bonus_bk + bonus_safe

                        s['score'] = round(score, 4)

                        s['prob_pct'] = round(prob * 100, 1)

                    stats.sort(
                        key=lambda x: x['score'],
                        reverse=True
                    )

                    best = stats[0]

                    label, css = MARCHE_INFO[mkt]

                    selections.append({
                        "match_id": match['id'],
                        "match": f"{home} vs {away}",
                        "league": league,
                        "market": label,
                        "market_key": mkt,
                        "css": css,
                        "prediction": best['nom'],
                        "cote": best['cote'],
                        "score": best['score'],
                        "prob": best['prob_pct'],
                        "bk": best['bk']
                    })

        except:
            pass

        progress.progress((idx + 1) / 40)

    progress.empty()

    selections.sort(
        key=lambda x: x['score'],
        reverse=True
    )

    return selections

# =========================================================
# TICKET ENGINE
# =========================================================

def construire_ticket(sels, cible, used):

    candidats = [
        s for s in sels
        if f"{s['match_id']}_{s['market_key']}" not in used
    ]

    candidats = sorted(
        candidats,
        key=lambda x: x['score'],
        reverse=True
    )[:18]

    best_ticket = None

    best_diff = 999

    best_conf = 0

    for r in range(1, min(7, len(candidats) + 1)):

        for combo in itertools.combinations(candidats, r):

            matchs = [c['match_id'] for c in combo]

            if len(matchs) != len(set(matchs)):
                continue

            cote = 1

            for c in combo:
                cote *= c['cote']

            cote = round(cote, 2)

            diff = abs(cote - cible)

            conf = sum(c['score'] for c in combo) / len(combo)

            if cote > cible * 1.15:
                diff += 2

            if (
                diff < best_diff
                or (
                    diff == best_diff
                    and conf > best_conf
                )
            ):

                best_diff = diff
                best_conf = conf
                best_ticket = combo

    if not best_ticket:
        return [], 0

    final_cote = 1

    for x in best_ticket:
        final_cote *= x['cote']

    return list(best_ticket), round(final_cote, 2)

# =========================================================
# LOAD DATA
# =========================================================

with st.spinner("Analyse IA en cours..."):

    selections = fetch_predictions()

if not selections:

    st.warning("Aucune sélection trouvée.")

    st.stop()

# =========================================================
# STATS
# =========================================================

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Matchs", len(set(s['match_id'] for s in selections)))

with c2:
    st.metric("Sélections", len(selections))

with c3:
    moyenne = round(
        sum(s['score'] for s in selections)
        / len(selections) * 100,
        1
    )

    st.metric("Fiabilité IA", f"{moyenne}%")

# =========================================================
# PACKS
# =========================================================

st.markdown("---")

st.header("🎯 PACKS IA")

used_keys = set()

for cible in PACK_CIBLES:

    ticket, cote_finale = construire_ticket(
        selections,
        cible,
        used_keys
    )

    if not ticket:

        st.warning(f"Impossible de créer le pack x{cible}")

        continue

    fiabilite = round(
        sum(s['score'] for s in ticket)
        / len(ticket) * 100,
        1
    )

    st.markdown(
        f"""
        <div class="card">
        <div class="ticket-title">
        PACK x{cible} → @{cote_finale}
        </div>

        <br>

        <b>Fiabilité IA :</b> {fiabilite}%

        </div>
        """,
        unsafe_allow_html=True
    )

    for s in ticket:

        st.markdown(
            f"""
            <div class="match-row">

            <b>{s['match']}</b>

            <br><br>

            <span class="badge {s['css']}">
            {s['market']}
            </span>

            <br><br>

            🎯 {s['prediction']}

            <br>

            💰 Cote : @{s['cote']}

            <br>

            📊 Probabilité : {s['prob']}%

            <br>

            🏦 Bookmakers : {s['bk']}

            </div>
            """,
            unsafe_allow_html=True
        )

        used_keys.add(
            f"{s['match_id']}_{s['market_key']}"
        )

# =========================================================
# ALL PREDICTIONS
# =========================================================

st.markdown("---")

st.header("📋 Toutes les prédictions IA")

for s in selections[:50]:

    st.markdown(
        f"""
        <div class="match-row">

        <b>{s['match']}</b>

        <br><br>

        <span class="badge {s['css']}">
        {s['market']}
        </span>

        <br><br>

        🎯 {s['prediction']}

        <br>

        💰 @{s['cote']}

        <br>

        📊 {s['prob']}%

        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "WinHand AI PRO • The Odds API • Bet Responsibly"
)
```
