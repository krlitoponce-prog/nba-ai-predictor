import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V8.5", layout="wide", page_icon="🏀")

# --- 2. BASE DE DATOS ADN NBA (Estadísticas Base + Localía Específica) ---
ADVANCED_STATS = {
    "Celtics": [123.5, 110.5, 1.12, 4.8, 0.99], "Thunder": [119.5, 110.0, 1.09, 3.8, 1.02],
    "Nuggets": [118.0, 112.0, 1.18, 5.8, 0.97], "76ers": [116.5, 113.5, 1.02, 3.5, 0.98],
    "Cavaliers": [117.2, 110.2, 1.06, 3.8, 0.98], "Lakers": [116.0, 115.0, 1.07, 4.2, 1.03],
    "Warriors": [117.5, 115.8, 1.04, 4.5, 1.02], "Knicks": [118.0, 111.5, 1.05, 4.5, 0.95],
    "Mavericks": [118.8, 115.2, 1.11, 4.0, 0.98], "Bucks": [117.0, 116.2, 0.95, 4.1, 1.01],
    "Timberwolves": [114.5, 108.2, 0.96, 4.0, 0.97], "Suns": [117.8, 116.0, 1.01, 3.8, 0.99],
    "Pacers": [121.5, 120.0, 0.98, 3.6, 1.08], "Kings": [116.8, 115.5, 1.03, 4.2, 1.01],
    "Heat": [114.0, 111.8, 1.08, 4.3, 0.96], "Magic": [111.5, 109.5, 0.96, 3.7, 0.98],
    "Clippers": [115.5, 114.0, 1.03, 3.8, 0.97], "Rockets": [113.8, 112.5, 1.01, 3.6, 1.00],
    "Pelicans": [115.0, 113.8, 0.92, 3.5, 0.99], "Hawks": [118.5, 121.2, 0.95, 3.4, 1.05],
    "Grizzlies": [113.0, 112.8, 1.01, 3.8, 1.01], "Bulls": [114.2, 116.5, 1.04, 3.5, 0.99],
    "Nets": [112.5, 116.8, 0.96, 3.2, 0.99], "Raptors": [113.2, 118.0, 0.94, 3.7, 1.00],
    "Jazz": [115.8, 120.5, 0.98, 4.6, 1.01], "Spurs": [111.0, 115.2, 1.05, 3.6, 1.02],
    "Hornets": [110.2, 119.5, 0.93, 3.2, 1.01], "Pistons": [109.5, 118.0, 0.90, 3.1, 0.99],
    "Wizards": [111.8, 122.5, 0.91, 3.0, 1.04], "Trail Blazers": [110.0, 117.5, 0.93, 3.8, 0.98]
}

STARS_DB = {
    "tatum": [22.5, 18.5, 29.5], "jokic": [31.5, 25.0, 32.1], "doncic": [28.1, 23.5, 35.8], 
    "james": [23.0, 19.0, 28.5], "curry": [24.5, 20.0, 30.2], "embiid": [30.2, 24.5, 34.0], 
    "antetokounmpo": [29.8, 24.0, 32.5], "davis": [25.0, 20.5, 26.8], "durant": [24.0, 21.0, 29.0],
    "booker": [21.5, 18.5, 28.0], "gilgeous": [27.5, 22.0, 31.5], "brunson": [21.5, 17.5, 30.5]
}

# --- 3. FUNCIONES DE DATOS ---
@st.cache_data(ttl=600)
def get_espn_injuries():
    try:
        res = requests.get("https://espndeportes.espn.com/basquetbol/nba/lesiones", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_raw = title.text.strip().lower()
            team_key = "76ers" if "76ers" in team_raw else team_raw.split()[-1]
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

def perform_auto_detection(team_nick, injuries_db):
    bajas_equipo = injuries_db.get(team_nick.lower(), [])
    penalizacion = 0.0
    detected_stars = []
    for player in bajas_equipo:
        for star, stats in STARS_DB.items():
            if star in player.lower():
                # Penalización exacta basada en el rendimiento
                impacto_p = (stats[0]/200) + (stats[1]/200) + (stats[2]/600)
                penalizacion += impacto_p
                detected_stars.append(f"{player} (USG%: {stats[2]})")
    return min(0.26, penalizacion), detected_stars

# --- 4. SIDEBAR ---
inj_db = get_espn_injuries()
with st.sidebar:
    st.header("⚙️ OPCIONES")
    if st.button("🔄 ACTUALIZAR LESIONADOS"):
        st.cache_data.clear(); st.rerun()
    st.subheader("💰 LÍNEAS CASINO")
    linea_ou = st.number_input("Over/Under", value=220.0, step=0.5)
    linea_spread = st.number_input("Hándicap Local", value=0.0, step=0.5)
    
    st.subheader("📍 LISTA LATERAL DE LESIONADOS")
    for t_nick_disp in sorted(ADVANCED_STATS.keys()):
        bajas_sidebar = inj_db.get(t_nick_disp.lower(), [])
        if bajas_sidebar:
            with st.expander(f"📍 {t_nick_disp.upper()}"):
                for p in bajas_sidebar: st.write(f"• {p}")

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V8.5")

# BOTÓN DE LESIONADOS EN TIEMPO REAL (SOLICITADO)
with st.expander("🔍 VER REPORTE DE LESIONADOS EN TIEMPO REAL (ESPN)"):
    cols = st.columns(3)
    for i, (team, players) in enumerate(inj_db.items()):
        cols[i % 3].markdown(f"**{team.upper()}**")
        for p in players:
            cols[i % 3].caption(f"❌ {p}")

c1, c2 = st.columns(2)

with c1:
    l_nick = st.selectbox("LOCAL", sorted(ADVANCED_STATS.keys()), index=5)
    penal_auto_l, estrellas_l = perform_auto_detection(l_nick, inj_db)
    if estrellas_l: 
        st.error(f"📉 Impacto Bajas: -{round(penal_auto_l*100, 1)}% en ataque")
        st.caption(f"Bajas: {', '.join(estrellas_l)}")
    else: st.success("✅ Plantilla completa")
    l_pg = st.checkbox("Falta Base (PG)", key="lpg")
    venganza_l = st.checkbox("🔥 Venganza", key="vl")

with c2:
    v_nick = st.selectbox("VISITANTE", sorted(ADVANCED_STATS.keys()), index=23)
    penal_auto_v, estrellas_v = perform_auto_detection(v_nick, inj_db)
    if estrellas_v: 
        st.error(f"📉 Impacto Bajas: -{round(penal_auto_v*100, 1)}% en ataque")
        st.caption(f"Bajas: {', '.join(estrellas_v)}")
    else: st.success("✅ Plantilla completa")
    v_pg = st.checkbox("Falta Base (PG)", key="vpg")
    venganza_v = st.checkbox("🔥 Venganza", key="vv")

# --- 6. MOTOR DE CÁLCULO ---
if st.button("🚀 ANALIZAR PARTIDO"):
    s_l, s_v = ADVANCED_STATS[l_nick], ADVANCED_STATS[v_nick]
    
    # Penalizaciones finales
    red_l = penal_auto_l + (0.02 if l_pg else 0)
    red_v = penal_auto_v + (0.02 if v_pg else 0)
    
    ritmo_p = (s_l[4] + s_v[4]) / 2
    
    pot_l = (((s_l[0] * (1 - red_l + (0.03 if venganza_l else 0))) * 0.7) + (s_v[1] * 0.3)) * ritmo_p
    pot_v = (((s_v[0] * (1 - red_v + (0.03 if venganza_v else 0))) * 0.7) + (s_l[1] * 0.3)) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    st.session_state.analisis = {"l": l_nick, "v": v_nick, "rl": res_l, "rv": res_v, "total": round(res_l+res_v, 1)}

# --- 7. RESULTADOS Y TABLA DE CUARTOS ---
if 'analisis' in st.session_state:
    res = st.session_state.analisis
    st.divider()
    st.header(f"📊 {res['l']} {res['rl']} - {res['rv']} {res['v']}")
    
    # Tabla de Cuartos Restaurada
    dist = [0.26, 0.26, 0.24, 0.24]
    df_qs = pd.DataFrame({
        "Periodo": ["Q1", "Q2", "Q3", "Q4", "FINAL"],
        res['l']: [round(res['rl']*d, 1) for d in dist] + [res['rl']],
        res['v']: [round(res['rv']*d, 1) for d in dist] + [res['rv']]
    })
    st.table(df_qs)
    
    st.metric("Total Proyectado", res['total'], delta=f"{round(res['total'] - linea_ou, 1)} vs Línea")