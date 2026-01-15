import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V5.9", layout="wide", page_icon="🏀")

# --- 2. MOTOR DE RATINGS ---
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.12], "Thunder": [118.5, 111.0, 1.08], "Nuggets": [119.0, 112.5, 1.18],
    "Timberwolves": [114.0, 108.5, 0.94], "Mavericks": [117.5, 115.0, 1.10], "Bucks": [116.0, 116.5, 0.90],
    "Knicks": [117.2, 112.1, 1.04], "76ers": [115.5, 113.0, 1.01], "Cavaliers": [116.8, 110.5, 1.05],
    "Suns": [117.0, 115.8, 0.98], "Pacers": [120.1, 119.5, 0.96], "Kings": [116.2, 115.0, 1.03],
    "Lakers": [115.0, 114.8, 1.06], "Pelicans": [114.5, 113.2, 0.88], "Warriors": [116.5, 115.5, 1.02],
    "Magic": [110.5, 109.8, 0.95], "Heat": [113.2, 111.5, 1.07], "Rockets": [112.8, 112.0, 0.99],
    "Hawks": [118.0, 120.5, 0.94], "Bulls": [113.8, 115.5, 1.04], "Jazz": [115.2, 119.0, 0.97],
    "Nets": [112.0, 116.0, 0.95], "Raptors": [112.5, 117.8, 0.92], "Grizzlies": [111.5, 113.0, 1.00],
    "Spurs": [110.0, 115.5, 1.05], "Hornets": [109.5, 118.2, 0.91], "Pistons": [108.2, 117.5, 0.89],
    "Trail Blazers": [109.0, 116.5, 0.93], "Wizards": [111.2, 119.8, 0.90], "Clippers": [115.8, 113.5, 1.02]
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "williamson", "ingram", "mccollum", "butler", "adebayo", "george", "leonard", "fox", "sabonis", "brunson", "mitchell", "siakam", "barnes", "markkanen", "lavine", "derozan", "bridges"]

# --- 3. EXTRACCIÓN Y SIDEBAR (CARRITO PERMANENTE) ---
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
    st.header("⚙️ Ajustes de Energía")
    b2b_l = st.toggle("Local en Back-to-Back")
    b2b_v = st.toggle("Visita en Back-to-Back")
    st.write("---")
    st.header("📂 Carrito Permanente")
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
            else: st.write("✅ Plantilla Completa")
    if st.button("🔄 ACTUALIZAR"): st.rerun()

# --- 4. INTERFAZ Y COMPARATIVA TÁCTICA ---
st.title("🏀 NBA AI PRO V5.9: CLUTCH ANALYZER")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_data = next(t for t in all_nba_teams if t['full_name'] == l_name)
    s_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0])
    manual_l = st.checkbox(f"🚨 BAJA ESTRELLA ({l_data['nickname']})")
    # Muestra de Factor Clutch
    st.metric(label=f"Factor Clutch {l_data['nickname']}", value=f"x{s_l[2]}", delta="Superior a 1.0 es Élite" if s_l[2] > 1.0 else "Debilidad en cierre")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_data = next(t for t in all_nba_teams if t['full_name'] == v_name)
    s_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0])
    manual_v = st.checkbox(f"🚨 BAJA ESTRELLA ({v_data['nickname']})")
    # Muestra de Factor Clutch
    st.metric(label=f"Factor Clutch {v_data['nickname']}", value=f"x{s_v[2]}", delta="Superior a 1.0 es Élite" if s_v[2] > 1.0 else "Debilidad en cierre")

st.write("---")

if st.button("🔥 GENERAR ANÁLISIS COMPLETO"):
    # Penalizaciones
    red_l = 0.08 if manual_l else 0
    if not manual_l:
        for p in inj_db.get(l_data['nickname'].lower(), []):
            red_l += 0.045 if any(s in p.lower() for s in STARS) else 0.015
    
    red_v = 0.08 if manual_v else 0
    if not manual_v:
        for p in inj_db.get(v_data['nickname'].lower(), []):
            red_v += 0.045 if any(s in p.lower() for s in STARS) else 0.015

    red_l, red_v = min(red_l, 0.15), min(red_v, 0.15)
    f_c_l = 0.975 if b2b_l else 1.0
    f_c_v = 0.975 if b2b_v else 1.0
    
    # PROYECCIÓN
    f_l = (((s_l[0] * (1-red_l)) + s_v[1]) / 2 + 3.5) * f_c_l
    f_v = (((s_v[0] * (1-red_v)) + s_l[1]) / 2) * f_c_v

    q_base_l, q_base_v = f_l / 4, f_v / 4
    
    # Tabla de Cuartos
    qs = {
        "Cuarto": ["Q1", "Q2", "Q3", "Q4 (Clutch)", "TOTAL FINAL"],
        l_data['nickname']: [round(q_base_l,1), round(q_base_l,1), round(q_base_l*0.95,1), round(q_base_l*s_l[2],1), round(f_l*s_l[2],1)],
        v_data['nickname']: [round(q_base_v,1), round(q_base_v,1), round(q_base_v*0.95,1), round(q_base_v*s_v[2],1), round(f_v*s_v[2],1)]
    }
    
    st.table(pd.DataFrame(qs))
    
    h_final = round(-( (f_l*s_l[2]) - (f_v*s_v[2]) ), 1)
    st.info(f"🎯 Hándicap Sugerido (Incluyendo Factores de Cierre): **{h_final}**")