import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import math

# --- 1. CONFIGURACIÓN DE LA TERMINAL ---
st.set_page_config(page_title="NBA AI ELITE TERMINAL V5.1", layout="wide", page_icon="🔥")

# --- 2. EL "PITÓN" (MOTOR DE DATOS AVANZADOS Y RATINGS) ---
# Formato: [Offensive_Rating, Defensive_Rating, Clutch_Factor]
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.12], "Thunder": [118.5, 111.0, 1.08], 
    "Nuggets": [119.0, 112.5, 1.18], "Timberwolves": [114.0, 108.5, 0.94], 
    "Mavericks": [117.5, 115.0, 1.10], "Bucks": [116.0, 116.5, 0.90], 
    "Knicks": [117.2, 112.1, 1.04], "Lakers": [115.0, 114.8, 1.06], 
    "Pelicans": [114.5, 113.2, 0.88], "Warriors": [116.5, 115.5, 1.02],
    "Suns": [117.0, 115.8, 0.98], "76ers": [115.5, 113.0, 1.01],
    "Cavaliers": [116.8, 110.5, 1.05], "Pacers": [120.1, 119.5, 0.96], 
    "Kings": [116.2, 115.0, 1.03]
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "jokic", "edwards", "haliburton", "williamson", "ingram", "mccollum", "butler", "adebayo", "george", "leonard"]

# --- 3. MEMORIA DE SESIÓN ---
if 'analisis_activo' not in st.session_state:
    st.session_state.analisis_activo = False

# --- 4. EXTRACCIÓN DE CONTEXTO (LESIONES Y LINEUPS) ---
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

# --- 5. SIDEBAR (CARRITO DE REFERENCIAS PERMANENTE) ---
inj_db = get_all_context()
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    st.subheader("🚑 Reporte de Lesiones & Lineups")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    es_estrella = any(s in p.lower() for s in STARS)
                    impacto = "🔴 ESTRELLA (-4.0)" if es_estrella else "🟡 ROL (-1.5)"
                    st.write(f"**{p}**\n{impacto}")
    else:
        st.write("No se detectan bajas críticas.")
    
    st.write("---")
    if st.button("🔄 REFRESCAR DATOS NBA"):
        st.rerun()

# --- 6. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO: TERMINAL V5.1")
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

# --- 7. EL PITÓN: LÓGICA DE CÁLCULO (LAS 4 TAREAS) ---
if st.session_state.analisis_activo:
    with st.container():
        st.write("---")
        
        # Tarea 1 & 2: Matchups y Ratings
        stats_l = ADVANCED_STATS.get(l_data['nickname'], [114.0, 114.0, 1.0])
        stats_v = ADVANCED_STATS.get(v_data['nickname'], [112.0, 115.0, 1.0])

        # Mermas por lesionados confirmados en el Carrito
        m_l = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(l_data['nickname'].lower(), [])])
        m_v = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(v_data['nickname'].lower(), [])])

        # Fuerza Proyectada (Ataque Local vs Defensa Visitante y viceversa)
        fuerza_l = (stats_l[0] + stats_v[1]) / 2 + 4.0 - m_l
        fuerza_v = (stats_v[0] + stats_l[1]) / 2 - m_v

        # Tarea 3: Factor Clutch (Impacto en el marcador final)
        final_l = fuerza_l * stats_l[2]
        final_v = fuerza_v * stats_v[2]

        h_ia = round(-(final_l - final_v), 1)
        brecha = abs(h_ia - cuota_casa)

        # Tarea 4: Alerta de Valor y Movimiento Sospechoso
        if brecha >= 6.0:
            st.markdown(f'<div style="background-color:#ff4b4b; color:white; padding:20px; border-radius:10px; text-align:center; font-weight:bold; border: 2px solid white;">🚨 MOVIMIENTO SOSPECHOSO DETECTADO<br>Brecha crítica de {brecha} puntos con la casa de apuestas.</div>', unsafe_allow_html=True)
        
        # Marcador y Sugerencia
        st.subheader(f"📍 Marcador Proyectado: {l_data['nickname']} {round(final_l,1)} - {round(final_v,1)} {v_data['nickname']}")
        
        pick = l_data['nickname'] if h_ia < cuota_casa else v_data['nickname']
        val_pick = h_ia if pick == l_data['nickname'] else abs(h_ia)
        st.success(f"💡 Sugerencia de Apuesta: **{pick} Hándicap {val_pick}**")

        # Desglose por Periodos (Clutch en Q4)
        q1_l, q1_v = round(fuerza_l*0.26,1), round(fuerza_v*0.26,1)
        q2_l, q2_v = round(fuerza_l*0.24,1), round(fuerza_v*0.24,1)
        q3_l, q3_v = round(fuerza_l*0.26,1), round(fuerza_v*0.26,1)
        q4_l, q4_v = round(final_l - (q1_l+q2_l+q3_l), 1), round(final_v - (q1_v+q2_v+q3_v), 1)

        st.table(pd.DataFrame({
            "Equipo": [l_data['nickname'], v_data['nickname']],
            "Q1": [q1_l, q1_v], "Q2": [q2_l, q2_v], "Q3": [q3_l, q3_v], 
            "Q4 (Clutch)": [q4_l, q4_v], "Total": [round(final_l,1), round(final_v,1)]
        }))

        if st.button("❌ CERRAR ANÁLISIS"):
            st.session_state.analisis_activo = False
            st.rerun()