import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V8.3", layout="wide", page_icon="🏀")

# --- 2. BASE DE DATOS ADN NBA (Estadísticas Base) ---
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

# --- DICCIONARIO GLOBAL DE ESTRELLAS (Métricas PER, GS) ---
STARS_DB = {
    "tatum": [22.5, 18.5], "brown": [19.0, 16.0], "jokic": [31.5, 25.0], "doncic": [28.1, 23.5], 
    "james": [23.0, 19.0], "curry": [24.5, 20.0], "embiid": [30.2, 24.5], "antetokounmpo": [29.8, 24.0],
    "davis": [25.0, 20.5], "durant": [24.0, 21.0], "booker": [21.5, 18.5], "leonard": [23.0, 19.5],
    "gilgeous": [27.5, 22.0], "lillard": [21.0, 18.0], "brunson": [21.5, 17.5], "edwards": [20.5, 16.5],
    "haliburton": [23.0, 19.0], "mitchell": [21.5, 18.0], "morant": [22.5, 18.0], "adebayo": [20.0, 17.0],
    "butler": [21.5, 18.0], "banchero": [19.0, 15.5], "sabonis": [22.0, 19.0], "fox": [21.0, 17.5],
    "wembanayama": [22.0, 18.0], "williamson": [22.0, 17.5], "markkanen": [20.5, 17.0], "maxey": [21.0, 17.5],
    "george": [20.0, 16.5], "siakam": [19.5, 16.0], "derozan": [20.0, 17.0], "irving": [21.5, 18.0]
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

def perform_auto_detection(team_nick, injuries_db):
    bajas_equipo = injuries_db.get(team_nick.lower(), [])
    penalizacion = 0.0
    detected_stars = []
    for player in bajas_equipo:
        for star, stats in STARS_DB.items():
            if star in player.lower():
                penalizacion += (stats[0]/200) + (stats[1]/200)
                detected_stars.append(player)
    return min(0.25, penalizacion), detected_stars

def get_history():
    try:
        conn = sqlite3.connect('nba_data.db')
        df = pd.read_sql_query("SELECT fecha, partido, pred_total FROM historial ORDER BY id DESC LIMIT 5", conn)
        conn.close(); return df
    except: return pd.DataFrame(columns=["Fecha", "Partido", "Pred"])

# --- 4. SIDEBAR ---
inj_db = get_espn_injuries()
with st.sidebar:
    st.header("⚙️ SISTEMA V8.3")
    if st.button("🔄 ACTUALIZAR DATOS FRESCOS"):
        st.cache_data.clear(); st.rerun()
    
    st.write("---")
    st.subheader("💰 LÍNEAS CASINO")
    linea_ou = st.number_input("Over/Under", value=220.0, step=0.5)
    linea_spread = st.number_input("Hándicap Local", value=0.0, step=0.5)

    st.write("---")
    st.subheader("🔋 Fatiga")
    b2b_l, reg_l = st.toggle("Local B2B", key="b2bl"), st.toggle("🔙 Regreso Casa", key="regl")
    b2b_v, viaje_v = st.toggle("Visita B2B", key="b2bv"), st.toggle("✈️ Viaje Largo", key="viajev")
    
    st.write("---")
    st.subheader("📜 ÚLTIMOS GUARDADOS")
    st.table(get_history())

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V8.3: ADVANCED ANALYTICS")
c1, c2 = st.columns(2)

with c1:
    l_nick = st.selectbox("LOCAL", sorted(ADVANCED_STATS.keys()), index=5)
    st.markdown(f"### Ajustes {l_nick}")
    
    # REPORTE DE BAJAS VISIBLE DEBAJO DE CADA EQUIPO
    penal_auto_l, estrellas_l = perform_auto_detection(l_nick, inj_db)
    if estrellas_l:
        st.error(f"⚠️ BAJAS CLAVE DETECTADAS: {', '.join(estrellas_l)}")
    else:
        st.success("✅ Estrellas disponibles")
        
    l_pg = st.checkbox("Falta Base (PG)", key="lpg")
    l_c = st.checkbox("Falta Pívot (C)", key="lc")
    venganza_l = st.checkbox("🔥 Venganza", key="vl")
    paliza_l = st.checkbox("🛡️ Viene de Paliza", key="pl")

with c2:
    v_nick = st.selectbox("VISITANTE", sorted(ADVANCED_STATS.keys()), index=23)
    st.markdown(f"### Ajustes {v_nick}")
    
    # REPORTE DE BAJAS VISIBLE DEBAJO DE CADA EQUIPO
    penal_auto_v, estrellas_v = perform_auto_detection(v_nick, inj_db)
    if estrellas_v:
        st.error(f"⚠️ BAJAS CLAVE DETECTADAS: {', '.join(estrellas_v)}")
    else:
        st.success("✅ Estrellas disponibles")

    v_pg = st.checkbox("Falta Base (PG)", key="vpg")
    v_c = st.checkbox("Falta Pívot (C)", key="vc")
    venganza_v = st.checkbox("🔥 Venganza", key="vv")
    paliza_v = st.checkbox("🛡️ Viene de Paliza", key="pv")

# --- 6. MOTOR DE CÁLCULO ---
if st.button("🚀 INICIAR ANÁLISIS"):
    alt_bonus = 1.015 if l_nick in ["Nuggets", "Jazz"] else 1.0
    s_l, s_v = ADVANCED_STATS[l_nick], ADVANCED_STATS[v_nick]
    
    if abs(s_l[4] - s_v[4]) > 0.06: st.warning("⚠️ ALERTA: Conflicto de Ritmos (Over/Under Inestable).")

    red_l = penal_auto_l + (0.02 if l_pg else 0)
    red_v = penal_auto_v + (0.02 if v_pg else 0)

    f_l = 0.045 if reg_l else (0.035 if b2b_l else 0)
    f_v = 0.045 if viaje_v else (0.035 if b2b_v else 0)
    
    ritmo_p = ((s_l[4] + s_v[4])/2) * (0.98 if (b2b_l or b2b_v) else 1.0)
    
    pot_l = (((s_l[0] * (1 - red_l - f_l + (0.03 if venganza_l else 0))) * 0.7) + (s_v[1] * (0.33 if l_c else 0.3))) * ritmo_p * alt_bonus
    pot_v = (((s_v[0] * (1 - red_v - f_v + (0.03 if venganza_v else 0))) * 0.7) + (s_l[1] * (0.33 if v_c else 0.3))) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3] * (0.95 if paliza_v else 1.0), 1), round(pot_v * (0.95 if paliza_l else 1.0), 1)
    
    wp_l = 1 / (1 + (10 ** (-(res_l - res_v) / 15)))
    
    st.session_state.analisis = {"l": l_nick, "v": v_nick, "rl": res_l, "rv": res_v, "total": round(res_l+res_v, 1), "wp": wp_l, "diff": res_l - res_v}

# --- 7. RESULTADOS ---
if 'analisis' in st.session_state:
    res = st.session_state.analisis
    st.divider()
    col_out1, col_out2 = st.columns([2, 1])
    with col_out1:
        st.header(f"📊 {res['l']} {res['rl']} - {res['rv']} {res['v']}")
        st.progress(res['wp'], text=f"Fuerza {res['l']}: {round(res['wp']*100, 1)}%")
        
    with col_out2:
        st.metric("Total IA", res['total'], delta=f"{round(res['total'] - linea_ou, 1)} vs Casino")
        st.metric("Hándicap", round(-res['diff'], 1), delta=f"{round((-res['diff']) - linea_spread, 1)} vs Casino")

    # Tabla de Cuartos con PROMEDIO
    dist = [0.26, 0.26, 0.24, 0.24]
    st.table(pd.DataFrame({
        "Periodo": ["Q1", "Q2", "Q3", "Q4", "PROM/Q"],
        res['l']: [round(res['rl']*d, 1) for d in dist] + [round(res['rl']/4, 1)],
        res['v']: [round(res['rv']*d, 1) for d in dist] + [round(res['rv']/4, 1)]
    }))