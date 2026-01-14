import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NBA AI Analyst Pro V3", layout="wide", page_icon="🏀")

# --- RANKING DE PODER ACTUALIZADO (POST INDIANA VS BOSTON) ---
TEAM_POWER = {
    "Celtics": 120.5, "Thunder": 120.0, "Nuggets": 119.5, "Timberwolves": 118.0,
    "Mavericks": 118.0, "Bucks": 116.5, "Knicks": 117.0, "Suns": 116.0,
    "Pacers": 117.5, "Lakers": 114.5, "Warriors": 114.0, "Cavaliers": 116.0,
    "76ers": 115.0, "Heat": 114.5, "Kings": 114.0
}

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .handicap-box { 
        font-size: 2rem; font-weight: bold; color: #ff9500; 
        background: #262730; padding: 10px 20px; border-radius: 15px;
        border: 2px solid #ff9500; margin-top: 10px; display: inline-block;
    }
    .paliza-alert {
        background: #ff4b2b; color: white; padding: 8px 15px; 
        border-radius: 8px; font-weight: bold; font-size: 0.9rem;
        margin-top: 15px; display: block; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE DATOS ---
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

# --- INTERFAZ DE USUARIO ---
st.title("🏀 NBA AI: ANALIZADOR PROFESIONAL")
st.write("Análisis basado en ELO Dinámico, Lesiones en Tiempo Real y Proyección por Periodos.")

all_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in all_teams])

col_l, col_v = st.columns(2)
with col_l:
    l_name = st.selectbox("EQUIPO LOCAL", team_names, index=0)
    l_data = next(t for t in all_teams if t['full_name'] == l_name)
    st.image(f"https://cdn.nba.com/logos/nba/{l_data['id']}/global/L/logo.svg", width=80)

with col_v:
    v_name = st.selectbox("EQUIPO VISITANTE", team_names, index=1)
    v_data = next(t for t in all_teams if t['full_name'] == v_name)
    st.image(f"https://cdn.nba.com/logos/nba/{v_data['id']}/global/L/logo.svg", width=80)

if st.button("🔥 EJECUTAR PREDICCIÓN PROFESIONAL"):
    with st.spinner('Procesando datos...'):
        inj_db = get_injuries()
        b_l, b_v = inj_db.get(l_data['nickname'].lower(), []), inj_db.get(v_data['nickname'].lower(), [])
        b2b_l, b2b_v = check_b2b(l_data['id']), check_b2b(v_data['id'])

        # CÁLCULO DE PUNTOS PROYECTADOS (Ajuste Localía +4.0)
        sl = TEAM_POWER.get(l_data['nickname'], 113.0) + 4.0 - (len(b_l) * 2.5) - (4 if b2b_l else 0)
        sv = TEAM_POWER.get(v_data['nickname'], 111.0) - (len(b_v) * 2.5) - (4 if b2b_v else 0)

        diff = sl - sv
        prob_l = 1 / (1 + math.exp(-0.065 * diff))
        p_l, p_v = round(prob_l * 100, 1), round((1 - prob_l) * 100, 1)

        h_l = f"-{abs(round(diff, 1))}" if diff > 0 else f"+{abs(round(diff, 1))}"
        h_v = f"+{abs(round(diff, 1))}" if diff > 0 else f"-{abs(round(diff, 1))}"

        # --- SECCIÓN 1: PROBABILIDAD Y HANDICAP ---
        st.write("---")
        r1, r_vs, r2 = st.columns([1, 0.2, 1])
        
        with r1:
            st.markdown(f"<h1 style='text-align: center; color: #00ff88; margin:0;'>{p_l}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #888;'>{l_data['nickname']}</p>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'><div class='handicap-box'>{h_l}</div></div>", unsafe_allow_html=True)
            if diff >= 12: st.markdown("<div class='paliza-alert'>🔥 PALIZA PROBABLE</div>", unsafe_allow_html=True)

        with r_vs:
            st.markdown("<h2 style='text-align: center; color: #f63366; margin-top: 35px;'>VS</h2>", unsafe_allow_html=True)

        with r2:
            st.markdown(f"<h1 style='text-align: center; color: #1f77b4; margin:0;'>{p_v}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #888;'>{v_data['nickname']}</p>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'><div class='handicap-box'>{h_v}</div></div>", unsafe_allow_html=True)
            if diff <= -12: st.markdown("<div class='paliza-alert'>🔥 PALIZA PROBABLE</div>", unsafe_allow_html=True)

        # --- SECCIÓN 2: DESGLOSE POR CUARTOS ---
        st.write("---")
        st.write("### 📈 Puntos Aproximados por Periodo")
        
        dist = [0.265, 0.235, 0.260, 0.240] # Distribución estadística real
        ql = [round(sl * d, 1) for d in dist]
        qv = [round(sv * d, 1) for d in dist]
        
        df_cuartos = pd.DataFrame({
            "Equipo": [l_data['nickname'], v_data['nickname']],
            "1er Cuarto": [ql[0], qv[0]],
            "2do Cuarto": [ql[1], qv[1]],
            "3er Cuarto": [ql[2], qv[2]],
            "4to Cuarto": [ql[3], qv[3]],
            "Total": [round(sum(ql), 1), round(sum(qv), 1)]
        })
        st.table(df_cuartos)

        # Gráfico comparativo
        fig = go.Figure()
        fig.add_trace(go.Bar(name=l_data['nickname'], x=['Q1','Q2','Q3','Q4'], y=ql, marker_color='#00ff88', text=ql, textposition='auto'))
        fig.add_trace(go.Bar(name=v_data['nickname'], x=['Q1','Q2','Q3','Q4'], y=qv, marker_color='#1f77b4', text=qv, textposition='auto'))
        fig.update_layout(template="plotly_dark", barmode='group', height=300, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.success(f"📍 Marcador Final Proyectado: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")