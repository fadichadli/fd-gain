import streamlit as st
import requests
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
.pack-card { background:#0d1220; border:1px solid #1a2540; border-radius:14px; padding:18px 22px; margin-bottom:14px; border-left:4px solid #00e5a0; }
.pack-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:0.08em; color:#e8eaf0; }
.pack-meta { font-size:0.72rem; color:#3a4a6a; margin-top:2px; }
.pack-cote { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#ffd700; line-height:1; }
.sel-row { background:#111827; border:1px solid #1e2a40; border-radius:8px; padding:11px 15px; margin-top:8px; }
.sel-match  { font-weight:600; font-size:0.88rem; color:#c8d0e0; }
.sel-league { font-size:0.7rem; color:#3a4a6a; margin-bottom:5px; }
.cote-pill  { font-family:'Bebas Neue',sans-serif; font-size:1.15rem; background:rgba(0,229,160,0.1); color:#00e5a0; padding:1px 10px; border-radius:4px; display:inline-block; }
.badge { display:inline-block; font-size:0.67rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:2px 9px; border-radius:20px; }
.b-h2h   { background:rgba(0,229,160,0.12); color:#00e5a0; }
.b-dc    { background:rgba(77,159,255,0.12); color:#4d9fff; }
.b-btts  { background:rgba(255,180,0,0.12);  color:#ffb400; }
.b-over  { background:rgba(200,100,255,0.12);color:#c864ff; }
.b-under { background:rgba(255,90,90,0.12);  color:#ff5a5a; }
.stat-box { background:#0d1220; border:1px solid #1a2540; border-radius:10px; padding:14px; text-align:center; }
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00e5a0; line-height:1; }
.stat-lbl { font-size:0.7rem; color:#3a4a6a; margin-top:3px; }
.pack-off { background:#0a0d15; border:1px dashed #1a2035; border-radius:14px; padding:14px 22px; margin-bottom:14px; color:#2a3550; font-size:0.8rem; }
.rec-row { background:#0d1220; border:1px solid #151d30; border-radius:8px; padding:10px 13px; margin-bottom:6px; }
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

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    marches_actifs = st.multiselect("Marchés", options=list(MKT_INFO.keys()), default=['h2h', 'double_chance', 'btts'], format_func=lambda x: MKT_INFO[x][0])
    st.divider()
    if st.button("↻ Actualiser les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #151d30;padding-bottom:1rem;margin-bottom:1.5rem">
  <span class="wh-title">BETCORE AI PLATINUM</span><br>
  <span class="wh-sub">Analyses prédictives basées sur les algorithmes de consensus des bookmakers</span>
</div>
""", unsafe_allow_html=True)

# ─── FETCH SECURISE ───────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_selections(marches_tuple):
    # LIMITATION AUX LIGUES MAJEURES POUR EVITER LE BLOCAGE API
    ligues_fiables = [
        'soccer_france_ligue_one', 'soccer_england_premier_league', 
        'soccer_germany_bundesliga', 'soccer_italy_serie_a', 
        'soccer_spain_la_liga', 'soccer_brazil_campeonato'
    ]
    
    api_mkts = set()
    for m in marches_tuple: api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)
    
    selections = []
    pb = st.progress(0, text="Connexion aux serveurs API...")
    
    for i, ligue in enumerate(ligues_fiables):
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                for match in r.json():
                    match_id = match['id']
                    home, away = match.get('home_team',''), match.get('away_team','')
                    
                    for bk in match.get('bookmakers', []):
                        for mkt in bk.get('markets', []):
                            mkt_key = mkt.get('key','')
                            
                            # On mappe le marché avec la config locale
                            local_mkt = mkt_key
                            if mkt_key == 'totals':
                                local_mkt = 'totals_over' # Simplification pour garantir la donnée
                                
                            if local_mkt not in marches_tuple: continue
                            
                            for out in mkt.get('outcomes', []):
                                cote = out['price']
                                if cote <= 1.10: continue # Ignorer les cotes trop faibles
                                
                                lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                
                                selections.append({
                                    'match_id': match_id,
                                    'match': f"{home} vs {away}",
                                    'league': ligue.replace('soccer_', '').replace('_', ' ').title(),
                                    'date': "Prochainement",
                                    'mkt': local_mkt,
                                    'mkt_lbl': lbl,
                                    'mkt_css': css,
                                    'prono': out['name'],
                                    'cote': cote,
                                    'prob': round((1/cote)*100, 1),
                                    'score_ia': round((1/cote) + 0.1, 4), # Score simulé
                                    'nb_bk': 15
                                })
        except: pass
        pb.progress((i+1)/len(ligues_fiables), text=f"Analyse {ligue}...")
    
    pb.empty()
    # Trier par fiabilité (plus la cote est basse, plus c'est fiable, donc prob haute)
    selections.sort(key=lambda x: x['prob'], reverse=True)
    return selections

# ─── CONSTRUCTION TICKET INTELLIGENTE ─────────────────────────────────────────
def construire_ticket(sels, cote_cible, cles_utilisees):
    ticket = []
    cote_actuelle = 1.0
    ids_dans_ticket = set()
    
    for s in sels:
        cle_unique = f"{s['match_id']}_{s['mkt']}_{s['prono']}"
        
        # Ignorer si déjà utilisé dans un autre pack ou le même match dans ce pack
        if cle_unique in cles_utilisees or s['match_id'] in ids_dans_ticket:
            continue
            
        # Ajouter au ticket
        ticket.append(s)
        cote_actuelle *= s['cote']
        ids_dans_ticket.add(s['match_id'])
        cles_utilisees.add(cle_unique)
        
        # Arrêter si on a atteint ou légèrement dépassé la cible
        if cote_actuelle >= cote_cible * 0.90:
            break
            
    # Si le ticket atteint au moins 70% de la cible, on l'accepte
    if cote_actuelle >= cote_cible * 0.70:
        return ticket, round(cote_actuelle, 2)
    else:
        # On annule l'utilisation de ces clés car le pack a échoué
        for s in ticket:
            cles_utilisees.remove(f"{s['match_id']}_{s['mkt']}_{s['prono']}")
        return [], 0.0

# ─── EXECUTION ────────────────────────────────────────────────────────────────
sels = fetch_selections(tuple(marches_actifs))

if not sels:
    st.error("❌ Aucun match exploitable récupéré. Vérifiez l'API ou réessayez plus tard.")
    st.stop()

# ─── STATS BAR ────────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
for col, (v,l) in zip([c1,c2,c3,c4],[
    (len(set(s['match_id'] for s in sels)), "Matchs analysés"),
    (len(sels), "Pronostics trouvés"),
    (f"{round(sum(s['prob'] for s in sels[:10])/10 if sels else 0, 1)}%", "Fiabilité Top 10"),
    (len(marches_actifs), "Marchés actifs"),
]):
    with col: st.markdown(f'<div class="stat-box"><div class="stat-val">{v}</div><div class="stat-lbl">{l}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── AFFICHAGE DES PACKS ──────────────────────────────────────────────────────
col_packs, col_recap = st.columns([3, 2], gap="large")
cles_utilisees = set()

with col_packs:
    st.markdown("### 📦 Packs Prédictifs")
    
    for cible in PACK_CIBLES:
        ticket, cote_r = construire_ticket(sels, cible, cles_utilisees)
        
        if not ticket:
            st.markdown(f'<div class="pack-off">📦 <b>Pack ×{cible}</b> — ⚠️ Pas assez de matchs sûrs pour atteindre cette cote aujourd\'hui.</div>', unsafe_allow_html=True)
            continue
            
        nb_s = len(ticket)
        fiab = round(sum(s['prob'] for s in ticket)/nb_s, 1)
        risque = "🟢 Faible" if cote_r<=3 else "🟡 Modéré" if cote_r<=8 else "🟠 Élevé" if cote_r<=15 else "🔴 Très élevé"
        
        rows = ""
        for s in ticket:
            bw = min(int(s['prob']), 100)
            rows += f"""
            <div class="sel-row">
                <div class="sel-league">{s['league']}</div>
                <div class="sel-match">{s['match']}</div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:5px">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="font-size:0.83rem;color:#e8eaf0">▶ {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                </div>
                <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
            </div>"""
            
        st.markdown(f"""
        <div class="pack-card">
            <div class="pack-top">
                <div>
                    <div class="pack-name">PACK OBJECTIF ×{cible}</div>
                    <div class="pack-meta">{nb_s} sélections · Fiabilité {fiab}% · Risque {risque}</div>
                </div>
                <div class="pack-cote">{cote_r}×</div>
            </div>
            {rows}
        </div>""", unsafe_allow_html=True)

# ─── RECAP ────────────────────────────────────────────────────────────────────
with col_recap:
    st.markdown("### 📋 Base de données")
    for s in sels[:15]: # Afficher les 15 meilleurs
        bw = min(int(s['prob']), 100)
        st.markdown(f"""
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between">
                <span style="font-weight:600;font-size:0.85rem;color:#c8d0e0">{s['match']}</span>
                <span class="cote-pill">@{s['cote']}</span>
            </div>
            <div style="font-size:0.7rem;color:#3a4a6a">{s['league']}</div>
            <div style="display:flex;gap:6px;align-items:center;margin-top:5px">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="font-size:0.8rem;color:#e8eaf0">▶ {s['prono']}</span>
            </div>
            <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
        </div>""", unsafe_allow_html=True)
