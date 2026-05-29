import streamlit as st
import requests
import itertools
from datetime import datetime, timezone, timedelta
from collections import defaultdict

st.set_page_config(page_title="WinHand AI", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#07090f;color:#e8eaf0}
.block-container{padding:1.5rem 2rem;max-width:1300px}
.wh-title{font-family:'Bebas Neue',sans-serif;font-size:3rem;color:#00e5a0;letter-spacing:.1em}
.wh-sub{color:#3a4a6a;font-size:.85rem}
.pack-card{background:#0d1220;border:1px solid #1a2540;border-radius:14px;padding:18px 22px;margin-bottom:14px;border-left:4px solid #00e5a0}
.pack-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
.pack-name{font-family:'Bebas Neue',sans-serif;font-size:1.4rem;letter-spacing:.08em;color:#e8eaf0}
.pack-meta{font-size:.72rem;color:#3a4a6a;margin-top:2px}
.pack-cote{font-family:'Bebas Neue',sans-serif;font-size:2.6rem;color:#ffd700;line-height:1}
.sel-row{background:#111827;border:1px solid #1e2a40;border-radius:8px;padding:11px 15px;margin-top:8px}
.sel-match{font-weight:600;font-size:.88rem;color:#c8d0e0}
.sel-league{font-size:.7rem;color:#3a4a6a;margin-bottom:4px}
.cote-pill{font-family:'Bebas Neue',sans-serif;font-size:1.15rem;background:rgba(0,229,160,.1);color:#00e5a0;padding:1px 10px;border-radius:4px;display:inline-block}
.badge{display:inline-block;font-size:.67rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:2px 9px;border-radius:20px}
.b-h2h  {background:rgba(0,229,160,.12);color:#00e5a0}
.b-dc   {background:rgba(77,159,255,.12);color:#4d9fff}
.b-btts {background:rgba(255,180,0,.12);color:#ffb400}
.b-over {background:rgba(200,100,255,.12);color:#c864ff}
.b-under{background:rgba(255,90,90,.12);color:#ff5a5a}
.stat-box{background:#0d1220;border:1px solid #1a2540;border-radius:10px;padding:14px;text-align:center}
.stat-val{font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#00e5a0;line-height:1}
.stat-lbl{font-size:.7rem;color:#3a4a6a;margin-top:3px}
.pack-off{background:#0a0d15;border:1px dashed #1a2035;border-radius:14px;padding:14px 22px;margin-bottom:14px;color:#2a3550;font-size:.8rem}
.rec-row{background:#0d1220;border:1px solid #151d30;border-radius:8px;padding:10px 13px;margin-bottom:6px}
.prob-wrap{background:#0a0f1a;border-radius:3px;height:3px;margin-top:5px}
.prob-fill{height:3px;border-radius:3px;background:linear-gradient(90deg,#0077ff,#00e5a0)}
.quota-box{background:#0d1220;border:1px solid #1a2540;border-radius:8px;padding:10px 14px;font-size:.75rem;color:#3a4a6a;margin-top:8px}
.log-ok  {color:#00e5a0;font-size:.72rem}
.log-warn{color:#ffb400;font-size:.72rem}
.log-err {color:#ff5a5a;font-size:.72rem}
</style>
""", unsafe_allow_html=True)

# ── CONFIG ─────────────────────────────────────────────────────────────────────
API_KEY     = 'bdbb7557ab0c884d6b6bcb14c33e90fb'
PACK_CIBLES = [2, 3, 5, 10, 20]
FENETRE_H   = 168

MKT_INFO = {
    'h2h':           ('1X2',           'b-h2h'),
    'double_chance': ('Double Chance',  'b-dc'),
    'btts':          ('Les 2 Marquent', 'b-btts'),
    'totals_over':   ('Over',           'b-over'),
    'totals_under':  ('Under',          'b-under'),
}
DC_MAP = {
    'HomeOrDraw': '1X — Domicile ou Nul',
    'AwayOrDraw': 'X2 — Nul ou Extérieur',
    'HomeOrAway': '12 — Match décisif',
}

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for k,v in [('quota','—'),('logs',[]),('nb_matchs',0),('nb_sels',0)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── FETCH LIGUES ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_ligues():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
        if r.status_code == 200:
            return [s for s in r.json()
                    if s.get('group','').lower() in ('soccer','football')
                    and not s.get('has_outrights', False)]
    except:
        pass
    return []

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")

    marches_actifs = st.multiselect(
        "Marchés actifs",
        options=list(MKT_INFO.keys()),
        default=['h2h','double_chance','btts','totals_over','totals_under'],
        format_func=lambda x: MKT_INFO[x][0]
    )

    point_ou = st.selectbox("Seuil Over/Under", [1.5, 2.5, 3.5, 4.5], index=1)

    fenetre = st.selectbox(
        "Fenêtre temporelle",
        [24, 48, 72, 168], index=3,
        format_func=lambda x: f"{x}h ({x//24}j)"
    )

    ligues_data = get_ligues()
    if ligues_data:
        options_l = {l['key']: l['title'] for l in ligues_data}
        defaut    = [k for k in options_l if any(t in k for t in
                     ['mls','brazil','sweden','norway','finland','japan','australia'])]
        defaut    = defaut[:6] if defaut else [list(options_l.keys())[0]]

        ligues_choisies = st.multiselect(
            "Ligues à scanner",
            options=list(options_l.keys()),
            default=defaut,
            format_func=lambda x: options_l.get(x, x)
        )
        st.caption(f"{len(ligues_data)} ligues foot disponibles via l'API")
    else:
        st.error("API inaccessible — vérifiez votre clé.")
        ligues_choisies = []

    st.divider()
    st.markdown(f'<div class="quota-box">💳 Quota API restant : <b>{st.session_state["quota"]}</b></div>',
                unsafe_allow_html=True)

    log_box = st.empty()

    st.divider()
    if st.button("↻ Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #151d30;padding-bottom:1rem;margin-bottom:1.5rem">
  <span class="wh-title">WinHand AI</span><br>
  <span class="wh-sub">1X2 · Double Chance · BTTS · Over · Under — Score IA multi-bookmakers</span>
</div>
""", unsafe_allow_html=True)

# ── MOTEUR PRINCIPAL ───────────────────────────────────────────────────────────
def fetch_selections(ligues_tuple, marches_tuple, fenetre_h, point_ou):
    """
    Pour chaque ligue et chaque match :
      1. Agrège les cotes de tous les bookmakers disponibles
      2. Calcule le Score IA = prob_corrigee + bonus_consensus
         - prob_corrigee : probabilité normalisée sans marge BK
         - bonus_consensus : récompense si plusieurs BK s'accordent
      3. Garde TOUTES les issues valides (pas seulement la meilleure)
         → plus de candidats pour atteindre les cotes cibles des packs
    """
    if not ligues_tuple or not marches_tuple:
        return []

    api_mkts = set()
    for m in marches_tuple:
        api_mkts.add('totals' if m.startswith('totals') else m)
    mkts_str = ','.join(api_mkts)

    maintenant  = datetime.now(timezone.utc)
    fin         = maintenant + timedelta(hours=fenetre_h)
    raw         = {}
    logs        = []

    pb = st.progress(0, text="Scan des ligues...")

    for idx, ligue in enumerate(ligues_tuple):
        nom = ligue.replace('soccer_','').replace('_',' ').title()
        url = (f'https://api.the-odds-api.com/v4/sports/{ligue}/odds/'
               f'?apiKey={API_KEY}&regions=eu&markets={mkts_str}&oddsFormat=decimal')
        try:
            r = requests.get(url, timeout=12)

            if 'x-requests-remaining' in r.headers:
                st.session_state['quota'] = r.headers['x-requests-remaining']

            if r.status_code == 401:
                logs.append(('err', f"{nom} : Clé API invalide"))
                break
            if r.status_code == 403:
                logs.append(('err', f"{nom} : Accès refusé (quota ou IP)"))
                break
            if r.status_code != 200:
                logs.append(('warn', f"{nom} : HTTP {r.status_code}"))
                continue

            data = r.json()
            if not isinstance(data, list) or not data:
                logs.append(('warn', f"{nom} : Aucun match"))
                continue

            for m in data:
                raw[m['id']] = m
            logs.append(('ok', f"{nom} : {len(data)} matchs"))

        except Exception as e:
            logs.append(('err', f"{nom} : Erreur réseau"))

        pb.progress((idx+1)/len(ligues_tuple), text=f"Ligue {idx+1}/{len(ligues_tuple)}...")

    pb.empty()
    st.session_state['logs'] = logs

    # ── Traitement des matchs ────────────────────────────────────────────────
    selections = []

    for match in raw.values():
        try:
            date_m = datetime.fromisoformat(match['commence_time'].replace('Z','+00:00'))
        except:
            continue
        if not (maintenant <= date_m <= fin):
            continue

        home     = match.get('home_team','')
        away     = match.get('away_team','')
        league   = match.get('sport_title','?')
        match_id = match['id']

        dj = (date_m.date() - maintenant.date()).days
        if dj == 0:   label_d = "Auj. " + date_m.strftime('%H:%M')
        elif dj == 1: label_d = "Dem. " + date_m.strftime('%H:%M')
        else:         label_d = date_m.strftime('%d/%m %H:%M')

        # Agréger par sous-marché
        agreg = defaultdict(lambda: defaultdict(list))
        for bk in match.get('bookmakers',[]):
            for mkt in bk.get('markets',[]):
                mk = mkt.get('key','')
                for out in mkt.get('outcomes',[]):
                    cote = out.get('price', 1.0)
                    nom_out = out.get('name','')

                    if mk == 'totals':
                        pt = float(out.get('point', point_ou))
                        if pt != float(point_ou): continue
                        sous_cle = f"totals_{nom_out.lower()}"
                        label_prono = f"{nom_out} {pt} buts"
                        agreg[sous_cle][label_prono].append(cote)
                    elif mk == 'double_chance':
                        label_prono = DC_MAP.get(nom_out, nom_out)
                        agreg[mk][label_prono].append(cote)
                    elif mk == 'btts':
                        label_prono = "Les 2 marquent ✓" if nom_out.lower()=='yes' else "Les 2 ne marquent pas"
                        agreg[mk][label_prono].append(cote)
                    elif mk == 'h2h':
                        if nom_out.lower() == 'draw':
                            label_prono = "Match Nul"
                        elif nom_out == home:
                            label_prono = f"Victoire {home}"
                        else:
                            label_prono = f"Victoire {away}"
                        agreg[mk][label_prono].append(cote)

        # Score IA par sous-marché
        for mkt_key in marches_tuple:
            if mkt_key not in agreg: continue
            issues     = agreg[mkt_key]
            stats      = []
            total_prob = 0

            for nom_issue, cotes in issues.items():
                cote_moy = round(sum(cotes)/len(cotes), 3)
                if cote_moy <= 1.01: continue
                pb_brut    = 1 / cote_moy
                total_prob += pb_brut
                stats.append({'nom': nom_issue, 'cote': cote_moy,
                               'pb': pb_brut, 'nb_bk': len(cotes)})

            if not stats or total_prob == 0: continue

            for s in stats:
                prob_c       = s['pb'] / total_prob        # corrige marge BK
                bonus        = min(s['nb_bk'] / 10.0, 0.20)  # bonus consensus
                s['score_ia'] = round(prob_c + bonus, 4)
                s['prob_pct'] = round(prob_c * 100, 1)

            stats.sort(key=lambda x: x['score_ia'], reverse=True)
            lbl, css = MKT_INFO.get(mkt_key, (mkt_key,'b-h2h'))

            for s in stats:
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
    st.session_state['nb_matchs'] = len(set(s['match_id'] for s in selections))
    st.session_state['nb_sels']   = len(selections)
    return selections

# ── ALGORITHME DE PACK (combinatoire optimisé) ─────────────────────────────────
def construire_ticket(sels, cote_cible, cles_utilisees):
    """
    Cherche la meilleure combinaison (1 à 6 sélections) dont la cote
    combinée est la plus proche de cote_cible.

    Différence vs algorithme greedy (ancien code) :
    - L'ancien code prenait les sélections une par une jusqu'à atteindre la cible
      → résultat sous-optimal, souvent trop loin de la cible
    - Ce code explore TOUTES les combinaisons possibles (jusqu'à 6 matchs)
      → trouve la combinaison mathématiquement la plus proche de la cote cible
    
    Tolérance : 75% à 160% de la cible
    Pénalité si on dépasse trop (évite tickets trop risqués)
    """
    candidats = [
        s for s in sels
        if f"{s['match_id']}_{s['mkt']}_{s['prono']}" not in cles_utilisees
    ][:15]  # top 15 par score IA

    if not candidats: return [], 0.0

    best_t, best_c, best_d = [], 0.0, float('inf')

    for r in range(1, min(7, len(candidats)+1)):
        for combo in itertools.combinations(candidats, r):
            ct = 1.0
            for s in combo: ct *= s['cote']
            if ct < cote_cible * 0.75: continue
            diff = abs(ct - cote_cible)
            if ct > cote_cible * 1.60:
                diff += (ct - cote_cible * 1.60) * 2
            if diff < best_d:
                best_d = diff
                best_c = round(ct, 2)
                best_t = list(combo)

    return best_t, best_c

# ── CHARGEMENT ─────────────────────────────────────────────────────────────────
if not ligues_choisies or not marches_actifs:
    st.info("💡 Sélectionnez au moins une ligue et un marché dans le panneau de gauche.")
    st.stop()

with st.spinner("Analyse en cours..."):
    sels = fetch_selections(
        tuple(ligues_choisies), tuple(marches_actifs), fenetre, point_ou
    )

# Affichage logs sidebar
with log_box.container():
    for typ, msg in st.session_state.get('logs', []):
        css_cls = 'log-ok' if typ=='ok' else 'log-warn' if typ=='warn' else 'log-err'
        st.markdown(f'<span class="{css_cls}">{msg}</span>', unsafe_allow_html=True)

if not sels:
    st.error("❌ Aucun match trouvé. Vérifiez : (1) votre quota API, (2) les ligues sélectionnées ont bien des matchs programmés, (3) la fenêtre temporelle.")
    st.stop()

# ── STATS ──────────────────────────────────────────────────────────────────────
score_moy = round(sum(s['score_ia'] for s in sels)/len(sels)*100, 1) if sels else 0
c1,c2,c3,c4 = st.columns(4)
for col,(v,l) in zip([c1,c2,c3,c4],[
    (st.session_state['nb_matchs'], "Matchs analysés"),
    (st.session_state['nb_sels'],   "Sélections IA"),
    (f"{score_moy}%",               "Fiabilité moyenne"),
    (len(marches_actifs),           "Marchés actifs"),
]):
    with col:
        st.markdown(f'<div class="stat-box"><div class="stat-val">{v}</div><div class="stat-lbl">{l}</div></div>',
                    unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── PACKS + RÉCAP ──────────────────────────────────────────────────────────────
col_g, col_d = st.columns([3,2], gap="large")
cles_utilisees = set()

with col_g:
    st.markdown("### 📦 Tickets du jour")

    for cible in PACK_CIBLES:
        ticket, cote_r = construire_ticket(sels, cible, cles_utilisees)

        if not ticket:
            restantes = [s for s in sels
                         if f"{s['match_id']}_{s['mkt']}_{s['prono']}" not in cles_utilisees]
            if not restantes:
                raison = "Toutes les sélections ont été utilisées."
            else:
                top5 = sorted([s['cote'] for s in restantes], reverse=True)[:6]
                max_a = 1.0
                for c in top5: max_a *= c
                raison = (f"×{cible} non atteignable — max ≈ ×{round(max_a,1)} "
                          f"avec les sélections restantes. Ajoutez des ligues.")
            st.markdown(f'<div class="pack-off">📦 <b>Pack ×{cible}</b> — ⚠️ {raison}</div>',
                        unsafe_allow_html=True)
            continue

        nb_s   = len(ticket)
        fiab   = round(sum(s['score_ia'] for s in ticket)/nb_s*100, 1)
        risque = ("🟢 Faible" if cote_r<=3 else "🟡 Modéré" if cote_r<=7
                  else "🟠 Élevé" if cote_r<=12 else "🔴 Très élevé")

        rows = ""
        for s in ticket:
            bw = min(int(s['prob']), 100)
            rows += f"""
            <div class="sel-row">
              <div class="sel-league">{s['league']} — {s['date']}</div>
              <div class="sel-match">{s['match']}</div>
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:5px">
                <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
                <span style="font-size:.83rem;color:#e8eaf0">▶ {s['prono']}</span>
                <span class="cote-pill">@{s['cote']}</span>
                <span style="margin-left:auto;font-size:.68rem;color:#3a4a6a">
                  {s['prob']}% · {s['nb_bk']} BK · IA {s['score_ia']}
                </span>
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

with col_d:
    st.markdown("### 📋 Flux des sélections IA")

    filtre_mkt = st.selectbox(
        "Filtrer par marché",
        ['Tous'] + [MKT_INFO[m][0] for m in marches_actifs]
    )

    affichees = 0
    for s in sels:
        if filtre_mkt != 'Tous' and s['mkt_lbl'] != filtre_mkt:
            continue
        if affichees >= 30: break
        used = " ✓" if f"{s['match_id']}_{s['mkt']}_{s['prono']}" in cles_utilisees else ""
        bw = min(int(s['prob']), 100)
        st.markdown(f"""
        <div class="rec-row">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:600;font-size:.83rem;color:#c8d0e0">{s['match']}{used}</span>
            <span class="cote-pill">@{s['cote']}</span>
          </div>
          <div style="font-size:.68rem;color:#3a4a6a">{s['league']} · {s['date']}</div>
          <div style="display:flex;gap:6px;align-items:center;margin-top:4px">
            <span class="badge {s['mkt_css']}">{s['mkt_lbl']}</span>
            <span style="font-size:.79rem;color:#e8eaf0">▶ {s['prono']}</span>
          </div>
          <div class="prob-wrap"><div class="prob-fill" style="width:{bw}%"></div></div>
          <div style="font-size:.64rem;color:#3a4a6a;margin-top:2px">
            {s['prob']}% · {s['nb_bk']} BK · score IA {s['score_ia']}
          </div>
        </div>""", unsafe_allow_html=True)
        affichees += 1

st.markdown('<div style="text-align:center;color:#1a2035;font-size:.7rem;margin-top:2rem">WinHand AI — The Odds API — Pariez de façon responsable</div>',
            unsafe_allow_html=True)
