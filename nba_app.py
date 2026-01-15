import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V6.7", layout="wide", page_icon="🎯")

# --- 2. BASE DE DATOS DE LOS 30 EQUIPOS (Ratings 2026) ---
# Estructura: [Ataque, Defensa, Clutch (Cierre), Localía]
ADVANCED_STATS = {
    "Celtics": [123.5, 110.5, 1.12, 4.8], "Thunder": [119.5, 110.0, 1.09, 3.8],
    "Nuggets": [118.0, 112.0, 1.18, 5.8], "76ers": [116.5, 113.5, 1.02, 3.5],
    "Cavaliers": [117.2, 110.2, 1.06, 3.8], "Lakers": [116.0, 115.0, 1.07, 4.2],
    "Warriors": [117.5, 115.8, 1.04, 4.5], "Knicks": [118.0, 111.5, 1.05, 4.5],
    "Mavericks": [118.8, 115.2, 1.11, 4.0], "Bucks": [117.0, 116.2, 0.95, 4.1],
    "Timberwolves": [114.5, 108.2, 0.96, 4.0], "Suns": [117.8, 116.0, 1.01, 3.8],
    "Pacers": [121.5, 120.0, 0.98, 3.6], "Kings": [116.8, 115.5, 1.03, 4.2],
    "Heat": [114.0, 111.8, 1.08, 4.3], "Magic": [111.5, 109.5, 0.96, 3.7],
    "Clippers": [115.5, 114.0, 1.03, 3.8], "Rockets": [113.8, 112.5, 1.01, 3.6],
    "Pelicans": [115.0, 113.8, 0.92, 3.5], "Hawks": [118.5, 121.2, 0.95, 3.4],
    "Grizzlies": [113.0, 112.8, 1.01, 3.8], "Bulls": [114.2, 116.5, 1.04, 3.5],
    "Nets": [112.5, 116.8, 0.96, 3.2], "Raptors": [113.2, 118.0, 0.94, 3.7],
    "Jazz": [115.8, 120.5, 0.98, 4.6], "Spurs": [111.0, 115.2, 1.05, 3.6],
    "Hornets": [110.2, 119.5, 0.93, 3.2], "Pistons": [109.5, 118.0, 0.90, 3.1],
    "Wizards": [111.8, 122.5, 0.91, 3.0], "Trail Blazers": [110.0, 117.5, 0.93, 3.8]
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "mitchell", "brunson", "wembanayama", "morant", "adebayo", "butler", "banchero", "sabonis", "fox"]

# --- 3. EXTRACCIÓN Y SIDEBAR (CARRITO PERMANENTE) ---
@st.cache_data(ttl=600)
def get_all_context():
    try:
        url = "https://espndeportes.espn.com/basquetbol/nba/lesiones"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_raw = title.text.strip().lower()
            if "76ers" in team_raw: team_key = "76ers"
            else: team_key = team_raw.split()[-1]
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

all_nba_teams = teams.get_teams()
inj_db = get_all_context()

with st.sidebar:
    st.header("📂 Carrito Permanente")
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname']
        bajas = inj_db.get(nick.lower(), [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
            else: st.write("✅ Plantilla Completa")
    if st.button("🔄 ACTUALIZAR WEB"): st.rerun()

# --- 4. INTERFAZ ---
st.title("🏀 NBA AI PRO V6.7: 30-TEAM TERMINAL")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_data = next(t for t in all_nba_teams if t['full_name'] == l_name)
    s_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0, 3.5])
    m_l = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({l_data['nickname']})")
    st.metric(f"Clutch {l_data['nickname']}", f"x{s_l[2]}", f"Home: +{s_l[3]}")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_data = next(t for t in all_nba_teams if t['full_name'] == v_name)
    s_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0, 3.5])
    m_v = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({v_data['nickname']})")
    st.metric(f"Clutch {v_data['nickname']}", f"x{s_v[2]}", "Visitante")

# --- 5. CÁLCULO DE PRECISIÓN ---
if st.button("🚀 ANALIZAR PARTIDO"):
    red_l = 0.08 if m_l else 0
    if not m_l:
        for p in inj_db.get(l_data['nickname'].lower(), []):
            red_l += 0.045 if any(s in p.lower() for s in STARS) else 0.015
    
    red_v = 0.08 if m_v else 0
    if not m_v:
        for p in inj_db.get(v_data['nickname'].lower(), []):
            red_v += 0.045 if any(s in p.lower() for s in STARS) else 0.015

    # Lógica 70/30 (Ofensiva/Defensa Rival)
    pot_l = ((s_l[0] * (1 - min(red_l, 0.15))) * 0.7) + (s_v[1] * 0.3)
    pot_v = ((s_v[0] * (1 - min(red_v, 0.15))) * 0.7) + (s_l[1] * 0.3)
    
    res_l, res_v = round((pot_l + s_l[3]) * s_l[2], 1), round(pot_v * s_v[2], 1)
    h_final, total = round(-(res_l - res_v), 1), round(res_l + res_v, 1)

    st.divider()
    st.subheader(f"📊 {l_data['nickname']} {res_l} - {res_v} {v_data['nickname']}")
    
    c_res1, c_res2 = st.columns(2)
    with c_res1: st.success(f"🎯 Hándicap: {h_final}")
    with c_res2: st.warning(f"🏀 Total Puntos (O/U): {total}")

    # Tabla de Cuartos
    q_l, q_v = res_l/4, res_v/4
    qs = {"Periodo": ["Q1", "Q2", "Q3", "Q4 (Clutch)", "TOTAL"],
          l_data['nickname']: [round(q_l,1), round(q_l,1), round(q_l*0.95,1), round(q_l*s_l[2],1), res_l],
          v_data['nickname']: [round(q_v,1), round(q_v,1), round(q_v*0.95,1), round(q_v*s_v[2],1), res_v]}
    st.table(pd.DataFrame(qs))