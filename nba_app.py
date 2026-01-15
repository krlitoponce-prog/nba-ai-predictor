import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V5.4", layout="wide", page_icon="🏀")

# --- 2. EL PITÓN: MOTOR DE RATINGS (30 EQUIPOS) ---
# [Offensive_Rating, Defensive_Rating, Clutch_Factor]
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.12], "Thunder": [118.5, 111.0, 1.08], "Nuggets": [119.0, 112.5, 1.18],
    "Timberwolves": [114.0, 108.5, 0.94], "Mavericks": [117.5, 115.0, 1.10], "Bucks": [116.0, 116.5, 0.90],
    "Knicks": [117.2, 112.1, 1.04], "76ers": [115.5, 113.0, 1.01], "Cavaliers": [116.8, 110.5, 1.05],
    "Suns": [117.0, 115.8, 0.98], "Pacers": [120.1, 119.5, 0.96], "Kings": [116.2, 115.0, 1.03],
    "Lakers": [115.0, 114.8, 1.06], "Pelicans": [114.5, 113.2, 0.88], "Warriors": [116.5, 115.5, 1.02],
    "Magic": [110.5, 109.8, 0.95], "Heat": [113.2, 111.5, 1.07], "Rockets": [112.8, 112.0, 0.99],
    "Hawks": [118.0, 120.5, 0.94], "Bulls": [113.8, 115.5, 1.04], "Jazz": [115.2, 119.0, 0.97],
    "Nets": [112.0, 116.0, 0.95], "Raptors": [112.5, 117.8, 0.92], "Grizzlies": [111.5, 113.0, 1.00],
    "Spurs": [110.0, 115.5, 1.05], "Hornets": [109.5, 118.2, 0.91], "Pistons": [108.2, 117.5, 0.89],
    "Trail Blazers": [109.0, 116.5, 0.93], "Wizards": [111.2, 119.8, 0.90], "Clippers": [115.8, 113.5, 1.02]
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "williamson", "ingram", "mccollum", "butler", "adebayo", "george", "leonard", "fox", "sabonis", "brunson", "mitchell", "siakam", "barnes", "markkanen", "lavine", "derozan", "bridges"]

if 'analisis_activo' not in st.session_state:
    st.session_state.analisis_activo = False

def get_all_context():
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

# --- 3. SIDEBAR (CONTROL DE FATIGA Y CARRITO) ---
inj_db = get_all_context()
with st.sidebar:
    st.header("⚙️ Panel de Control")
    st.subheader("🔋 Estado Físico (B2B)")
    b2b_l = st.toggle("¿LOCAL jugó ayer?")
    b2b_v = st.toggle("¿VISITANTE jugó ayer?")
    
    st.write("---")
    st.header("📂 Carrito de Referencias")
    if inj_db:
        for equipo, lista in inj_db.items():
            with st.expander(f"📍 {equipo.upper()}"):
                for p in lista:
                    impacto = "🔴 ESTRELLA" if any(s in p.lower() for s in STARS) else "🟡 ROL"
                    st.write(f"**{p}** ({impacto})")
    
    if st.button("🔄 ACTUALIZAR TODO"):
        st.rerun()

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO: TERMINAL V5.4")
all_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in all_teams])

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("EQUIPO LOCAL", team_names, index=0)
    l_data = next(t for t in all_teams if t['full_name'] == l_name)
with c2:
    v_name = st.selectbox("EQUIPO VISITANTE", team_names, index=1)
    v_data = next(t for t in all_teams if t['full_name'] == v_name)

if st.button("🔥 GENERAR HÁNDICAP ELITE"):
    st.session_state.analisis_activo = True

# --- 5. LÓGICA DE PRECISIÓN MEJORADA ---
if st.session_state.analisis_activo:
    with st.container():
        st.write("---")
        stats_l = list(ADVANCED_STATS.get(l_data['nickname'], [112.0, 114.0, 1.0]))
        stats_v = list(ADVANCED_STATS.get(v_data['nickname'], [111.0, 115.0, 1.0]))

        # Ajuste por Bajas y Estrellas
        inj_l = inj_db.get(l_data['nickname'].lower(), [])
        inj_v = inj_db.get(v_data['nickname'].lower(), [])
        
        # Penalización acumulativa
        penalty_l = 3.5 if b2b_l else 0
        penalty_v = 3.5 if b2b_v else 0

        for p in inj_l:
            if any(s in p.lower() for s in STARS):
                stats_l[0] -= 6.5 # Baja el ataque si falta la estrella
                stats_l[2] -= 0.10 # El cierre empeora mucho
                penalty_l += 4.0
            else: penalty_l += 1.2

        for p in inj_v:
            if any(s in p.lower() for s in STARS):
                stats_v[0] -= 6.5
                stats_v[2] -= 0.10
                penalty_v += 4.0
            else: penalty_v += 1.2

        # CÁLCULO DE FUERZA (Ajuste de localía +4.5)
        fuerza_l = (stats_l[0] + stats_v[1]) / 2 + 4.5 - penalty_l
        fuerza_v = (stats_v[0] + stats_l[1]) / 2 - penalty_v

        # Aplicación de Factor Clutch
        final_l, final_v = fuerza_l * stats_l[2], fuerza_v * stats_v[2]
        h_ideal = round(-(final_l - final_v), 1)

        # MOSTRAR RESULTADOS
        st.subheader(f"📍 Proyección IA: {l_data['nickname']} {round(final_l,1)} - {round(final_v,1)} {v_data['nickname']}")
        
        st.info(f"🎯 Hándicap IA sugerido: **{h_ideal}**")
        
        if abs(h_ideal) > 15:
            st.warning("⚠️ ALERTA: Diferencia extrema. Verifica si el equipo mermado está alineando suplentes de la G-League.")

        # Desglose Visual
        st.table(pd.DataFrame({
            "Métrica": ["Fuerza Bruta", "Ajuste Clutch", "Puntos Proyectados"],
            l_data['nickname']: [round(fuerza_l,1), f"x{stats_l[2]}", round(final_l,1)],
            v_data['nickname']: [round(fuerza_v,1), f"x{stats_v[2]}", round(final_v,1)]
        }))