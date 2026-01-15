import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V6.0", layout="wide", page_icon="📈")

# --- 2. MOTOR DE RATINGS ---
# [Off_Rating, Def_Rating, Clutch_Factor, Home_Advantage]
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.12, 4.5], "Thunder": [118.5, 111.0, 1.08, 3.5], "Nuggets": [119.0, 112.5, 1.18, 5.5],
    "76ers": [115.5, 113.0, 1.01, 3.5], "Cavaliers": [116.8, 110.5, 1.05, 3.5], "Lakers": [115.0, 114.8, 1.06, 4.0],
    "Warriors": [116.5, 115.5, 1.02, 4.2], "Knicks": [117.2, 112.1, 1.04, 4.0] # Agregados ejemplos de localía fuerte
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "mitchell", "brunson"]

# --- 3. EXTRACCIÓN Y SIDEBAR ---
@st.cache_data(ttl=600)
def get_injuries():
    try:
        url = "https://espndeportes.espn.com/basquetbol/nba/lesiones"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        injuries = {}
        for title in soup.find_all('div', class_='Table__Title'):
            team_raw = title.text.strip().lower()
            team_key = "76ers" if "76ers" in team_raw else team_raw.split()[-1]
            rows = title.find_parent('div', class_='ResponsiveTable').find_all('tr', class_='Table__TR')
            injuries[team_key] = [r.find_all('td')[0].text.strip() for r in rows[1:]]
        return injuries
    except: return {}

all_nba_teams = teams.get_teams()
inj_db = get_injuries()

with st.sidebar:
    st.header("📂 Carrito Permanente")
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
            else: st.write("✅ Plantilla OK")

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V6.0: VISUAL INTELLIGENCE")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_data = next(t for t in all_nba_teams if t['full_name'] == l_name)
    s_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0, 3.5])
    m_l = st.checkbox(f"🚨 BAJA ESTRELLA ({l_data['nickname']})")
    st.metric("Poder Ofensivo", f"{s_l[0]} pts", help="Puntos promedio proyectados")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_data = next(t for t in all_nba_teams if t['full_name'] == v_name)
    s_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0, 3.5])
    m_v = st.checkbox(f"🚨 BAJA ESTRELLA ({v_data['nickname']})")
    st.metric("Poder Ofensivo", f"{s_v[0]} pts")

if st.button("🔥 EJECUTAR PROYECCIÓN V6.0"):
    # Lógica de cálculo (Mejorada con Localía Dinámica)
    red_l = 0.08 if m_l else 0
    red_v = 0.08 if m_v else 0
    
    f_l = (((s_l[0] * (1-red_l)) + s_v[1]) / 2 + s_l[3]) # s_l[3] es la localía dinámica
    f_v = (((s_v[0] * (1-red_v)) + s_l[1]) / 2)
    
    res_l, res_v = f_l * s_l[2], f_v * s_v[2]
    handicap = round(-(res_l - res_v), 1)

    # Gráfico Comparativo
    st.bar_chart(pd.DataFrame({
        "Equipo": [l_data['nickname'], v_data['nickname']],
        "Proyección Final": [res_l, res_v]
    }).set_index("Equipo"))

    # Semáforo de Valor
    if abs(handicap) > 10:
        st.success(f"💎 GRAN VALOR DETECTADO: Hándicap Sugerido {handicap}")
    elif abs(handicap) > 5:
        st.warning(f"⚠️ VALOR MODERADO: Hándicap Sugerido {handicap}")
    else:
        st.info(f"⚖️ PARTIDO EQUILIBRADO: Hándicap Sugerido {handicap}")

    # Tabla de Cuartos (Sin borrar nada)
    q_l, q_v = res_l/4, res_v/4
    qs = {"Cuarto": ["Q1", "Q2", "Q3", "Q4", "FINAL"],
          l_data['nickname']: [round(q_l,1)]*4 + [round(res_l,1)],
          v_data['nickname']: [round(q_v,1)]*4 + [round(res_v,1)]}
    st.table(pd.DataFrame(qs))