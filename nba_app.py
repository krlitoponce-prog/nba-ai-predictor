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

# --- RANKING DE PODER ACTUALIZADO ---
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
    .status-tag {
        padding: 4px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; margin: 2px;
    }
    .tag-injury { background: #ff4b2b; color: white; }
    .tag-b2b { background: #ffcc00; color: black; }
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
        # Revisa si jugaron ayer (Back-to-Back)
        ayer = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        sb = scoreboardv2.ScoreboardV2(game_date=ayer)
        df = sb.get_data_frames()[0]
        # Retorna True si el ID del equipo aparece en los juegos de ayer
        return team_id in df['HOME_TEAM_ID'].values or team_id in df['VISITOR_TEAM_ID'].values
    except: return False

# --- INTERFAZ ---
st.title("🏀 NBA AI: ANALIZADOR PROFESIONAL")

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
    with st.spinner('Escaneando lesiones y fatiga...'):
        inj_db = get_injuries()
        b_l = inj_db.get(l_data['nickname'].lower(), [])
        b_v = inj_db.get(v_data['nickname'].lower(), [])
        
        b2b_l = check_b2b(l_data['id'])
        b2b_v = check_b2b(v_data['id'])

        # CÁLCULO DE PUNTOS (Localía +4.0 | Lesión -2.5 | B2B -4.0)
        sl = TEAM_POWER.get(l_data['nickname'], 113.0) + 4.0 - (len(b_l) * 2.5) - (4 if b2b_l else 0)
        sv = TEAM_POWER.get(v_data['nickname'], 111.0) - (len(b_v) * 2.5) - (4 if b2b_v else 0)

        # --- MOSTRAR ALERTAS DETECTADAS ---
        st.write("### 📢 Reporte de Situación")
        c_a, c_b = st.columns(2)
        with c_a:
            st.write(f"**{l_data['nickname']}:**")
            if b2b_l: st.markdown('<span class="status-tag tag-b2b">⚠️ JUGÓ AYER (FATIGA)</span>', unsafe_allow_html=True)
            if b_l: st.markdown(f'<span class="status-tag tag-injury">🚑 {len(b_l)} LESIONADOS</span>', unsafe_allow_html=True)
            if not b2b_l and not b_l: st.write("✅ Plantilla completa y descansada.")
        
        with c_b:
            st.write(f"**{v_data['nickname']}:**")
            if b2b_v: st.markdown('<span class="status-tag tag-b2b">⚠️ JUGÓ AYER (FATIGA)</span>', unsafe_allow_html=True)
            if b_v: st.markdown(f'<span class="status-tag tag-injury">🚑 {len(b_v)} LESIONADOS</span>', unsafe_allow_html=True)
            if not b2b_v and not b_v: st.write("✅ Plantilla completa y descansada.")

        # --- RESULTADOS PRINCIPALES ---
        diff = sl - sv
        prob_l = 1 / (1 + math.exp(-0.065 * diff))
        p_l, p_v = round(prob_l * 100, 1), round((1 - prob_l) * 100, 1)

        st.write("---")
        r1, r_vs, r2 = st.columns([1, 0.2, 1])
        with r1:
            st.markdown(f"<h1 style='text-align: center; color: #00ff88;'>{p_l}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'><div class='handicap-box'>{'-'+str(abs(round(diff, 1))) if diff > 0 else '+'+str(abs(round(diff, 1)))}</div></div>", unsafe_allow_html=True)
        with r_vs: st.markdown("<h2 style='text-align: center; margin-top: 35px;'>VS</h2>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"<h1 style='text-align: center; color: #1f77b4;'>{p_v}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center;'><div class='handicap-box'>{'+'+str(abs(round(diff, 1))) if diff > 0 else '-'+str(abs(round(diff, 1)))}</div></div>", unsafe_allow_html=True)

        # --- TABLA DE CUARTOS ---
        st.write("---")
        st.write("### 📈 Puntos Aproximados por Periodo")
        dist = [0.265, 0.235, 0.260, 0.240]
        ql = [round(sl * d, 1) for d in dist]
        qv = [round(sv * d, 1) for d in dist]
        df_cuartos = pd.DataFrame({
            "Equipo": [l_data['nickname'], v_data['nickname']],
            "1er Q": [ql[0], qv[0]], "2do Q": [ql[1], qv[1]], "3er Q": [ql[2], qv[2]], "4to Q": [ql[3], qv[3]], "Total": [round(sum(ql), 1), round(sum(qv), 1)]
        })
        st.table(df_cuartos)

        st.success(f"📍 Marcador Final: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")