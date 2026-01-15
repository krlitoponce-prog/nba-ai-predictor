import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V5.6", layout="wide", page_icon="🏀")

# --- 2. EL PITÓN: MOTOR DE RATINGS ---
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

def get_all_context():
    try:
        url = "https://espndeportes.espn.com/basquetbol/nba/lesiones"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_key = title.text.strip().split()[-1].lower()
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

# --- 3. SIDEBAR ---
inj_db = get_all_context()
with st.sidebar:
    st.header("⚙️ Ajustes Físicos")
    b2b_l = st.toggle("¿LOCAL jugó ayer?")
    b2b_v = st.toggle("¿VISITANTE jugó ayer?")
    st.write("---")
    st.header("📂 Carrito de Referencias")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
    if st.button("🔄 RECARGAR WEB"): st.rerun()

# --- 4. INTERFAZ ---
st.title("🏀 NBA AI PRO: V5.6 (Manual Star Override)")
all_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in all_teams])

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", team_names, index=0)
    l_data = next(t for t in all_teams if t['full_name'] == l_name)
    star_out_l = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({l_data['nickname']})")

with c2:
    v_name = st.selectbox("VISITANTE", team_names, index=1)
    v_data = next(t for t in all_teams if t['full_name'] == v_name)
    star_out_v = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({v_data['nickname']})")

if st.button("🔥 CALCULAR CON AJUSTE MANUAL"):
    # LÓGICA DE CÁLCULO
    off_l, def_l, clu_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0])
    off_v, def_v, clu_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0])

    # Penalización Cansancio
    f_cansancio_l = 0.975 if b2b_l else 1.0
    f_cansancio_v = 0.975 if b2b_v else 1.0

    # Penalización Lesiones (Web + Manual)
    red_off_l = 0.08 if star_out_l else 0 # 8% directo si marcas el checkbox
    red_off_v = 0.08 if star_out_v else 0

    # Sumar lo que diga la web si no marcaste el manual
    if not star_out_l:
        for p in inj_db.get(l_data['nickname'].lower(), []):
            red_off_l += 0.045 if any(s in p.lower() for s in STARS) else 0.015
    
    if not star_out_v:
        for p in inj_db.get(v_data['nickname'].lower(), []):
            red_off_v += 0.045 if any(s in p.lower() for s in STARS) else 0.015

    red_off_l = min(red_off_l, 0.15)
    red_off_v = min(red_off_v, 0.15)

    fuerza_l = (((off_l * (1 - red_off_l)) + def_v) / 2) * f_cansancio_l + 3.5
    fuerza_v = (((off_v * (1 - red_off_v)) + def_l) / 2) * f_cansancio_v

    final_l = fuerza_l * clu_l
    final_v = fuerza_v * clu_v
    h_ideal = round(-(final_l - final_v), 1)

    st.success(f"📍 Proyectado Final: {l_data['nickname']} {round(final_l,1)} - {round(final_v,1)} {v_data['nickname']}")
    st.info(f"🎯 Hándicap IA Sugerido: **{h_ideal}**")