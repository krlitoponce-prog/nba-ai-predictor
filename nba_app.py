import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V7.5", layout="wide", page_icon="🚀")

# --- 2. BASE DE DATOS ADN NBA (Preservada) ---
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

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "mitchell", "brunson", "wembanayama", "morant", "adebayo", "butler", "banchero", "sabonis", "fox"]

# --- 3. FUNCIONES DE PERSISTENCIA Y SCRAPING ---
def save_to_history(partido, pred_total):
    try:
        conn = sqlite3.connect('nba_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO historial (fecha, partido, pred_total, real_total) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), partido, pred_total, 0))
        conn.commit()
        conn.close()
        st.success("✅ Predicción guardada en Historial.")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

@st.cache_data(ttl=3600)
def get_nba_lineups():
    # Estructura para scraping de nba.com/players/todays-lineups
    # Por ahora simulamos la conexión exitosa
    return {"status": "Ready to scrape NBA.com"}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración V7.5")
    
    st.subheader("🔋 Fatiga & Giras")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        b2b_l = st.toggle("Local B2B")
        regreso_l = st.toggle("🔙 Casa B2B")
    with col_f2:
        b2b_v = st.toggle("Visita B2B")
        viaje_v = st.toggle("✈️ Viaje Largo")
    
    st.subheader("🔥 Análisis de Rachas")
    racha_l = st.select_slider("Racha Local", options=["Frío", "Neutral", "Caliente"], value="Neutral")
    racha_v = st.select_slider("Racha Visita", options=["Frío", "Neutral", "Caliente"], value="Neutral")

    st.subheader("🎯 Contexto")
    contexto = st.selectbox("Importancia", ["Regular Season", "Playoff Push", "Trap Game Alerta"])

    st.divider()
    if st.button("🔄 ACTUALIZAR ALINEACIONES (NBA.com)"):
        st.cache_data.clear()
        st.info("Buscando alineaciones en NBA.com...")
        st.rerun()

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V7.5: ELITE PREDICTOR")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next(t for t in all_nba_teams if t['full_name'] == l_name)['nickname']
    s_l = ADVANCED_STATS.get(l_nick, [112, 114, 1.0, 3.5, 1.0])
    st.metric("Base Offense", s_l[0])
    
    m_l = st.checkbox(f"🚨 Baja Estrella ({l_nick})")
    l_gtd = st.checkbox("⚠️ Jugador en Duda (GTD)", key="gtd_l")
    l_pg_out = st.checkbox("Falta Base (PG)", key="l_pg")
    l_c_out = st.checkbox("Falta Pívot (C)", key="l_c")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next(t for t in all_nba_teams if t['full_name'] == v_name)['nickname']
    s_v = ADVANCED_STATS.get(v_nick, [111, 115, 1.0, 3.5, 1.0])
    st.metric("Base Offense", s_v[0])

    m_v = st.checkbox(f"🚨 Baja Estrella ({v_nick})")
    v_gtd = st.checkbox("⚠️ Jugador en Duda (GTD)", key="gtd_v")
    v_pg_out = st.checkbox("Falta Base (PG)", key="v_pg")
    v_c_out = st.checkbox("Falta Pívot (C)", key="v_c")

# --- 6. MOTOR DE CÁLCULO V7.5 ---
if st.button("🚀 INICIAR ANÁLISIS"):
    # Penalizaciones (Ajustadas con GTD)
    red_l = min(0.22, (0.08 if m_l else 0) + (0.025 if l_gtd else 0) + (0.02 if l_pg_out else 0))
    red_v = min(0.22, (0.08 if m_v else 0) + (0.025 if v_gtd else 0) + (0.02 if v_pg_out else 0))

    # Rachas y Trap Game
    bonus_racha_l = 0.02 if racha_l == "Caliente" else (-0.02 if racha_l == "Frío" else 0)
    bonus_racha_v = 0.02 if racha_v == "Caliente" else (-0.02 if racha_v == "Frío" else 0)
    trap_factor = 0.96 if contexto == "Trap Game Alerta" else 1.0

    # Potencial
    ritmo_p = ((s_l[4] + s_v[4]) / 2) * (0.98 if (b2b_l or b2b_v) else 1.0)
    pot_l = (((s_l[0] * (1 - red_l + bonus_racha_l)) * 0.7) + (s_v[1] * 0.3)) * ritmo_p * trap_factor
    pot_v = (((s_v[0] * (1 - red_v + bonus_racha_v)) * 0.7) + (s_l[1] * 0.3)) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    
    # Probabilidad de Victoria (Win Probability)
    # Basado en el Logit de la diferencia de puntos proyectada
    diff = res_l - res_v
    win_prob_l = 1 / (1 + (10 ** (-diff / 15))) # Sigmoide NBA estándar
    win_prob_v = 1 - win_prob_l

    st.session_state.analisis = {
        "res_l": res_l, "res_v": res_v, "wp_l": win_prob_l, "wp_v": win_prob_v,
        "l_nick": l_nick, "v_nick": v_nick, "total": round(res_l + res_v, 1)
    }

# --- 7. RESULTADOS ---
if st.session_state.analisis:
    a = st.session_state.analisis
    st.divider()
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader(f"📊 PROYECCIÓN: {a['l_nick']} {a['res_l']} - {a['res_v']} {a['v_nick']}")
        st.progress(a['wp_l'], text=f"Probabilidad Victoria {a['l_nick']}: {round(a['wp_l']*100, 1)}%")
    
    with col_w2:
        st.metric("Total Puntos Proyectado", a['total'])
        if st.button("💾 GUARDAR EN HISTORIAL"):
            save_to_history(f"{a['l_nick']} vs {a['v_nick']}", a['total'])

    # Monitor de Desviación (Preservado)
    st.write("---")
    st.subheader("⏱️ MONITOR DE DESVIACIÓN EN VIVO")
    lx1, lx2, lx3 = st.columns(3)
    live_l = lx1.number_input(f"Puntos {a['l_nick']}", value=0)
    live_v = lx2.number_input(f"Puntos {a['v_nick']}", value=0)
    tiempo = lx3.selectbox("Tiempo", ["Q1", "Q2", "Q3"])
    
    if live_l > 0:
        factor = 4 if tiempo == "Q1" else (2 if tiempo == "Q2" else 1.33)
        tendencia = (live_l + live_v) * factor
        st.write(f"Tendencia: {round(tendencia, 1)} pts | Desv: {round(tendencia - a['total'], 1)}")