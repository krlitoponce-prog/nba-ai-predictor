import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import plotly.graph_objects as go
import math
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI Analyst Pro V4.3", layout="wide", page_icon="🏀")

# --- LISTA DE JUGADORES DESEQUILIBRANTES (ESTRELLAS) ---
STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "siakam", "durant", "booker", "brunson", "mitchell", "sabo"]

# --- ESTILOS ---
st.markdown("""
    <style>
    .valormaximo {
        background-color: #ff0000; color: white; padding: 15px;
        border-radius: 10px; border: 3px solid #fff;
        font-weight: bold; text-align: center; font-size: 1.2rem;
        animation: blinker 1s linear infinite; margin-bottom: 20px;
    }
    @keyframes blinker { 50% { opacity: 0.3; } }
    </style>
    """, unsafe_allow_html=True)

# --- RANKING DE PODER ---
TEAM_POWER = {
    "Celtics": 120.5, "Thunder": 120.0, "Nuggets": 119.5, "Timberwolves": 118.0,
    "Mavericks": 118.0, "Bucks": 116.5, "Knicks": 117.0, "Suns": 116.0,
    "Pacers": 117.5, "Lakers": 114.5, "Warriors": 114.0, "Cavaliers": 116.0,
    "76ers": 115.0, "Heat": 114.5, "Kings": 114.0
}

def get_injuries():
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

def check_b2b(team_id):
    try:
        ayer = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        sb = scoreboardv2.ScoreboardV2(game_date=ayer)
        df = sb.get_data_frames()[0]
        return team_id in df['HOME_TEAM_ID'].values or team_id in df['VISITOR_TEAM_ID'].values
    except: return False

# --- SIDEBAR (CARRITO DE REFERENCIAS -> LESIONADOS) ---
inj_db = get_injuries()
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    st.subheader("🚑 Reporte Global de Lesiones")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    impacto = "⭐ Estrella" if any(s in p.lower() for s in STARS) else "🔄 Rol"
                    st.write(f"- {p} ({impacto})")
    else:
        st.write("No se detectan lesiones hoy.")

# --- INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO: COMPARADOR DE VALOR")
all_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in all_teams])

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    l_name = st.selectbox("LOCAL", team_names, index=0)
    l_data = next(t for t in all_teams if t['full_name'] == l_name)
with c2:
    v_name = st.selectbox("VISITANTE", team_names, index=1)
    v_data = next(t for t in all_teams if t['full_name'] == v_name)
with c3:
    cuota_casa = st.number_input("Hándicap Casa de Apuestas", value=0.0, step=0.5)

if st.button("🔥 EJECUTAR ANÁLISIS DE VALOR"):
    with st.spinner('Analizando variables...'):
        b_l = inj_db.get(l_data['nickname'].lower(), [])
        b_v = inj_db.get(v_data['nickname'].lower(), [])
        b2b_l, b2b_v = check_b2b(l_data['id']), check_b2b(v_data['id'])

        # LÓGICA DE IMPACTO SEGÚN CALIDAD DEL JUGADOR
        def calcular_merma(lista_lesionados):
            merma = 0
            for p in lista_lesionados:
                if any(s in p.lower() for s in STARS): merma += 4.0  # Estrella (Desequilibrante)
                else: merma += 1.5  # Reemplazable
            return merma

        sl = TEAM_POWER.get(l_data['nickname'], 113.0) + 4.0 - calcular_merma(b_l) - (4 if b2b_l else 0)
        sv = TEAM_POWER.get(v_data['nickname'], 111.0) - calcular_merma(b_v) - (4 if b2b_v else 0)

        diff = sl - sv
        h_valor = round(-diff, 1)
        h_texto = f"{l_data['nickname']} {h_valor if h_valor < 0 else '+' + str(h_valor)}"
        prob_l = round((1 / (1 + math.exp(-0.065 * diff))) * 100, 1)

        st.write("---")
        brecha = abs(h_valor - cuota_casa)
        
        if brecha >= 6.0:
            st.markdown(f'<div class="valormaximo">🚨 ¡VALOR MÁXIMO! 🚨<br>Diferencia de {brecha} pts con la casa</div>', unsafe_allow_html=True)
        
        st.subheader("💡 Sugerencia de Apuesta")
        if h_valor < cuota_casa:
            st.success(f"Apuesta Recomendada: **{l_data['nickname']} Hándicap {h_valor}**")
        else:
            st.warning(f"Apuesta Recomendada: **{v_data['nickname']} Hándicap {abs(h_valor)}**")

        st.info(f"📍 Marcador Proyectado: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")
        
        dist = [0.265, 0.235, 0.260, 0.240]
        ql, qv = [round(sl * d, 1) for d in dist], [round(sv * d, 1) for d in dist]
        st.table(pd.DataFrame({"Equipo": [l_data['nickname'], v_data['nickname']], "Q1": [ql[0], qv[0]], "Q2": [ql[1], qv[1]], "Q3": [ql[2], qv[2]], "Q4": [ql[3], qv[3]], "Total": [round(sum(ql),1), round(sum(qv),1)]}))