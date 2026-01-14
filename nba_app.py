import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime, timedelta
import math
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI Live Analyst V4.5", layout="wide", page_icon="🏀")

# --- LISTA DE ESTRELLAS (MERMA DESEQUILIBRANTE) ---
STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "siakam", "durant", "booker", "brunson", "mitchell", "sabo", "towns", "gobert", "wembanyama", "holmgren"]

# --- RANKING DE PODER (BASE) ---
TEAM_POWER = {
    "Celtics": 120.5, "Thunder": 120.0, "Nuggets": 119.5, "Timberwolves": 118.0,
    "Mavericks": 118.0, "Bucks": 114.5, "Knicks": 117.0, "Suns": 116.0,
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

def get_live_data():
    try:
        sb = scoreboardv2.ScoreboardV2()
        return sb.get_data_frames()[1] # LineScore (contiene puntos actuales)
    except: return None

# --- SIDEBAR (CARRITO DE REFERENCIAS: LESIONADOS) ---
inj_db = get_injuries()
with st.sidebar:
    st.header("📂 Carrito de Referencias")
    st.markdown("### 🚑 Reporte de Impacto")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    es_estrella = any(s in p.lower() for s in STARS)
                    impacto = "🔴 DESEQUILIBRANTE (-4.0)" if es_estrella else "🟡 REEMPLAZABLE (-1.5)"
                    st.write(f"**{p}**")
                    st.caption(impacto)
    else:
        st.write("No hay lesiones críticas reportadas.")
    
    st.write("---")
    if st.button("🔄 REFRESCAR MARCADORES LIVE"):
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
    with st.spinner('Sincronizando con la NBA en vivo...'):
        # 1. Calcular mermas por lesiones
        def calcular_merma(equipo_nickname):
            lista = inj_db.get(equipo_nickname.lower(), [])
            return sum([4.0 if any(s in p.lower() for s in STARS) else 1.5 for p in lista])

        merma_l = calcular_merma(l_data['nickname'])
        merma_v = calcular_merma(v_data['nickname'])

        # 2. Obtener puntos en vivo si existen
        live_df = get_live_data()
        pts_l, pts_v = 0, 0
        is_live = False
        
        if live_df is not None and not live_df.empty:
            match_l = live_df[live_df['TEAM_ID'] == l_data['id']]
            match_v = live_df[live_df['TEAM_ID'] == v_data['id']]
            if not match_l.empty and not match_v.empty:
                pts_l = match_l.iloc[-1]['PTS']
                pts_v = match_v.iloc[-1]['PTS']
                if pts_l > 0 or pts_v > 0: is_live = True

        # 3. Proyección Lógica
        # Si el partido es en vivo, la proyección es (Puntos actuales + Proyección restante ajustada)
        base_l = TEAM_POWER.get(l_data['nickname'], 112.0) + 4.0 - merma_l
        base_v = TEAM_POWER.get(v_data['nickname'], 110.0) - merma_v

        if is_live:
            # Estimamos cuánto falta basándonos en el marcador real (ajustamos tendencia)
            sl = (pts_l * 1.8) if pts_l > 60 else (pts_l + (base_l / 2))
            sv = (pts_v * 1.8) if pts_v > 60 else (pts_v + (base_v / 2))
            status_msg = f"🚨 PARTIDO EN VIVO: Marcador Actual {pts_l} - {pts_v}"
        else:
            sl, sv = base_l, base_v
            status_msg = "📅 PROYECCIÓN PRE-PARTIDO"

        diff = sl - sv
        h_ia = round(-diff, 1)

        # --- RESULTADOS ---
        st.write("---")
        st.subheader(status_msg)
        
        brecha = abs(h_ia - cuota_casa)
        if brecha >= 6.0:
            st.markdown(f'<div style="background-color:red; color:white; padding:20px; border-radius:10px; text-align:center; font-weight:bold; animation: blinker 1s linear infinite;">🚨 VALOR MÁXIMO DETECTADO: DIFERENCIA DE {brecha} PTS</div>', unsafe_allow_html=True)

        st.info(f"📍 Marcador Final Estimado: {l_data['nickname']} {round(sl,1)} - {round(sv,1)} {v_data['nickname']}")
        
        # Sugerencia
        pick = l_data['nickname'] if h_ia < cuota_casa else v_data['nickname']
        st.success(f"💡 Sugerencia de Apuesta: **{pick} Hándicap {h_ia if pick == l_data['nickname'] else abs(h_ia)}**")

        # Tabla por Cuartos
        dist = [0.265, 0.235, 0.260, 0.240]
        ql, qv = [round(sl * d, 1) for d in dist], [round(sv * d, 1) for d in dist]
        st.table(pd.DataFrame({
            "Equipo": [l_data['nickname'], v_data['nickname']],
            "Q1": [ql[0], qv[0]], "Q2": [ql[1], qv[1]], "Q3": [ql[2], qv[2]], "Q4": [ql[3], qv[3]],
            "Total Proyectado": [round(sum(ql),1), round(sum(qv),1)]
        }))