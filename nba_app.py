import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI PRO V8.6", layout="wide", page_icon="🚀")

# --- 2. BASE DE DATOS ADN NBA (Actualizada) ---
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

def get_total_lineup_impact(team_nick, injuries_db):
    bajas = injuries_db.get(team_nick.lower(), [])
    penalizacion = 0.0
    detected_players = []
    for player in bajas:
        is_star = False
        detected_players.append(player)
        for star, stats in STARS_DB.items():
            if star in player.lower():
                impacto_p = (stats[0]/200) + (stats[1]/200) + (stats[2]/600)
                penalizacion += impacto_p
                is_star = True
        if not is_star:
            penalizacion += 0.015 # Penalización base por jugador de rotación (Sensibilidad Total)
    return min(0.30, penalizacion), detected_players

# --- 4. SIDEBAR ---
inj_db = get_espn_injuries()
with st.sidebar:
    st.header("⚙️ SISTEMA V8.6")
    if st.button("🔄 ACTUALIZAR DATOS FRESCOS"):
        st.cache_data.clear(); st.rerun()
    
    st.write("---")
    st.subheader("💰 CALCULADORA DE VALOR (EDGE)")
    casino_ou = st.number_input("Línea O/U Casino", value=225.0, step=0.5)
    casino_spread = st.number_input("Línea Hándicap Local", value=-3.5, step=0.5)

    st.write("---")
    st.subheader("🔋 FACTOR B2B DINÁMICO")
    b2b_l = st.toggle("Local en B2B", key="b2bl")
    b2b_v = st.toggle("Visita en B2B (Castigo +15%)", key="b2bv")
    
    st.subheader("📈 INERCIA RECIENTE (L10)")
    l10_l = st.select_slider("Inercia Local", ["Frío", "Neutral", "Caliente"], "Neutral", key="l10l")
    l10_v = st.select_slider("Inercia Visita", ["Frío", "Neutral", "Caliente"], "Neutral", key="l10v")

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V8.6: PROFESIONAL ENGINE")
c1, c2 = st.columns(2)

with c1:
    l_nick = st.selectbox("LOCAL", sorted(ADVANCED_STATS.keys()), index=5)
    st.markdown(f"### Ajustes {l_nick}")
    impact_l, list_l = get_total_lineup_impact(l_nick, inj_db)
    if list_l: st.warning(f"🚑 Bajas Detectadas ({len(list_l)}): {', '.join(list_l[:4])}...")
    else: st.success("✅ Rotación Completa")
    venganza_l = st.checkbox("🔥 Factor Venganza", key="vl")

with c2:
    v_nick = st.selectbox("VISITANTE", sorted(ADVANCED_STATS.keys()), index=23)
    st.markdown(f"### Ajustes {v_nick}")
    impact_v, list_v = get_total_lineup_impact(v_nick, inj_db)
    if list_v: st.warning(f"🚑 Bajas Detectadas ({len(list_v)}): {', '.join(list_v[:4])}...")
    else: st.success("✅ Rotación Completa")
    venganza_v = st.checkbox("🔥 Factor Venganza", key="vv")

# --- 6. PROCESAMIENTO ---
if st.button("🚀 CALCULAR PREDICCIÓN ELITE"):
    s_l, s_v = ADVANCED_STATS[l_nick], ADVANCED_STATS[v_nick]
    
    # Altitud Automática (Denver/Utah)
    alt_bonus = 1.02 if l_nick in ["Nuggets", "Jazz"] else 1.0
    
    # Alerta Duelo de Estilos
    if abs(s_l[4] - s_v[4]) > 0.07: st.error("⚔️ DUELO DE ESTILOS: Ritmos opuestos detectados. Juego impredecible.")

    # Fatiga Dinámica
    penal_b2b_l = 0.035 if b2b_l else 0
    penal_b2b_v = 0.042 if b2b_v else 0 # +15% de peso al visitante
    
    # Inercia L10
    bonus_l = 0.02 if l10_l == "Caliente" else (-0.02 if l10_l == "Frío" else 0)
    bonus_v = 0.02 if l10_v == "Caliente" else (-0.02 if l10_v == "Frío" else 0)

    ritmo_p = ((s_l[4] + s_v[4])/2) * (0.97 if (b2b_l or b2b_v) else 1.0)
    
    pot_l = (((s_l[0] * (1 - impact_l - penal_b2b_l + bonus_l + (0.03 if venganza_l else 0))) * 0.7) + (s_v[1] * 0.3)) * ritmo_p * alt_bonus
    pot_v = (((s_v[0] * (1 - impact_v - penal_b2b_v + bonus_v + (0.03 if venganza_v else 0))) * 0.7) + (s_l[1] * 0.3)) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    total_ia = round(res_l + res_v, 1)
    diff_ia = res_l - res_v

    # --- 7. DASHBOARD DE RESULTADOS ---
    st.divider()
    res_c1, res_c2 = st.columns([2, 1])
    
    with res_c1:
        st.header(f"📊 PROYECCIÓN: {l_nick} {res_l} - {res_v} {v_nick}")
        # Barra de Fuerza (Probabilidad)
        wp_l = 1 / (1 + (10 ** (-diff_ia / 15)))
        st.write(f"**Probabilidad de Victoria {l_nick}:**")
        st.progress(wp_l, text=f"{round(wp_l*100,1)}%")

    with res_c2:
        st.metric("TOTAL PROYECTADO", total_ia)
        # Lógica de EDGE
        edge_ou = round(total_ia - casino_ou, 1)
        st.metric("EDGE O/U", edge_ou, delta=f"{edge_ou} pts vs Casino", delta_color="normal")
        
        edge_sp = round((-diff_ia) - casino_spread, 1)
        st.metric("EDGE SPREAD", edge_sp, delta="Valor en Hándicap")

    # Tabla de Cuartos
    st.table(pd.DataFrame({
        "Periodo": ["Q1", "Q2", "Q3", "Q4", "PROM/Q"],
        l_nick: [round(res_l*0.26,1), round(res_l*0.26,1), round(res_l*0.24,1), round(res_l*0.24,1), round(res_l/4,1)],
        v_nick: [round(res_v*0.26,1), round(res_v*0.26,1), round(res_v*0.24,1), round(res_v*0.24,1), round(res_v/4,1)]
    }))