import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import math

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI Live Analyst V4.8", layout="wide", page_icon="🏀")

# --- LISTA DE ESTRELLAS ---
STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "siakam", "durant", "booker", "brunson", "mitchell", "sabo", "towns", "gobert", "wembanyama", "holmgren"]

# --- RANKING DE PODER BASE ---
TEAM_POWER = {
    "Celtics": 120.5, "Thunder": 120.0, "Nuggets": 119.5, "Timberwolves": 118.0,
    "Mavericks": 118.0, "Bucks": 114.5, "Knicks": 117.0, "Suns": 116.0,
    "Pacers": 117.5, "Lakers": 114.5, "Warriors": 114.0, "Cavaliers": 116.0,
    "76ers": 115.0, "Heat": 114.5, "Kings": 114.0, "Pelicans": 113.5
}

# --- INICIALIZAR MEMORIA TEMPORAL ---
if 'analisis_activo' not in st.session_state:
    st.session_state.analisis_activo = False

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

def get_live_data():
    try:
        sb = scoreboardv2.ScoreboardV2()
        return sb.get_data_frames()[1]
    except: return None

# --- SIDEBAR (CARRITO DE REFERENCIAS) ---
inj_db = get_injuries()
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    st.markdown("### 🚑 Reporte de Impacto")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    impacto = "🔴 ESTRELLA (-4.0)" if any(s in p.lower() for s in STARS) else "🟡 ROL (-1.5)"
                    st.write(f"**{p}** \n {impacto}")
    
    st.write("---")
    if st.button("🔄 ACTUALIZAR MARCADORES LIVE"):
        st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO: ANALIZADOR LIVE")
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

if st.button("🔥 EJECUTAR ANÁLISIS"):
    st.session_state.analisis_activo = True

# --- LÓGICA DE VISUALIZACIÓN ---
if st.session_state.analisis_activo:
    with st.container():
        st.write("---")
        m_l = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(l_data['nickname'].lower(), [])])
        m_v = sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in inj_db.get(v_data['nickname'].lower(), [])])
        
        live_df = get_live_data()
        p_l, p_v, is_live = 0, 0, False
        
        if live_df is not None and not live_df.empty:
            m_l_live = live_df[live_df['TEAM_ID'] == l_data['id']]
            m_v_live = live_df[live_df['TEAM_ID'] == v_data['id']]
            if not m_l_live.empty and not m_v_live.empty:
                # CORRECCIÓN: Manejo de valores None o No numéricos
                val_l = m_l_live.iloc[-1]['PTS']
                val_v = m_v_live.iloc[-1]['PTS']
                p_l = int(val_l) if val_l is not None and str(val_l).isdigit() else 0
                p_v = int(val_v) if val_v is not None and str(val_v).isdigit() else 0
                if p_l > 0 or p_v > 0: is_live = True

        sl = (TEAM_POWER.get(l_data['nickname'], 112.0) + 4.0 - m_l)
        sv = (TEAM_POWER.get(v_data['nickname'], 110.0) - m_v)

        if is_live:
            sl = (p_l * 1.85) if p_l > 60 else (p_l + (sl/1.8))
            sv = (p_v * 1.85) if p_v > 60 else (p_v + (sv/1.8))
            st.subheader(f"🚨 EN VIVO: {l_data['nickname']} {p_l} - {p_v} {v_data['nickname']}")
        else:
            st.subheader("📅 PROYECCIÓN PRE-PARTIDO")

        h_ia = round(-(sl - sv), 1)
        brecha = abs(h_ia - cuota_casa)

        if brecha >= 6.0:
            st.error(f"🚨 VALOR MÁXIMO DETECTADO: DIFERENCIA DE {brecha} PTS")
        
        st.info(f"📍 Final Proyectado: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")
        st.success(f"💡 Sugerencia: **{l_data['nickname'] if h_ia < cuota_casa else v_data['nickname']} Hándicap {h_ia if h_ia < cuota_casa else abs(h_ia)}**")

        dist = [0.265, 0.235, 0.260, 0.240]
        st.table(pd.DataFrame({
            "Equipo": [l_data['nickname'], v_data['nickname']], 
            "Q1": [round(sl*dist[0],1), round(sv*dist[0],1)], 
            "Q2": [round(sl*dist[1],1), round(sv*dist[1],1)], 
            "Q3": [round(sl*dist[2],1), round(sv*dist[2],1)], 
            "Q4": [round(sl*dist[3],1), round(sv*dist[3],1)], 
            "Total": [round(sl,1), round(sv,1)]
        }))

        if st.button("❌ CERRAR Y LIMPIAR ANÁLISIS"):
            st.session_state.analisis_activo = False
            st.rerun()