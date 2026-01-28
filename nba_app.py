import streamlit as st
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# Intentar importar librería de Standings para L10 Automático
try:
    from nba_api.stats.endpoints import leaguestandings
    NBA_API_AVAILABLE = True
except:
    NBA_API_AVAILABLE = False

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI PRO V8.9", layout="wide", page_icon="🏀")

# --- 2. BASE DE DATOS DE ESTADÍSTICAS ---
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

# --- NUEVO: ADN COMPLETO DE LOS 30 EQUIPOS (Distribución Q1, Q2, Q3, Q4) ---
# Suma aprox 1.0. Esto evita que los cuartos se vean iguales.
TEAM_QUARTER_DNA = {
    "Celtics": [0.27, 0.26, 0.24, 0.23], "Thunder": [0.26, 0.26, 0.25, 0.23],
    "Nuggets": [0.25, 0.25, 0.26, 0.24], "76ers": [0.26, 0.25, 0.24, 0.25],
    "Cavaliers": [0.26, 0.26, 0.24, 0.24], "Lakers": [0.24, 0.25, 0.24, 0.27],
    "Warriors": [0.23, 0.24, 0.30, 0.23], "Knicks": [0.25, 0.25, 0.26, 0.24],
    "Mavericks": [0.24, 0.24, 0.25, 0.27], "Bucks": [0.24, 0.25, 0.23, 0.28],
    "Timberwolves": [0.25, 0.26, 0.24, 0.25], "Suns": [0.25, 0.25, 0.25, 0.25],
    "Pacers": [0.28, 0.27, 0.24, 0.21], "Kings": [0.27, 0.26, 0.24, 0.23],
    "Heat": [0.23, 0.24, 0.25, 0.28], "Magic": [0.24, 0.25, 0.26, 0.25],
    "Clippers": [0.25, 0.25, 0.25, 0.25], "Rockets": [0.24, 0.24, 0.26, 0.26],
    "Pelicans": [0.25, 0.26, 0.24, 0.25], "Hawks": [0.27, 0.26, 0.24, 0.23],
    "Grizzlies": [0.24, 0.24, 0.25, 0.27], "Bulls": [0.25, 0.24, 0.24, 0.27],
    "Nets": [0.24, 0.24, 0.24, 0.28], "Raptors": [0.25, 0.25, 0.25, 0.25],
    "Jazz": [0.23, 0.24, 0.26, 0.27], "Spurs": [0.24, 0.24, 0.25, 0.27],
    "Hornets": [0.26, 0.24, 0.24, 0.26], "Pistons": [0.24, 0.24, 0.24, 0.28],
    "Wizards": [0.26, 0.25, 0.23, 0.26], "Trail Blazers": [0.24, 0.24, 0.25, 0.27]
}

STARS_DB = {
    "tatum": [22.5, 18.5, 29.5], "jokic": [31.5, 25.0, 32.1], "doncic": [28.1, 23.5, 35.8], 
    "james": [23.0, 19.0, 28.5], "curry": [24.5, 20.0, 30.2], "embiid": [30.2, 24.5, 34.0], 
    "antetokounmpo": [29.8, 24.0, 32.5], "davis": [25.0, 20.5, 26.8], "durant": [24.0, 21.0, 29.0],
    "booker": [21.5, 18.5, 28.0], "gilgeous": [27.5, 22.0, 31.5], "brunson": [21.5, 17.5, 30.5],
    "wembanayama": [22.0, 18.0, 28.5], "maxey": [21.0, 17.0, 26.5], "fox": [22.0, 18.0, 29.0]
}

# --- 3. FUNCIONES DE DATOS ---
@st.cache_data(ttl=3600)
def get_l10_stats():
    """Obtiene el récord L10 de la API oficial"""
    try:
        standings = leaguestandings.LeagueStandings(season='2024-25').get_dict()
        data = standings['resultSets'][0]['rowSet']
        l10_map = {}
        headers = standings['resultSets'][0]['headers']
        idx_name, idx_l10 = headers.index('TeamName'), headers.index('L10')
        for row in data:
            l10_map[row[idx_name]] = row[idx_l10]
        return l10_map
    except: return {}

def calculate_inertia(l10_record):
    if not l10_record: return 0.0, "Neutral"
    try:
        wins = int(l10_record.split('-')[0])
        if wins >= 7: return 0.025, "🔥 Caliente"
        elif wins <= 3: return -0.025, "❄️ Frío"
        else: return 0.0, "Neutral"
    except: return 0.0, "Neutral"

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
    bajas = injuries_db.get(team_nick.lower(), [])
    penalizacion = 0.0
    detected_stars = []
    for player in bajas:
        for star, stats in STARS_DB.items():
            if star in player.lower():
                impacto_p = (stats[0]/200) + (stats[1]/200) + (stats[2]/600)
                penalizacion += impacto_p
                detected_stars.append(f"{player} (USG%: {stats[2]})")
    return min(0.26, penalizacion), detected_stars

def get_history():
    try:
        conn = sqlite3.connect('nba_data.db')
        df = pd.read_sql_query("SELECT fecha, partido, pred_total FROM historial ORDER BY id DESC LIMIT 5", conn)
        conn.close(); return df
    except: return pd.DataFrame(columns=["Fecha", "Partido", "Pred"])

# --- 4. SIDEBAR ---
inj_db = get_espn_injuries()
l10_data = get_l10_stats()

with st.sidebar:
    st.header("⚙️ SISTEMA V8.9 PRO")
    if st.button("🔄 ACTUALIZAR TODO"):
        st.cache_data.clear(); st.rerun()
    
    st.subheader("🦓 FACTOR ARBITRAL")
    ref_trend = st.selectbox("Tendencia Jueces", ["Neutral", "Over (Muchas Faltas)", "Under (Dejan Jugar)"])
    
    st.divider()
    st.subheader("💰 LÍNEAS CASINO")
    linea_ou = st.number_input("Over/Under", value=220.0, step=0.5)
    linea_spread = st.number_input("Hándicap Local", value=-4.5, step=0.5)
    
    st.subheader("🔋 FACTOR B2B")
    b2b_l = st.toggle("Local en B2B", key="b2bl")
    b2b_v = st.toggle("Visita en B2B (+Castigo)", key="b2bv")
    
    st.subheader("📍 LISTA LESIONADOS")
    for t_nick_disp in sorted(ADVANCED_STATS.keys()):
        bajas_sidebar = inj_db.get(t_nick_disp.lower(), [])
        if bajas_sidebar:
            with st.expander(f"📍 {t_nick_disp.upper()}"):
                for p in bajas_sidebar: st.write(f"• {p}")

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V8.9: FULL QUARTER DNA")

with st.expander("🔍 VER REPORTE DE LESIONADOS EN TIEMPO REAL (ESPN)"):
    cols = st.columns(3)
    for i, (team, players) in enumerate(inj_db.items()):
        cols[i % 3].markdown(f"**{team.upper()}**")
        for p in players: cols[i % 3].caption(f"❌ {p}")

c1, c2 = st.columns(2)

with c1:
    l_nick = st.selectbox("LOCAL", sorted(ADVANCED_STATS.keys()), index=5)
    rec_l = l10_data.get(l_nick, l10_data.get(l_nick.split()[-1], None))
    bonus_l10_l, status_l = calculate_inertia(rec_l)
    st.markdown(f"### {l_nick} | {status_l} ({rec_l if rec_l else 'N/A'})")
    
    penal_auto_l, estrellas_l = perform_auto_detection(l_nick, inj_db)
    if estrellas_l: st.error(f"⚠️ BAJAS CLAVE: {', '.join(estrellas_l)}")
    else: st.success("✅ Plantilla OK")
    venganza_l = st.checkbox("🔥 Venganza", key="vl")

with c2:
    v_nick = st.selectbox("VISITANTE", sorted(ADVANCED_STATS.keys()), index=23)
    rec_v = l10_data.get(v_nick, l10_data.get(v_nick.split()[-1], None))
    bonus_l10_v, status_v = calculate_inertia(rec_v)
    st.markdown(f"### {v_nick} | {status_v} ({rec_v if rec_v else 'N/A'})")

    penal_auto_v, estrellas_v = perform_auto_detection(v_nick, inj_db)
    if estrellas_v: st.error(f"⚠️ BAJAS CLAVE: {', '.join(estrellas_v)}")
    else: st.success("✅ Plantilla OK")
    venganza_v = st.checkbox("🔥 Venganza", key="vv")

# --- 6. MOTOR DE CÁLCULO ---
if st.button("🚀 CALCULAR PICK (ADN + PALIZA)"):
    s_l, s_v = ADVANCED_STATS[l_nick], ADVANCED_STATS[v_nick]
    alt_bonus = 1.02 if l_nick in ["Nuggets", "Jazz"] else 1.0
    if abs(s_l[4] - s_v[4]) > 0.07: st.warning("⚠️ ALERTA: Choque de Ritmos")

    penal_b2b_l = 0.035 if b2b_l else 0
    penal_b2b_v = 0.042 if b2b_v else 0 
    
    ref_factor = 1.03 if "Over" in ref_trend else (0.97 if "Under" in ref_trend else 1.0)
    ritmo_p = ((s_l[4] + s_v[4])/2) * (0.97 if (b2b_l or b2b_v) else 1.0) * ref_factor
    
    pot_l = (((s_l[0] * (1 - penal_auto_l - penal_b2b_l + bonus_l10_l + (0.03 if venganza_l else 0))) * 0.7) + (s_v[1] * 0.3)) * ritmo_p * alt_bonus
    pot_v = (((s_v[0] * (1 - penal_auto_v - penal_b2b_v + bonus_l10_v + (0.03 if venganza_v else 0))) * 0.7) + (s_l[1] * 0.3)) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    
    # --- DISTRIBUCIÓN POR ADN REAL ---
    # Ahora usamos el diccionario completo, por lo que nunca usará el fallback de 0.25
    dna_l = TEAM_QUARTER_DNA.get(l_nick, [0.25, 0.25, 0.25, 0.25])
    dna_v = TEAM_QUARTER_DNA.get(v_nick, [0.25, 0.25, 0.25, 0.25])
    
    q1_l, q2_l, q3_l = [res_l * p for p in dna_l[:3]]
    q1_v, q2_v, q3_v = [res_v * p for p in dna_v[:3]]
    
    cum_l_q3 = q1_l + q2_l + q3_l
    cum_v_q3 = q1_v + q2_v + q3_v
    diff_q3 = cum_l_q3 - cum_v_q3
    
    # Factor Paliza (Blowout)
    q4_l = res_l * dna_l[3]
    q4_v = res_v * dna_v[3]
    
    blowout_msg = ""
    if abs(diff_q3) > 15:
        blowout_msg = "🚨 DETECCIÓN DE PALIZA (GARBAGE TIME): Puntos reducidos en Q4"
        if diff_q3 > 0: # Local gana
            q4_l *= 0.85
            q4_v *= 0.95
        else: # Visita gana
            q4_v *= 0.85
            q4_l *= 0.95
            
    final_l = q1_l + q2_l + q3_l + q4_l
    final_v = q1_v + q2_v + q3_v + q4_v
    total_ia = round(final_l + final_v, 1)
    diff_final = final_l - final_v
    wp_l = 1 / (1 + (10 ** (-diff_final / 15)))

    # --- RESULTADOS ---
    st.divider()
    if blowout_msg: st.info(blowout_msg)
    
    rc1, rc2 = st.columns([2, 1])
    with rc1:
        st.header(f"📊 {l_nick} {round(final_l,1)} - {round(final_v,1)} {v_nick}")
        st.progress(wp_l, text=f"Probabilidad {l_nick}: {round(wp_l*100, 1)}%")
        
    with rc2:
        st.metric("TOTAL IA", total_ia, delta=f"{round(total_ia - linea_ou, 1)} vs Casino")
        st.metric("SPREAD IA", round(-diff_final, 1), delta=f"{round((-diff_final) - linea_spread, 1)} Valor")

    st.table(pd.DataFrame({
        "Periodo": ["Q1", "Q2", "Q3", "Q4", "FINAL"],
        l_nick: [round(x,1) for x in [q1_l, q2_l, q3_l, q4_l, final_l]],
        v_nick: [round(x,1) for x in [q1_v, q2_v, q3_v, q4_v, final_v]]
    }))