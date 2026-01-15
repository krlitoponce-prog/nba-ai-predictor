import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V6.5", layout="wide", page_icon="🏆")

# --- 2. MOTOR DE RATINGS AMPLIADO ---
# Estructura: [Off_Rating, Def_Rating, Clutch, Home_Advantage]
ADVANCED_STATS = {
    "Celtics": [122.5, 110.2, 1.12, 4.8], "Thunder": [118.5, 111.0, 1.08, 3.8], "Nuggets": [119.0, 112.5, 1.18, 5.8],
    "76ers": [115.5, 113.0, 1.01, 3.5], "Cavaliers": [116.8, 110.5, 1.05, 3.5], "Lakers": [115.0, 114.8, 1.06, 4.2],
    "Warriors": [116.5, 115.5, 1.02, 4.5], "Knicks": [117.2, 112.1, 1.04, 4.3], "Mavericks": [117.5, 115.0, 1.10, 3.8],
    "Bucks": [116.0, 116.5, 0.90, 4.0], "Timberwolves": [114.0, 108.5, 0.94, 3.9], "Suns": [117.0, 115.8, 0.98, 3.7],
    "Pacers": [120.1, 119.5, 0.96, 3.6], "Kings": [116.2, 115.0, 1.03, 3.8], "Heat": [113.2, 111.5, 1.07, 4.1]
    # ... (Se pueden seguir añadiendo con sus localías específicas)
}

STARS = ["tatum", "brown", "curry", "james", "davis", "antetokounmpo", "lillard", "embiid", "doncic", "irving", "jokic", "gilgeous-alexander", "edwards", "haliburton", "mitchell", "brunson"]

# --- 3. EXTRACCIÓN Y SIDEBAR (CARRITO PERMANENTE) ---
@st.cache_data(ttl=600)
def get_all_context():
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
inj_db = get_all_context()

with st.sidebar:
    st.header("⚙️ Ajustes de Energía")
    b2b_l = st.toggle("Local en Back-to-Back")
    b2b_v = st.toggle("Visita en Back-to-Back")
    st.write("---")
    st.header("📂 Carrito Permanente")
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
            else: st.write("✅ Plantilla Completa")
    if st.button("🔄 ACTUALIZAR"): st.rerun()

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V6.5: ULTIMATE ENGINE")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_data = next(t for t in all_nba_teams if t['full_name'] == l_name)
    s_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0, 3.5])
    m_l = st.checkbox(f"🚨 BAJA ESTRELLA ({l_data['nickname']})")
    st.metric(f"Factor Clutch {l_data['nickname']}", f"x{s_l[2]}", delta="Localía: +"+str(s_l[3]))

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_data = next(t for t in all_nba_teams if t['full_name'] == v_name)
    s_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0, 3.5])
    m_v = st.checkbox(f"🚨 BAJA ESTRELLA ({v_data['nickname']})")
    st.metric(f"Factor Clutch {v_data['nickname']}", f"x{s_v[2]}", delta="Visitante: +0.0")

if st.button("🚀 INICIAR ANÁLISIS TOTAL"):
    # Penalizaciones
    red_l = 0.08 if m_l else 0
    if not m_l:
        for p in inj_db.get(l_data['nickname'].lower(), []):
            red_l += 0.045 if any(s in p.lower() for s in STARS) else 0.015
    
    red_v = 0.08 if m_v else 0
    if not m_v:
        for p in inj_db.get(v_data['nickname'].lower(), []):
            red_v += 0.045 if any(s in p.lower() for s in STARS) else 0.015

    red_l, red_v = min(red_l, 0.15), min(red_v, 0.15)
    f_c_l = 0.975 if b2b_l else 1.0
    f_c_v = 0.975 if b2b_v else 1.0

    # CÁLCULO DE FUERZA (Con Localía Dinámica s_l[3])
    f_l = (((s_l[0] * (1-red_l)) + s_v[1]) / 2 + s_l[3]) * f_c_l
    f_v = (((s_v[0] * (1-red_v)) + s_l[1]) / 2) * f_c_v
    
    res_l, res_v = round(f_l * s_l[2], 1), round(f_v * s_v[2], 1)
    h_final = round(-(res_l - res_v), 1)
    puntos_totales = round(res_l + res_v, 1)

    # VISUALIZACIÓN DE RESULTADOS
    st.divider()
    
    # 1. Gráfico de Proyección
    st.subheader("📊 Comparativa de Poder")
    st.bar_chart(pd.DataFrame({"Equipo": [l_data['nickname'], v_data['nickname']], "Puntaje Proyectado": [res_l, res_v]}).set_index("Equipo"))

    # 2. Semáforo y Hándicap
    if abs(h_final) > 9:
        st.success(f"💎 GRAN VENTAJA: {l_data['nickname']} vs {v_data['nickname']} | Hándicap Sugerido: {h_final}")
    else:
        st.info(f"⚖️ LÍNEA AJUSTADA: Hándicap Sugerido: {h_final}")
    
    st.warning(f"🏀 TOTAL DE PUNTOS PROYECTADO (O/U): {puntos_totales}")

    # 3. Tabla de Cuartos (Q1-Q4)
    q_l, q_v = res_l/4, res_v/4
    qs = {
        "Periodo": ["Q1", "Q2", "Q3", "Q4 (Clutch)", "TOTAL"],
        l_data['nickname']: [round(q_l,1), round(q_l,1), round(q_l*0.95,1), round(q_l*s_l[2],1), res_l],
        v_data['nickname']: [round(q_v,1), round(q_v,1), round(q_v*0.95,1), round(q_v*s_v[2],1), res_v]
    }
    st.table(pd.DataFrame(qs))