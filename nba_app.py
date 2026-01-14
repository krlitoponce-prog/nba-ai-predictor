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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NBA AI Analyst Pro V4.1", layout="wide", page_icon="🏀")

# --- SISTEMA DE PERSISTENCIA (CARRITO DE REFERENCIAS) ---
HISTORIAL_FILE = "historial_nba.csv"

def guardar_en_historial(datos):
    if os.path.exists(HISTORIAL_FILE):
        df = pd.read_csv(HISTORIAL_FILE)
    else:
        df = pd.DataFrame(columns=["Fecha", "Equipos", "H_IA", "Prob"])
    df = pd.concat([pd.DataFrame([datos]), df], ignore_index=True).head(5)
    df.to_csv(HISTORIAL_FILE, index=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        return pd.read_csv(HISTORIAL_FILE)
    return None

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .valormaximo {
        background-color: #ff0000; color: white; padding: 20px;
        border-radius: 15px; border: 5px solid #fff;
        font-weight: bold; text-align: center; font-size: 1.5rem;
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

# --- RANKING DE PODER ---
TEAM_POWER = {
    "Celtics": 120.5, "Thunder": 120.0, "Nuggets": 119.5, "Timberwolves": 118.0,
    "Mavericks": 118.0, "Bucks": 116.5, "Knicks": 117.0, "Suns": 116.0,
    "Pacers": 117.5, "Lakers": 114.5, "Warriors": 114.0, "Cavaliers": 116.0,
    "76ers": 115.0, "Heat": 114.5, "Kings": 114.0
}

# --- FUNCIONES DE APOYO ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    hist = cargar_historial()
    if hist is not None:
        st.table(hist)
    if st.button("Limpiar Historial"):
        if os.path.exists(HISTORIAL_FILE): os.remove(HISTORIAL_FILE)
        st.rerun()

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
    with st.spinner('Analizando datos...'):
        inj_db = get_injuries()
        b_l, b_v = inj_db.get(l_data['nickname'].lower(), []), inj_db.get(v_data['nickname'].lower(), [])
        b2b_l, b2b_v = check_b2b(l_data['id']), check_b2b(v_data['id'])

        sl = TEAM_POWER.get(l_data['nickname'], 113.0) + 4.0 - (len(b_l) * 2.5) - (4 if b2b_l else 0)
        sv = TEAM_POWER.get(v_data['nickname'], 111.0) - (len(b_v) * 2.5) - (4 if b2b_v else 0)

        diff = sl - sv
        h_ia = round(-diff, 1) if diff > 0 else round(abs(diff), 1)
        prob_l = round((1 / (1 + math.exp(-0.065 * diff))) * 100, 1)

        # GUARDAR EN HISTORIAL (CARRITO)
        guardar_en_historial({
            "Fecha": datetime.now().strftime("%H:%M"),
            "Equipos": f"{l_data['nickname']} vs {v_data['nickname']}",
            "H_IA": h_ia,
            "Prob": f"{prob_l}%"
        })

        # --- MOSTRAR RESULTADOS ---
        st.write("---")
        brecha = abs(h_ia - cuota_casa)
        
        if brecha >= 6.0:
            st.markdown(f'<div class="valormaximo">🚨 ¡VALOR MÁXIMO DETECTADO! 🚨<br>Diferencia de {brecha} puntos</div>', unsafe_allow_html=True)
        elif h_ia < cuota_casa:
            st.success(f"✅ VALOR MODERADO: La IA proyecta hándicap de {h_ia}.")
        else:
            st.warning(f"⚠️ RIESGO: La casa ofrece {cuota_casa}, la IA proyecta {h_ia}.")

        st.info(f"📍 Marcador Final Proyectado: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")
        
        st.write("### 📈 Puntos Aproximados por Periodo")
        dist = [0.265, 0.235, 0.260, 0.240]
        ql, qv = [round(sl * d, 1) for d in dist], [round(sv * d, 1) for d in dist]
        st.table(pd.DataFrame({"Equipo": [l_data['nickname'], v_data['nickname']], "Q1": [ql[0], qv[0]], "Q2": [ql[1], qv[1]], "Q3": [ql[2], qv[2]], "Q4": [ql[3], qv[3]], "Total": [round(sum(ql),1), round(sum(qv),1)]}))
        
        # NOTA: Eliminamos st.rerun() de aquí para que los resultados no se borren.
        # El historial se actualizará la próxima vez que interactúes o si refrescas manualmente.