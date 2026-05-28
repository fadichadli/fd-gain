import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

st.set_page_config(
    page_title="WinHand AI PRO",
    page_icon="⚽",
    layout="wide"
)

API_KEY = "YOUR_API_KEY_HERE"

PACK_CIBLES = [2, 3, 5, 10, 20]

MARCHE_INFO = {
    'h2h': ('1X2', 'badge-h2h'),
    'double_chance': ('Double Chance', 'badge-dc'),
    'btts': ('BTTS', 'badge-btts'),
    'totals_over': ('Over', 'badge-over'),
    'totals_under': ('Under', 'badge-under'),
}

st.markdown("""
<style>
html, body {
    background-color: #0b1020;
    color: white;
}
.card {
    background: #121a2b;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #1f2b45;
}
.badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: bold;
}
.badge-h2h { background: rgba(0,255,150,0.15); color: #00ff99; }
.badge-dc { background: rgba(0,150,255,0.15); color: #3da5ff; }
.badge-btts { background: rgba(255,180,0,0.15); color: #ffb400; }
.badge-over { background: rgba(200,100,255,0.15); color: #d26bff; }
.badge-under { background: rgba(255,80,80,0.15); color: #ff7070; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ WinHand AI PRO")

with st.sidebar:
    marches_actifs = st.multiselect(
        "Marchés",
        list(MARCHE_INFO.keys()),
        default=['double_chance', 'totals_over', 'btts', 'h2h'],
        format_func=lambda x: MARCHE_INFO[x][0]
    )

    point_totals = st.selectbox("Over/Under", [1.5, 2.5, 3.5], index=1)

    cote_min = st.slider("Cote min", 1.05, 2.0, 1.10)
    cote_max = st.slider("Cote max", 1.10, 5.0, 2.20)
    bk_min = st.slider("Min bookmakers", 1, 10, 2)
    fenetre = st.selectbox("Fenêtre", [24, 48, 72, 168], index=2)
    mode_safe = st.toggle("SAFE MODE", value=True)


@st.cache_data(ttl=1800)
def get_ligues():
    try:
        r = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}")
        return [s["key"] for s in r.json() if "soccer" in s.get("group", "")]
    except:
        return []


@st.cache_data(ttl=1800)
def fetch_predictions():
    ligues = get_ligues()
    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=fenetre)

    selections = []

    api_markets = set()
    for m in marches_actifs:
        if m in ["totals_over", "totals_under"]:
            api_markets.add("totals")
        else:
            api_markets.add(m)

    markets_str = ",".join(api_markets)

    progress = st.progress(0)

    for i, ligue in enumerate(ligues[:30]):

        try:
            url = f"https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={markets_str}&oddsFormat=decimal"
            r = requests.get(url, timeout=10)

            if r.status_code != 200:
                continue

            matchs = r.json()

            for match in matchs:

                try:
                    match_time = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
                except:
                    continue

                if not (now <= match_time <= end_time):
                    continue

                home = match.get("home_team", "")
                away = match.get("away_team", "")

                agreg = defaultdict(lambda: defaultdict(list))

                for bk in match.get("bookmakers", []):
                    for market in bk.get("markets", []):
                        mk = market.get("key", "")

                        for out in market.get("outcomes", []):

                            if mk == "totals":
                                point = out.get("point", point_totals)
                                if float(point) != float(point_totals):
                                    continue
                                key = f"totals_{out['name'].lower()}"
                                agreg[key][out["name"]].append(out["price"])
                            else:
                                agreg[mk][out["name"]].append(out["price"])

                for mkt in marches_actifs:

                    if mkt not in agreg:
                        continue

                    stats = []
                    total_prob = 0

                    for name, cotes in agreg[mkt].items():

                        if len(cotes) < bk_min:
                            continue

                        cote = sum(cotes) / len(cotes)

                        if not (cote_min <= cote <= cote_max):
                            continue

                        pb = 1 / cote
                        total_prob += pb

                        stats.append({
                            "name": name,
                            "cote": cote,
                            "pb": pb,
                            "bk": len(cotes)
                        })

                    if not stats:
                        continue

                    for s in stats:
                        prob = s["pb"] / total_prob
                        bonus = min(s["bk"] / 10, 0.18)

                        safe = 0
                        if mode_safe:
                            if s["cote"] <= 1.35:
                                safe = 0.10
                            elif s["cote"] <= 1.60:
                                safe = 0.06
                            elif s["cote"] <= 2:
                                safe = 0.03

                        s["score"] = prob + bonus + safe
                        s["prob_pct"] = prob * 100

                    stats.sort(key=lambda x: x["score"], reverse=True)
                    best = stats[0]

                    label, css = MARCHE_INFO[mkt]

                    selections.append({
                        "match": f"{home} vs {away}",
                        "market": label,
                        "css": css,
                        "prediction": best["name"],
                        "cote": round(best["cote"], 2),
                        "score": best["score"],
                        "prob": round(best["prob_pct"], 1)
                    })

        except:
            pass

        progress.progress((i + 1) / 30)

    progress.empty()

    return sorted(selections, key=lambda x: x["score"], reverse=True)


selections = fetch_predictions()

if not selections:
    st.warning("Aucune donnée")
    st.stop()

st.subheader("📊 Predictions")

for s in selections[:40]:
    st.markdown(f"""
    <div class="card">
        <b>{s['match']}</b><br><br>
        <span class="badge {s['css']}">{s['market']}</span><br><br>
        🎯 {s['prediction']}<br>
        💰 @{s['cote']}<br>
        📊 {round(s['prob'],1)}%
    </div>
    """, unsafe_allow_html=True)
