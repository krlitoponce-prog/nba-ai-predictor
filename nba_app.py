import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import math

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE TERMINAL V5.0", layout="wide", page_icon="🔥")

# --- BASE DE DATOS AVANZADA (DATOS 2026) ---
# Ratings: [Offensive_Rating, Defensive_Rating, Clutch_Factor]
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.10], "Thunder": [118.5, 111.0, 1.05],
    "Nuggets": [119.0, 112.5, 1.15], "Timberwolves": [114.0, 108.5, 0.95],
    "Mavericks": [117.5, 115.0, 1.08], "Bucks": [116.0, 116.5, 0.90],
    "Knicks": [117.2, 112.1, 1.02], "Lakers": [115.0, 114.8, 1.05],
    "Pelicans": [114.5, 113.2, 0.92], "Warriors": [116.5, 115.5, 1.00]
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "jokic", "edwards", "haliburton", "williamson", "ingram"]

if 'analisis_activo' not in st.session_state:
    st.session_state.analisis_activo = False

# --- FUNCIONES DE EXTRACCIÓN ---
def get_all_context():
    try:
        # Intentamos simular la lectura de lineups y movimientos de dinero
        # En una app real, aquí haríamos scraping de Action Network o covers.com
        res = requests.get("https://espndeportes.espn.com/basquetbol/nba/lesiones", timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_key = title.text.strip().split()[-1].lower()
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

# --- SIDEBAR (CARRITO DE REFERENCIAS) ---
inj_db = get_all_context()
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    st.subheader("🚑 Reporte de Lesiones & Lineups")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    impacto = "🔴 ESTRELLA (-4.0)" if any(s in p.lower() for s in STARS) else "🟡 ROL (-1.5)"
                    st.write(f"**{p}**\n{impacto}")
    
    st.write("---")
    st.info("💡 Consejo: Si un equipo tiene 'Clutch Factor' < 1.0, ten cuidado con los hándicaps ajustados en el Q4.")

# --- INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO: TERMINAL V5.0")
all_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in all_teams])

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    l_name = st.selectbox("EQUIPO LOCAL", team_names, index=0)
    l_data = next(t for t in all_teams if t['full_name'] == l_name)
with c2:
    v_name = st.selectbox("EQUIPO VISITANTE", team_names, index=1)
    v_data = next(t for t in all_teams if t['full_name'] == v_name)
with c3:
    cuota_casa = st.number_input("Hándicap Casa de Apuestas", value=0.0, step=0.5)

if st.button("🔥 EJECUTAR PREDICCIÓN INTEGRAL"):
    st.session_state.analisis_activo = True

if st.session_state.analisis_activo:
    # 1. LÓGICA DE RATINGS Y MATCHUPS
    stats_l = ADVANCED_STATS.get(l_data['nickname'], [114.0, 114.0, 1.0])
    stats_v = ADVANCED_STATS.get(v_data['nickname'], [112.0, 115.0, 1.0])

    # Merma por lesionados
    m_l = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(l_data['nickname'].lower(), [])])
    m_v = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(v_data['nickname'].lower(), [])])

    # 2. CÁLCULO DE FUERZA (Ataque vs Defensa Rival)
    fuerza_l = (stats_l[0] + stats_v[1]) / 2 + 4.0 - m_l # +4 por localía
    fuerza_v = (stats_v[0] + stats_l[1]) / 2 - m_v

    # 3. FACTOR CLUTCH (Ajuste para el final del juego)
    final_l = fuerza_l * stats_l[2]
    final_v = fuerza_v * stats_v[2]

    h_ia = round(-(final_l - final_v), 1)
    
    st.write("---")
    
    # 4. ALERTA DE DINERO SOSPECHOSO (Tarea 4)
    brecha = abs(h_ia - cuota_casa)
    if brecha >= 6.0:
        st.markdown(f'<div style="background-color:#ff4b4b; color:white; padding:20px; border-radius:10px; text-align:center;">🚨 <b>VALOR MÁXIMO / MOVIMIENTO SOSPECHOSO</b><br>La IA proyecta {h_ia} puntos. Brecha crítica de {brecha} pts con la casa.</div>', unsafe_allow_html=True)

    # Marcador Proyectado
    st.subheader(f"📍 Proyección Final: {l_data['nickname']} {round(final_l,1)} - {round(final_v,1)} {v_data['nickname']}")
    
    # Tabla por Cuartos con Factor Clutch
    st.write("### 📈 Desglose por Periodos")
    dist = [0.26, 0.24, 0.26] # Q1, Q2, Q3
    q1_l, q1_v = round(fuerza_l*0.26,1), round(fuerza_v*0.26,1)
    q2_l, q2_v = round(fuerza_l*0.24,1), round(fuerza_v*0.24,1)
    q3_l, q3_v = round(fuerza_l*0.26,1), round(fuerza_v*0.26,1)
    # El Q4 usa el Factor Clutch (Tarea 3)
    q4_l = round(final_l - (q1_l + q2_l + q3_l), 1)
    q4_v = round(final_v - (q1_v + q2_v + q3_v), 1)

    df_cuartos = pd.DataFrame({
        "Equipo": [l_data['nickname'], v_data['nickname']],
        "Q1": [q1_l, q1_v], "Q2": [q2_l, q2_v], "Q3": [q3_l, q3_v], 
        "Q4 (Clutch)": [q4_l, q4_v],
        "Total": [round(final_l,1), round(final_v,1)]
    })
    st.table(df_cuartos)

    if st.button("❌ CERRAR ANÁLISIS"):
        st.session_state.analisis_activo = False
        st.rerun()