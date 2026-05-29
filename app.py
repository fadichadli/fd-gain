import streamlit as st
import requests
from typing import List, Dict

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

if 'api_remaining' not in st.session_state:
    st.session_state['api_remaining'] = "Non vérifié"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:linear-gradient(135deg, #07090f 0%, #0a0e1a 100%); color:#e8eaf0; }
.block-container { padding:2rem 2.5rem; max-width:1400px; }
.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3.5rem; color:#00e5a0; letter-spacing:0.15em; }
.wh-sub { color:#3a4a6a; font-size:0.9rem; }
.pack-card { background:linear-gradient(135deg, #0f1623 0%, #151d30 100%); border:2px solid #00e5a0; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 8px 32px rgba(0,229,160,0.2); position:relative; }
.pack-badge { position:absolute; top:16px; right:16px; background:linear-gradient(135deg, #00e5a0 0%, #00c98d 100%); color:#07090f; font-family:'Bebas Neue'; font-size:1.8rem; padding:8px 16px; border-radius:8px; }
.pack-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
.pack-name { font-family:'Bebas Neue'; font-size:2rem; color:#fff; }
.pack-meta { font-size:0.8rem; color:#6b7a9a; }
.sel-row { background:#111827; border:1px solid #2a3550; border-left:4px solid #00e5a0; border-radius:10px; padding:16px; margin-top:12px; }
.sel-league { font-size:0.72rem; color:#00e5a0; font-weight:700; text-transform:uppercase; }
.sel-match { font-weight:700; font-size:1.05rem; color:#fff; margin:8px 0; }
.sel-details { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.badge { font-size:0.7rem; font-weight:700; padding:4px 12px; border-radius:20px; border:1px solid; }
.b-h2h { background:rgba(0,229,160,0.15); color:#00e5a0; border-color:#00e5a0; }
.b-dc { background:rgba(77,159,255,0.15); color:#4d9fff; border-color:#4d9fff; }
.b-btts { background:rgba(255,180,0,0.15); color:#ffb400; border-color:#ffb400; }
.b-over { background:rgba(200,100,255,0.15); color:#c864ff; border-color:#c864ff; }
.b-under { background:rgba(255,90,90,0.15); color:#ff5a5a; border-color:#ff5a5a; }
.cote-pill { font-family:'Bebas Neue'; font-size:1.4rem; background:#00e5a0; color:#07090f; padding:4px 14px; border-radius:6px; }
.stat-box { background:#0f1623; border:1px solid #2a3550; border-radius:12px; padding:18px; text-align:center; }
.stat-val { font-family:'Bebas Neue'; font-size:2.4rem; color:#00e5a0; }
.stat-lbl { font-size:0.75rem; color:#5a6a8a; }
.pack-off { background:#0a0d15; border:2px dashed #2a3550; border-radius:16px; padding:24px; color:#4a5570; text-align:center; }
.rec-row { background:#0f1623; border:1px solid #2a3550; border-radius:10px; padding:14px; margin-bottom:10px; }
.sidebar-success { color:#00e5a0; font-weight:600; }
</style>
""", unsafe_allow_html=True)

API_KEY = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 15]

MKT_INFO = {
    'h2h': ('1X2', 'b-h2h'),
    'double_chance': ('Double Chance', 'b-dc'),
    'btts': ('BTTS', 'b-btts'),
    'totals_over': ('Over', 'b-over'),
    'totals_under': ('Under', 'b-under'),
}

DC_MAP = {
    'HomeOrDraw': '1X',
    'AwayOrDraw': 'X2',
    'HomeOrAway': '12'
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_active_leagues():
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            data = r.json()
            return [s for s in data if s.get('group') == 'Soccer' and not s.get('has_outrights')][:25]
    except: pass
    return []

@st.cache_data(ttl=300, show_spinner=False)
def check_api_health():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
        return {'status': r.status_code == 200, 'remaining': r.headers.get('x-requests-remaining', 'N/A')}
    except:
        return {'status': False, 'remaining': 'N/A'}

def fetch_all_markets_with_fallback(leagues_list):
    """
    STRATÉGIE INTELLIGENTE :
    1. Tente d'abord TOUS les marchés (h2h, btts, totals, double_chance)
    2. Si échec (400 ou vide), fallback sur h2h SEUL
    3. Si échec total, skip la ligue
    """
    all_selections = []
    logs = []
    stats = {'total_ligues': 0, 'success_full': 0, 'success_fallback': 0, 'echec': 0}
    
    if not leagues_list:
        return [], ["Aucune ligue"], stats
    
    pb = st.progress(0, text="🔍 Scan TOUS marchés + Fallback...")
    
    for idx, ligue in enumerate(leagues_list):
        ligue_key = ligue['key']
        nom_court = ligue_key.replace('soccer_', '').replace('_', ' ').upper()
        stats['total_ligues'] += 1
        
        # STRATÉGIE 1: TOUS les marchés
        all_markets = 'h2h,btts,totals,double_chance'
        url = f'https://api.the-odds-api.com/v4/sports/{ligue_key}/odds/?apiKey={API_KEY}&regions=eu&markets={all_markets}&oddsFormat=decimal'
        
        selectionnes_trouvees = False
        
        try:
            r = requests.get(url, timeout=15)
            
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            
            # SUCCÈS: Tous les marchés fonctionnent
            if r.status_code == 200 and r.json():
                logs.append(f"🟢 {nom_court}: MARKETS COMPLETS ✓")
                stats['success_full'] += 1
                selectionnes_trouvees = True
                data = r.json()
            
            # ÉCHEC: Fallback sur h2h seul
            elif r.status_code != 200 or not r.json():
                logs.append(f"⚠️ {nom_court}: Repli sur h2h...")
                url_fallback = f'https://api.the-odds-api.com/v4/sports/{ligue_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal'
                r = requests.get(url_fallback, timeout=15)
                
                if r.status_code == 200 and r.json():
                    logs.append(f"🟡 {nom_court}: Fallback h2h OK")
                    stats['success_fallback'] += 1
                    selectionnes_trouvees = True
                    data = r.json()
                else:
                    logs.append(f"🔴 {nom_court}: ÉCHEC total")
                    stats['echec'] += 1
                    continue
            
            if selectionnes_trouvees and isinstance(data, list) and len(data) > 0:
                for match in data:
                    match_id = match['id']
                    home = match.get('home_team', 'Inconnu')
                    away = match.get('away_team', 'Inconnu')
                    
                    for bk in match.get('bookmakers', []):
                        for mkt in bk.get('markets', []):
                            mkt_key = mkt.get('key', '')
                            
                            for out in mkt.get('outcomes', []):
                                cote = out.get('price', 0)
                                name = out.get('name', '')
                                
                                if cote < 1.20 or cote > 4.50:
                                    continue
                                
                                local_mkt = mkt_key
                                prono_final = name
                                
                                # Normalisation Over/Under
                                if mkt_key == 'totals':
                                    point = out.get('point', 2.5)
                                    if name.lower() == 'over':
                                        local_mkt = 'totals_over'
                                        prono_final = f"Over {point}"
                                    elif name.lower() == 'under':
                                        local_mkt = 'totals_under'
                                        prono_final = f"Under {point}"
                                
                                # Traduction
                                if local_mkt == 'double_chance':
                                    prono_final = DC_MAP.get(name, name)
                                elif local_mkt == 'btts':
                                    prono_final = "Oui" if name.lower() == 'yes' else "Non"
                                elif local_mkt == 'h2h':
                                    if name.lower() == 'draw':
                                        prono_final = "Nul"
                                    elif name == home:
                                        prono_final = f"1 - {home}"
                                    elif name == away:
                                        prono_final = f"2 - {away}"
                                    else:
                                        continue
                                
                                prob = round((1/cote)*100, 1)
                                
                                if prob < 45:
                                    continue
                                
                                lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                
                                all_selections.append({
                                    'match_id': match_id,
                                    'match': f"{home} vs {away}",
                                    'league': nom_court,
                                    'mkt': local_mkt,
                                    'mkt_lbl': lbl,
                                    'mkt_css': css,
                                    'prono': prono_final,
                                    'cote': cote,
                                    'prob': prob,
                                    'confidence': 'high' if prob >= 60 else 'medium' if prob >= 52 else 'low'
                                })
        
        except Exception as e:
            logs.append(f"💥 {nom_court}: {str(e)[:30]}")
            stats['echec'] += 1
        
        pb.progress((idx + 1) / len(leagues_list))
    
    pb.empty()
    
    # Tri par probabilité
    all_selections.sort(key=lambda x: x['prob'], reverse=True)
    
    return all_selections, logs, stats

def generer_pack(selections, cible):
    if not selections:
        return [], 0.0
    
    ticket = []
    cote_total = 1.0
    matches_used = set()
    
    for s in selections:
        if s['match_id'] in matches_used:
            continue
        
        ticket.append(s)
        cote_total *= s['cote']
        matches_used.add(s['match_id'])
        
        if cote_total >= cible * 0.85:
            break
    
    if cote_total >= cible * 0.50:
        return ticket, round(cote_total, 2)
    return [], 0.0

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Contrôle")
    
    api_health = check_api_health()
    if api_health['status']:
        st.markdown("<div class='sidebar-success'>✅ API OK</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-success'>📊 {api_health['remaining']} req</div>", unsafe_allow_html=True)
    else:
        st.markdown("❌ API Hors ligne", unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📊 Marchés ACTIFS")
    st.info("""
    **TOUS les marchés sont activés :**
    ✅ 1X2 (Victoire/Nul)
    ✅ Double Chance (1X, X2, 12)
    ✅ BTTS (Les 2 marquent Oui/Non)
    ✅ Over (Plus de buts)
    ✅ Under (Moins de buts)
    
    **Fallback automatique si blocage API**
    """)
    
    marches_actifs_display = st.multiselect(
        "Marchés (affichés seulement)",
        options=list(MKT_INFO.keys()),
        default=list(MKT_INFO.keys()),
        format_func=lambda x: MKT_INFO[x][0]
    )
    
    st.divider()
    
    active_leagues = get_active_leagues()
    
    if active_leagues:
        options_leagues = {l['key']: l['title'] for l in active_leagues}
        
        default_sel = [k for k in [
            'soccer_usa_mls',
            'soccer_brazil_campeonato',
            'soccer_finland_veikkausliiga',
            'soccer_england_league1',
            'soccer_germany_bundesliga2',
            'soccer_netherlands_erstdive',
            'soccer_sweden_superettan'
        ] if k in options_leagues]
        
        if not default_sel:
            default_sel = [list(options_leagues.keys())[0]]
        
        leagues_choisies = st.multiselect(
            "🏆 Ligues (CHOISISSEZ 5+)",
            options=list(options_leagues.keys()),
            default=default_sel,
            format_func=lambda x: options_leagues[x]
        )
        
        st.info(f"💡 **{len(active_leagues)} ligues** → Choisissez **5+**")
    else:
        st.error("❌ API ligues échoué")
        leagues_choisies = []
    
    st.divider()
    st.markdown(f"💳 Quota: `{st.session_state['api_remaining']}`")
    
    if st.button("↻ LANCER ANALYSE COMPLÈTE", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #2a3550;padding-bottom:1.2rem;margin-bottom:1.8rem">
  <span class="wh-title">BETCORE AI v4.3 - TOUS MARKETS</span><br>
  <span class="wh-sub">1X2 + Double Chance + BTTS + Over + Under + Fallback automatique</span>
</div>
""", unsafe_allow_html=True)

if not leagues_choisies:
    st.info("💡 Sélectionnez des ligues")
    st.stop()

# ─── ANALYSE ──────────────────────────────────────────────────────────────────
with st.spinner(f"🔍 Scan {len(leagues_choisies)} ligues + TOUS marchés..."):
    sels, logs, stats = fetch_all_markets_with_fallback([l for l in active_leagues if l['key'] in leagues_choisies])

# DEBUG COMPLET
with st.expander("🔍 DEBUG - Logs + Stats API", expanded=True):
    st.markdown("### 📊 Statistiques API")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Ligues scannées", stats['total_ligues'])
    with c2: st.metric("Succès complet", f"{stats['success_full']} ✓")
    with c3: st.metric("Fallback h2h", f"{stats['success_fallback']} 🟡")
    with c4: st.metric("Échecs", f"{stats['echec']} 🔴")
    
    st.divider()
    st.markdown("### 📝 Logs détaillés")
    for log in logs:
        if "🟢" in log:
            st.success(log)
        elif "🟡" in log:
            st.warning(log)
        elif "🔴" in log or "💥" in log:
            st.error(log)
        else:
            st.info(log)
    
    st.divider()
    st.markdown(f"""
    **Résultats:**
    - Sélections totales: {len(sels)}
    - Matchs uniques: {len(set(s['match_id'] for s in sels))}
    - Quota reste: `{st.session_state['api_remaining']}`
    """)

if not sels:
    st.error(f"""
    ❌ **AUCUNE SÉLECTION**
    
    **Raisons:**
    - ❌ Ligues sans matchs aujourd'hui
    - ❌ Quota API épuisé: `{st.session_state['api_remaining']}`
    
    **Solutions:**
    ✅ Clique **↻ LANCER ANALYSE**
    ✅ Choisis **5+ ligues**
    ✅ Attends 1h si quota épuisé
    """)
    st.stop()

# Répartition marchés
st.markdown("### 📊 Répartition par marché")
mkt_counts = {}
for s in sels:
    mkt_counts[s['mkt_lbl']] = mkt_counts.get(s['mkt_lbl'], 0) + 1

cols = st.columns(len(mkt_counts))
for idx, (mkt, count) in enumerate(sorted(mkt_counts.items(), key=lambda x: x[1], reverse=True)):
    with cols[idx]:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{count}</div><div class="stat-lbl">{mkt}</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# STATS
unique_matches = len(set(s["match_id"] for s in sels))
high_conf = len([s for s in sels if s['confidence'] == 'high'])
avg_prob = round(sum(s["prob"] for s in sels) / len(sels), 1)

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_matches}</div><div class="stat-lbl">Matchs</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="stat-box"><div class="stat-val">{len(sels)}</div><div class="stat-lbl">Options</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="stat-box"><div class="stat-val">{high_conf}</div><div class="stat-lbl">Haute Conf</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="stat-box"><div class="stat-val">@{avg_prob}%</div><div class="stat-lbl">Prob Moy</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# PACKS
st.markdown("### 🎯 PACKS GÉNÉRÉS")

packs_generes = 0
col_gauche, col_droite = st.columns([3, 2], gap="large")

with col_gauche:
    for cible in PACK_CIBLES:
        tk, total_cote = generer_pack(sels, cible)
        
        if not tk:
            st.markdown(f'<div class="pack-off">📦 <b>PACK ×{cible}</b> — Non disponible</div>', unsafe_allow_html=True)
            continue
        
        packs_generes += 1
        
        st.markdown(f'''
        <div class="pack-card">
            <div class="pack-badge">{total_cote}×</div>
            <div class="pack-top">
                <div>
                    <div class="pack-name">🎯 PACK ×{cible}</div>
                    <div class="pack-meta">{len(tk)} matchs · {round(sum(s["prob"] for s in tk)/len(tk))}% conf · {len(set(s["match_id"] for s in tk))} uniques</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        for s in tk:
            st.markdown(f'''
            <div class="sel-row">
                <div class="sel-league">{s['league']}</div>
                <div class="sel-match">{s['match']}</div>
                <div class="sel-details">
                    <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                    <span style="color:#c8d0e0">👉 {s['prono']}</span>
                    <span class="cote-pill">@{s['cote']}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with col_droite:
    st.markdown("### 🔥 TOP 15")
    for s in sels[:15]:
        st.markdown(f'''
        <div class="rec-row">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-weight:600">{s['match']}</span>
                <span class="cote-pill" style="font-size:1.1rem">@{s['cote']}</span>
            </div>
            <div style="font-size:0.72rem;color:#5a6a8a;margin:4px 0;">{s['league']}</div>
            <div style="display:flex;gap:8px;align-items:center;">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="color:#c8d0e0;font-size:0.85rem">🎯 {s['prono']}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.success(f"✅ {packs_generes}/{len(PACK_CIBLES)} packs | {len(sels)} sélections | {unique_matches} matchs | {high_conf} haute confiance")
