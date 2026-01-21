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

# --- 3. FUNCIONES DE DATOS Y SCRAPING ---
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

def save_to_history(partido, pred_total):
    try:
        conn = sqlite3.connect('nba_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO historial (fecha, partido, pred_total, real_total) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), partido, pred_total, 0))
        conn.commit()
        conn.close()
        st.success("✅ Guardado en historial")
    except Exception as e:
        st.error(f"Error DB: {e}")

all_nba_teams = teams.get_teams()
inj_db = get_injuries()

# --- 4. SIDEBAR: CONTROLES GLOBALES ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    
    # Botón Actualizador Web de Lesionados
    if st.button("🔄 ACTUALIZAR WEB (LESIONES)"): 
        st.cache_data.clear()
        st.rerun()
    
    st.write("---")
    st.subheader("🔋 Fatiga & Giras")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        b2b_l = st.toggle("Local B2B")
        regreso_l = st.toggle("🔙 Casa B2B")
        gira_l = st.toggle("🏠 Estancia Local")
    with col_f2:
        b2b_v = st.toggle("Visita B2B")
        viaje_v = st.toggle("✈️ Viaje Largo")
    
    st.subheader("🔥 Rachas de Equipo")
    racha_l = st.select_slider("Local", options=["Frío", "Neutral", "Caliente"], value="Neutral", key="r_l")
    racha_v = st.select_slider("Visita", options=["Frío", "Neutral", "Caliente"], value="Neutral", key="r_v")

    st.divider()
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    st.write(f"{'🔴' if any(s in p.lower() for s in STARS) else '🟡'} {p}")
            else: st.write("✅ Plantilla Completa")

# --- 5. INTERFAZ: EQUIPOS E INDIVIDUALES ---
st.title("🏀 NBA AI PRO V7.5: ANALYTICS")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next(t for t in all_nba_teams if t['full_name'] == l_name)['nickname']
    s_l = ADVANCED_STATS.get(l_nick, [112, 114, 1.0, 3.5, 1.0])
    
    st.markdown("### Ajustes " + l_nick)
    m_l = st.checkbox(f"🚨 Baja Estrella", key="star_l")
    l_gtd = st.checkbox("⚠️ Jugador en Duda (GTD)", key="gtd_l")
    l_pg_out = st.checkbox("Falta Base (PG)", key="l_pg")
    l_c_out = st.checkbox("Falta Pívot (C)", key="l_c")
    venganza_l = st.checkbox("🔥 Venganza", key="rev_l")
    humillacion_l = st.checkbox("🛡️ Viene de Paliza", key="blow_l")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next(t for t in all_nba_teams if t['full_name'] == v_name)['nickname']
    s_v = ADVANCED_STATS.get(v_nick, [111, 115, 1.0, 3.5, 1.0])

    st.markdown("### Ajustes " + v_nick)
    m_v = st.checkbox(f"🚨 Baja Estrella", key="star_v")
    v_gtd = st.checkbox("⚠️ Jugador en Duda (GTD)", key="gtd_v")
    v_pg_out = st.checkbox("Falta Base (PG)", key="v_pg")
    v_c_out = st.checkbox("Falta Pívot (C)", key="v_c")
    venganza_v = st.checkbox("🔥 Venganza", key="rev_v")
    humillacion_v = st.checkbox("🛡️ Viene de Paliza", key="blow_v")

# --- 6. MOTOR DE CÁLCULO ---
if 'analisis' not in st.session_state: st.session_state.analisis = None

if st.button("🚀 INICIAR ANÁLISIS"):
    # Penalizaciones (Límite 22%)
    red_l = min(0.22, (0.08 if m_l else 0) + (0.025 if l_gtd else 0) + (0.02 if l_pg_out else 0))
    red_v = min(0.22, (0.08 if m_v else 0) + (0.025 if v_gtd else 0) + (0.02 if v_pg_out else 0))

    # Factores Alineación
    ritmo_adj = (-0.02 if l_pg_out else 0) + (-0.02 if v_pg_out else 0)
    def_adj_l = 0.025 if l_c_out else 0 
    def_adj_v = 0.025 if v_c_out else 0 

    # Motivación y Rachas
    b_rev_l = 0.03 if venganza_l else 0.0
    b_rev_v = 0.03 if venganza_v else 0.0
    b_racha_l = 0.02 if racha_l == "Caliente" else (-0.02 if racha_l == "Frío" else 0)
    b_racha_v = 0.02 if racha_v == "Caliente" else (-0.02 if racha_v == "Frío" else 0)
    
    # Intensidad Defensiva (tras paliza)
    d_rev_l = 0.05 if humillacion_l else 0.0
    d_rev_v = 0.05 if humillacion_v else 0.0

    # Fatiga y Altitud
    f_l = 0.045 if regreso_l else (0.035 if b2b_l else 0.0)
    f_v = 0.045 if viaje_v else (0.035 if b2b_v else 0.0)
    alt_bonus = 1.012 if l_nick in ["Nuggets", "Jazz"] else 1.0
    ritmo_p = (((s_l[4] + s_v[4]) / 2) + ritmo_adj) * (0.98 if (b2b_l or b2b_v or regreso_l) else 1.0)
    
    # Potencial
    pot_l = (((s_l[0] * (1 - (red_l + f_l) + b_rev_l + b_racha_l)) * 0.7) + (s_v[1] * (0.33 + def_adj_v))) * ritmo_p * alt_bonus * (1 - d_rev_v)
    pot_v = (((s_v[0] * (1 - (red_v + f_v) + b_rev_v + b_racha_v)) * 0.7) + (s_l[1] * (0.33 + def_adj_l))) * ritmo_p * (1 - d_rev_l)
    
    res_l, res_v = round((pot_l + s_l[3]) * s_l[2], 1), round(pot_v * s_v[2], 1)
    
    # Win Probability
    diff = res_l - res_v
    wp_l = 1 / (1 + (10 ** (-diff / 15)))

    st.session_state.analisis = {
        "res_l": res_l, "res_v": res_v, "l_nick": l_nick, "v_nick": v_nick,
        "wp_l": wp_l, "total": round(res_l + res_v, 1), "ritmo": ritmo_p
    }

# --- 7. RESULTADOS Y GRÁFICO ---
if st.session_state.analisis:
    a = st.session_state.analisis
    st.divider()
    col_out1, col_out2 = st.columns([2, 1])
    
    with col_out1:
        st.subheader(f"📊 {a['l_nick']} {a['res_l']} - {a['res_v']} {a['v_nick']}")
        st.progress(a['wp_l'], text=f"Victoria {a['l_nick']}: {round(a['wp_l']*100, 1)}%")
        
        # Gráfico de tendencia
        fig, ax = plt.subplots(figsize=(8, 3.5))
        dists = [0.26, 0.52, 0.76, 1.0]
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [a['res_l']*d for d in dists], marker='o', label=a['l_nick'], color='green')
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [a['res_v']*d for d in dists], marker='s', label=a['v_nick'], color='blue')
        ax.set_title("Progresión Proyectada")
        ax.legend(); st.pyplot(fig)

    with col_out2:
        if st.button("💾 GUARDAR"):
            save_to_history(f"{a['l_nick']} vs {a['v_nick']}", a['total'])
        
        st.table(pd.DataFrame({
            "Q": ["Q1","Q2","Q3","Q4"],
            a['l_nick']: [round(a['res_l']*0.26,1), round(a['res_l']*0.26,1), round(a['res_l']*0.24,1), round(a['res_l']*0.24,1)],
            a['v_nick']: [round(a['res_v']*0.26,1), round(a['res_v']*0.26,1), round(a['res_v']*0.24,1), round(a['res_v']*0.24,1)]
        }))

    # --- 8. MONITOR EN VIVO ---
    st.write("---")
    st.subheader("⏱️ MONITOR EN VIVO")
    lx1, lx2, lx3 = st.columns(3)
    live_l = lx1.number_input(f"Puntos {a['l_nick']}", value=0, key="live_l")
    live_v = lx2.number_input(f"Puntos {a['v_nick']}", value=0, key="live_v")
    tiempo = lx3.selectbox("Tiempo", ["Q1", "Medio Tiempo (Q2)", "Final Q3"], key="t_live")
    
    if live_l > 0:
        f_m = {"Q1": 4, "Medio Tiempo (Q2)": 2, "Final Q3": 1.33}
        tend = (live_l + live_v) * f_m[tiempo]
        desv = round(tend - a['total'], 1)
        st.write(f"**Tendencia:** {round(tend, 1)} pts | **Desviación:** {desv}")