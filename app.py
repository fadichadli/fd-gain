import streamlit as st
import requests
from datetime import datetime, timedelta
import time
from typing import List, Dict, Tuple, Set

# Configuration de la page
st.set_page_config(
    page_title="WinHand AI - BetCore Platinum", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation du session state
if 'api_remaining' not in st.session_state:
    st.session_state['api_remaining'] = "Non vérifié"
if 'last_fetch' not in st.session_state:
    st.session_state['last_fetch'] = None
if 'cache_selections' not in st.session_state:
    st.session_state['cache_selections'] = {}

# Styles CSS améliorés
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { 
    font-family:'DM Sans',sans-serif; 
    background:linear-gradient(135deg, #07090f 0%, #0a0e1a 100%); 
    color:#e8eaf0; 
}
.block-container { padding:1.5rem 2rem; max-width:1300px; }
.wh-title { font-family:'Bebas Neue',sans-serif; font-size:3rem; color:#00e5a0; letter-spacing:0.1em; text-shadow:0 0 20px rgba(0,229,160,0.3); }
.wh-sub   { color:#3a4a6a; font-size:0.85rem; }
.pack-card { 
    background:linear-gradient(135deg, #0d1220 0%, #111827 100%); 
    border:1px solid #1a2540; 
    border-radius:14px; 
    padding:18px 22px; 
    margin-bottom:14px; 
    border-left:4px solid #00e5a0;
    box-shadow:0 4px 12px rgba(0,0,0,0.3);
    transition:transform 0.2s, box-shadow 0.2s;
}
.pack-card:hover {
    transform:translateY(-2px);
    box-shadow:0 6px 20px rgba(0,229,160,0.15);
}
.pack-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.pack-name { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:0.08em; color:#e8eaf0; }
.pack-meta { font-size:0.72rem; color:#3a4a6a; margin-top:2px; }
.pack-cote { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#ffd700; line-height:1; text-shadow:0 0 10px rgba(255,215,0,0.3); }
.sel-row { 
    background:#111827; 
    border:1px solid #1e2a40; 
    border-radius:8px; 
    padding:11px 15px; 
    margin-top:8px;
    transition:background 0.2s;
}
.sel-row:hover { background:#151d30; }
.sel-match  { font-weight:600; font-size:0.88rem; color:#c8d0e0; }
.sel-league { font-size:0.7rem; color:#3a4a6a; margin-bottom:5px; }
.cote-pill  { 
    font-family:'Bebas Neue',sans-serif; 
    font-size:1.15rem; 
    background:rgba(0,229,160,0.1); 
    color:#00e5a0; 
    padding:2px 10px; 
    border-radius:4px; 
    display:inline-block;
    border:1px solid rgba(0,229,160,0.2);
}
.badge { 
    display:inline-block; 
    font-size:0.67rem; 
    font-weight:700; 
    letter-spacing:0.1em; 
    text-transform:uppercase; 
    padding:2px 9px; 
    border-radius:20px;
    border:1px solid transparent;
}
.b-h2h   { background:rgba(0,229,160,0.12); color:#00e5a0; border-color:rgba(0,229,160,0.3); }
.b-dc    { background:rgba(77,159,255,0.12); color:#4d9fff; border-color:rgba(77,159,255,0.3); }
.b-btts  { background:rgba(255,180,0,0.12);  color:#ffb400; border-color:rgba(255,180,0,0.3); }
.b-over  { background:rgba(200,100,255,0.12);color:#c864ff; border-color:rgba(200,100,255,0.3); }
.b-under { background:rgba(255,90,90,0.12);  color:#ff5a5a; border-color:rgba(255,90,90,0.3); }
.stat-box { 
    background:linear-gradient(135deg, #0d1220 0%, #111827 100%); 
    border:1px solid #1a2540; 
    border-radius:10px; 
    padding:14px; 
    text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,0.2);
}
.stat-val { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00e5a0; line-height:1; }
.stat-lbl { font-size:0.7rem; color:#3a4a6a; margin-top:3px; }
.pack-off { 
    background:#0a0d15; 
    border:1px dashed #1a2035; 
    border-radius:14px; 
    padding:14px 22px; 
    margin-bottom:14px; 
    color:#2a3550; 
    font-size:0.8rem;
}
.rec-row { 
    background:#0d1220; 
    border:1px solid #151d30; 
    border-radius:8px; 
    padding:10px 13px; 
    margin-bottom:6px;
    transition:all 0.2s;
}
.rec-row:hover {
    border-color:#1a2540;
    background:#111827;
}
.prob-wrap { background:#0a0f1a; border-radius:3px; height:3px; margin-top:5px; overflow:hidden; }
.prob-fill { 
    height:3px; 
    border-radius:3px; 
    background:linear-gradient(90deg,#0077ff,#00e5a0);
    transition:width 0.5s ease;
}
.sidebar-success { color:#00e5a0; }
.sidebar-error { color:#ff5a5a; }
.sidebar-warn { color:#ffb400; }
.error-box {
    background:rgba(255,90,90,0.1);
    border:1px solid rgba(255,90,90,0.3);
    border-radius:8px;
    padding:12px;
    margin:10px 0;
    color:#ff5a5a;
}
.success-box {
    background:rgba(0,229,160,0.1);
    border:1px solid rgba(0,229,160,0.3);
    border-radius:8px;
    padding:12px;
    margin:10px 0;
    color:#00e5a0;
}
.info-box {
    background:rgba(77,159,255,0.1);
    border:1px solid rgba(77,159,255,0.3);
    border-radius:8px;
    padding:12px;
    margin:10px 0;
    color:#4d9fff;
}
</style>
""", unsafe_allow_html=True)

# ─── CONFIGURATION RENFORCÉE ──────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20]
CACHE_TTL   = 3600  # 1 heure
REQUEST_TIMEOUT = 12

MKT_INFO = {
    'h2h':           ('1X2',            'b-h2h'),
    'double_chance': ('Double Chance',   'b-dc'),
    'btts':          ('Les 2 Marquent',  'b-btts'),
    'totals_over':   ('Over (Buts+)',    'b-over'),
    'totals_under':  ('Under (Buts-)',   'b-under'),
}

DC_MAP = {
    'HomeOrDraw': '1X (Gagnant ou Nul)',
    'AwayOrDraw': 'X2 (Nul ou Gagnant)',
    'HomeOrAway': '12 (Match non Nul)'
}

# ─── FONCTIONS UTILITAIRES ────────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_active_leagues():
    """Récupère les ligues de football actives avec gestion d'erreur améliorée"""
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if 'x-requests-remaining' in r.headers:
                st.session_state['api_remaining'] = r.headers['x-requests-remaining']
            return [s for s in data if s.get('group') == 'Soccer' and not s.get('has_outrights')]
        else:
            st.session_state['api_remaining'] = f"Erreur {r.status_code}"
    except requests.exceptions.Timeout:
        st.session_state['api_remaining'] = "Timeout API"
    except requests.exceptions.RequestException as e:
        st.session_state['api_remaining'] = "Erreur réseau"
    except Exception as e:
        st.session_state['api_remaining'] = "Erreur inconnue"
    return []

@st.cache_data(ttl=300, show_spinner=False)
def check_api_health():
    """Vérifie la santé de l'API"""
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        r = requests.get(url, timeout=10)
        return {
            'status': r.status_code == 200,
            'remaining': r.headers.get('x-requests-remaining', 'Inconnu'),
            'timestamp': datetime.now()
        }
    except:
        return {'status': False, 'remaining': 'N/A', 'timestamp': datetime.now()}

def format_time_ago(dt: datetime) -> str:
    """Formatte le temps écoulé depuis un datetime"""
    delta = datetime.now() - dt
    if delta.seconds < 60:
        return f"{delta.seconds}s"
    elif delta.seconds < 3600:
        return f"{delta.seconds // 60}min"
    else:
        return f"{delta.seconds // 3600}h"

def fetch_selections_secure(leagues_tuple: Tuple, marches_tuple: Tuple) -> List[Dict]:
    """Version améliorée avec logging détaillé, retry logic et meilleure gestion d'erreurs"""
    if not leagues_tuple or not marches_tuple: 
        return []
    
    # Optimisation: regrouper les marchés API
    api_mkts = set()
    for m in marches_tuple: 
        api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)
    
    dict_selections: Dict[str, Dict] = {}
    logs_sidebar: List[str] = []
    success_count = 0
    error_count = 0
    
    total_leagues = len(leagues_tuple)
    pb = st.progress(0, text="🔍 Analyse dynamique en cours...")
    
    for idx, ligue in enumerate(leagues_tuple):
        nom_court = ligue.replace('soccer_', '').replace('_', ' ').upper()
        url = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal'
        
        # Retry logic avec backoff exponentiel
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                r = requests.get(url, timeout=REQUEST_TIMEOUT)
                
                if 'x-requests-remaining' in r.headers:
                    st.session_state['api_remaining'] = r.headers['x-requests-remaining']
                
                # Stratégie de repli pour marchés complexes
                if r.status_code != 200 or not r.json():
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Backoff exponentiel
                        continue
                    
                    logs_sidebar.append(f"⚠️ {nom_court} : Repli sur marchés de base...")
                    url_fallback = f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal'
                    r = requests.get(url_fallback, timeout=REQUEST_TIMEOUT)
                
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list) and len(data) > 0:
                        logs_sidebar.append(f"🟢 {nom_court} : {len(data)} matchs trouvés")
                        success_count += 1
                        
                        for match in data:
                            match_id = match['id']
                            home = match.get('home_team', 'Inconnu')
                            away = match.get('away_team', 'Inconnu')
                            
                            for bk in match.get('bookmakers', []):
                                for mkt in bk.get('markets', []):
                                    mkt_key = mkt.get('key', '')
                                    
                                    for out in mkt.get('outcomes', []):
                                        cote = out.get('price', 1.0)
                                        name = out.get('name', '')
                                        
                                        # Filtre intelligent: éviter les cotes trop basses
                                        if cote <= 1.15: 
                                            continue
                                        
                                        local_mkt = mkt_key
                                        prono_final = name
                                        
                                        # Normalisation des marchés
                                        if mkt_key == 'totals':
                                            point = out.get('point', 2.5)
                                            if name.lower() == 'over':
                                                local_mkt = 'totals_over'
                                                prono_final = f"Over {point} Buts"
                                            elif name.lower() == 'under':
                                                local_mkt = 'totals_under'
                                                prono_final = f"Under {point} Buts"
                                        
                                        if local_mkt not in marches_tuple: 
                                            continue
                                        
                                        if local_mkt == 'double_chance':
                                            prono_final = DC_MAP.get(name, name)
                                        elif local_mkt == 'btts':
                                            prono_final = "Les 2 marquent" if name.lower() == 'yes' else "Pas de but des 2 côtés"
                                        elif local_mkt == 'h2h':
                                            if name.lower() == 'draw': 
                                                prono_final = "Match Nul"
                                            elif name == home: 
                                                prono_final = f"Victoire {home}"
                                            elif name == away: 
                                                prono_final = f"Victoire {away}"
                                        
                                        cle_unique = f"{match_id}_{local_mkt}_{prono_final}"
                                        
                                        # Garder la meilleure cote
                                        if cle_unique not in dict_selections or cote > dict_selections[cle_unique]['cote']:
                                            lbl, css = MKT_INFO.get(local_mkt, (local_mkt, 'b-h2h'))
                                            dict_selections[cle_unique] = {
                                                'match_id': match_id,
                                                'match': f"{home} vs {away}",
                                                'league': nom_court,
                                                'mkt': local_mkt,
                                                'mkt_lbl': lbl,
                                                'mkt_css': css,
                                                'prono': prono_final,
                                                'cote': cote,
                                                'prob': round((1/cote)*100, 1),
                                                'timestamp': datetime.now()
                                            }
                    else:
                        logs_sidebar.append(f"⚪ {nom_court} : Aucun match ouvert")
                        success_count += 1
                else:
                    logs_sidebar.append(f"🔴 {nom_court} : Erreur API {r.status_code}")
                    error_count += 1
                break
                
            except requests.exceptions.Timeout:
                if attempt == max_retries:
                    logs_sidebar.append(f"💥 {nom_court} : Timeout après {max_retries+1} tentatives")
                    error_count += 1
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    logs_sidebar.append(f"💥 {nom_court} : Erreur réseau")
                    error_count += 1
            except Exception as e:
                if attempt == max_retries:
                    logs_sidebar.append(f"💥 {nom_court} : Erreur inconnue")
                    error_count += 1
        
        pb.progress((idx + 1) / total_leagues, text=f"Analyse {idx+1}/{total_leagues} - {nom_court}")
    
    pb.empty()
    
    # Affichage des logs dans la sidebar avec stats
    with st.sidebar.expander(f"📊 Logs d'exécution ({success_count} succès, {error_count} erreurs)", expanded=False):
        for log in logs_sidebar:
            if "🟢" in log:
                st.success(log)
            elif "🔴" in log or "💥" in log:
                st.error(log)
            elif "⚠️" in log:
                st.warning(log)
            else:
                st.info(log)
        
        st.divider()
        st.markdown(f"""
        **Résumé:**
        - Ligues analysées: {total_leagues}
        - Succès: {success_count}
        - Erreurs: {error_count}
        - Sélections uniques: {len(dict_selections)}
        """)
    
    # Tri par probabilité décroissante
    liste_triee = list(dict_selections.values())
    liste_triee.sort(key=lambda x: x['prob'], reverse=True)
    
    # Mise en cache
    st.session_state['cache_selections'] = {
        'data': liste_triee,
        'timestamp': datetime.now(),
        'leagues': leagues_tuple,
        'markets': marches_tuple
    }
    
    return liste_triee

def generer_pack(selections_dispo: List[Dict], cote_cible: float, cles_utilisees: Set[str]) -> Tuple[List[Dict], float]:
    """Algorithme de pack optimisé avec meilleure stratégie de sélection"""
    ticket = []
    cote_accumulee = 1.0
    matches_du_ticket: Set[str] = set()
    
    # Tri par probabilité (meilleures chances en premier)
    for s in selections_dispo:
        id_unique = f"{s['match_id']}_{s['mkt']}_{s['prono']}"
        if id_unique in cles_utilisees or s['match_id'] in matches_du_ticket:
            continue
            
        ticket.append(s)
        cote_accumulee *= s['cote']
        matches_du_ticket.add(s['match_id'])
        cles_utilisees.add(id_unique)
        
        if cote_accumulee >= cote_cible * 0.92:
            break
    
    # Validation du pack
    if cote_accumulee >= cote_cible * 0.75:
        return ticket, round(cote_accumulee, 2)
    else:
        # Rollback: retirer les clés utilisées
        for s in ticket:
            cles_utilisees.discard(f"{s['match_id']}_{s['mkt']}_{s['prono']}")
        return [], 0.0

def calculate_risk_level(total_cote: float) -> Tuple[str, str]:
    """Calcule le niveau de risque avec notation colorée"""
    if total_cote <= 3.5:
        return "🟢 Faible", "success"
    elif total_cote <= 9.0:
        return "🟡 Modéré", "warning"
    else:
        return "🟠 Élevé", "error"

# ─── SIDEBAR AMÉLIORÉE ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Zone de Contrôle AI")
    
    # Vérification santé API
    api_health = check_api_health()
    if api_health['status']:
        st.markdown(f"<div class='sidebar-success'>✅ API Opérationnelle</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-success'>📊 Quota: {api_health['remaining']} requêtes</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sidebar-error'>❌ API Indisponible</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Sélection des marchés
    marches_actifs = st.multiselect(
        "📈 Marchés d'analyse", 
        options=list(MKT_INFO.keys()), 
        default=['h2h', 'double_chance', 'btts', 'totals_over'], 
        format_func=lambda x: MKT_INFO[x][0]
    )
    
    # Récupération ligues actives
    active_leagues_list = get_active_leagues()
    
    if active_leagues_list:
        options_leagues = {l['key']: l['title'] for l in active_leagues_list}
        
        # Ligues par défaut: les plus populaires
        default_sel = [k for k in [
            'soccer_usa_mls', 
            'soccer_brazil_campeonato', 
            'soccer_finland_veikkausliiga',
            'soccer_england_league1',
            'soccer_germany_bundesliga2'
        ] if k in options_leagues]
        
        if not default_sel: 
            default_sel = [list(options_leagues.keys())[0]]
        
        leagues_choisies = st.multiselect(
            "🏆 Ligues à scanner", 
            options=list(options_leagues.keys()), 
            default=default_sel, 
            format_func=lambda x: options_leagues[x]
        )
        
        st.markdown(f"<div style='font-size:0.75rem;color:#3a4a6a'>{len(active_leagues_list)} ligues disponibles</div>", unsafe_allow_html=True)
    else:
        st.error("❌ Impossible de joindre l'API pour lister les ligues.")
        leagues_choisies = []

    st.divider()
    
    # Affichage quota API
    st.markdown(f"💳 **Quota API Restant :** `{st.session_state['api_remaining']}`")
    
    if st.session_state.get('last_fetch'):
        last_fetch = st.session_state['last_fetch']
        st.markdown(f"<div style='font-size:0.7rem;color:#3a4a6a'>Dernière analyse: {format_time_ago(last_fetch)}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📊 Console d'état API")
    status_box = st.empty()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↻ Actualiser", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.session_state['cache_selections'] = {}
            st.rerun()
    
    with col2:
        if st.button("📋 Nettoyer cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache vidé!")
            st.rerun()

# ─── HEADER AMÉLIORÉ ──────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #151d30;padding-bottom:1rem;margin-bottom:1.5rem">
  <span class="wh-title">BETCORE AI PLATINUM v3.7</span><br>
  <span class="wh-sub">Algorithme tolérant aux pannes avec retry logic, fallback automatique et optimisation performance</span>
</div>
""", unsafe_allow_html=True)

# ─── VÉRIFICATION PRÉ-ANALYSE ─────────────────────────────────────────────────
if not leagues_choisies:
    st.info("💡 **Sélectionnez au moins une ligue active** dans le panneau de gauche pour commencer l'analyse.")
    st.stop()

if not marches_actifs:
    st.warning("⚠️ **Sélectionnez au moins un marché** d'analyse dans le panneau de gauche.")
    st.stop()

# Détection cache
use_cache = False
cached_data = None
if st.session_state['cache_selections']:
    cached = st.session_state['cache_selections']
    if (cached.get('leagues') == leagues_choisies and 
        cached.get('markets') == marches_actifs and
        cached.get('timestamp') and
        (datetime.now() - cached['timestamp']).seconds < CACHE_TTL):
        use_cache = True
        cached_data = cached['data']
        st.info(f"📦 **Données en cache**utilisées ( âgées de {format_time_ago(cached['timestamp'])})")

# Exécution analyse
if use_cache and cached_data:
    sels = cached_data
    st.session_state['last_fetch'] = cached['timestamp']
else:
    with st.spinner("🔍 Analyse des ligues en cours..."):
        sels = fetch_selections_secure(tuple(leagues_choisies), tuple(marches_actifs))
        st.session_state['last_fetch'] = datetime.now()

if not sels:
    st.error("""
    ❌ **Aucun match exploitable trouvé**
    
    Possibilités:
    - Les ligues sélectionnées n'ont aucun match programmé dans les 48h
    - L'API est temporairement indisponible
    - Les marchés sélectionnés ne sont pas disponibles
    
    **Solutions:**
    - Sélectionnez d'autres ligues
    - Essayez des marchés différents (1X2, Double Chance)
    - Cliquez sur "Actualiser" dans la sidebar
    """)
    st.stop()

# ─── TABLEAU DE BORD STATISTIQUES ────────────────────────────────────────────
unique_matches = len(set(s["match_id"] for s in sels))
total_selections = len(sels)
avg_prob_top5 = round(sum(s["prob"] for s in sels[:5])/min(5, len(sels)), 1) if sels else 0
total_filters = len(marches_actifs)

c1, c2, c3, c4 = st.columns(4)
with c1: 
    st.markdown(f'<div class="stat-box"><div class="stat-val">{unique_matches}</div><div class="stat-lbl">Matchs Analysés</div></div>', unsafe_allow_html=True)
with c2: 
    st.markdown(f'<div class="stat-box"><div class="stat-val">{total_selections}</div><div class="stat-lbl">Options Identifiées</div></div>', unsafe_allow_html=True)
with c3: 
    st.markdown(f'<div class="stat-box"><div class="stat-val">{avg_prob_top5}%</div><div class="stat-lbl">Confiance Max</div></div>', unsafe_allow_html=True)
with c4: 
    st.markdown(f'<div class="stat-box"><div class="stat-val">{total_filters}</div><div class="stat-lbl">Filtres Actifs</div></div>', unsafe_allow_html=True)

# Indicateurs supplémentaires
st.markdown("<br>", unsafe_allow_html=True)

c5, c6, c7 = st.columns(3)
with c5:
    avg_cote = round(sum(s['cote'] for s in sels) / len(sels), 2) if sels else 0
    st.markdown(f'<div class="stat-box"><div class="stat-val">@{avg_cote}</div><div class="stat-lbl">Cote Moyenne</div></div>', unsafe_allow_html=True)
with c6:
    high_confidence = len([s for s in sels if s['prob'] >= 60])
    st.markdown(f'<div class="stat-box"><div class="stat-val">{high_confidence}</div><div class="stat-lbl">Haute Confiance (≥60%)</div></div>', unsafe_allow_html=True)
with c7:
    packs_possibles = len([c for c in PACK_CIBLES if c <= max(s['cote'] for s in sels) * 3])
    st.markdown(f'<div class="stat-box"><div class="stat-val">{packs_possibles}/{len(PACK_CIBLES)}</div><div class="stat-lbl">Pack
