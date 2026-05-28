import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

API_KEY = "YOUR_API_KEY_HERE"

st.title("⚽ WinHand AI (DEBUG VERSION)")

# =========================
# TEST API LIGUES
# =========================

@st.cache_data(ttl=3600)
def get_ligues():
    try:
        url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
        r = requests.get(url, timeout=10)

        data = r.json()

        ligues = [s["key"] for s in data if "soccer" in s.get("key", "")]

        return ligues, data

    except Exception as e:
        return [], str(e)

ligues, raw = get_ligues()

st.write("📡 Ligues trouvées:", len(ligues))

if not ligues:
    st.error("❌ API KO ou clé invalide")
    st.stop()

# =========================
# PARAMS
# =========================

fenetre = st.selectbox("Fenêtre (heures)", [24, 48, 72], index=1)

# =========================
# FETCH MATCHES
# =========================

def fetch_matches():

    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=fenetre)

    selections = []

    progress = st.progress(0)

    for i, ligue in enumerate(ligues[:10]):  # limité pour test

        try:
            url = f"https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
            r = requests.get(url, timeout=10)

            if r.status_code != 200:
                continue

            matches = r.json()

            for m in matches:

                try:
                    t = datetime.fromisoformat(m["commence_time"].replace("Z", "+00:00"))
                except:
                    continue

                if not (now <= t <= end_time):
                    continue

                home = m.get("home_team")
                away = m.get("away_team")

                selections.append({
                    "match": f"{home} vs {away}",
                    "time": str(t)
                })

        except:
            pass

        progress.progress((i+1)/10)

    progress.empty()

    return selections

# =========================
# EXECUTION
# =========================

matches = fetch_matches()

st.write("🎯 Matchs trouvés:", len(matches))

if not matches:
    st.warning("⚠️ Aucun match récupéré (API ou filtre fenêtre)")
    st.stop()

# =========================
# DISPLAY
# =========================

for m in matches[:30]:
    st.markdown(f"""
    <div style="background:#111;padding:10px;border-radius:10px;margin:5px 0">
        ⚽ {m['match']} <br>
        🕒 {m['time']}
    </div>
    """, unsafe_allow_html=True)
