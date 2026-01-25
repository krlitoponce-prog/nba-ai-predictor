import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2, leaguedashplayerstats

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V7.8", layout="wide", page_icon="🏀")

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

# --- 3. FUNCIONES DE DATOS ---
def save_to_history(partido, pred_total, handicap, wp):
    try:
        conn = sqlite3.connect('nba_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO historial (fecha, partido, pred_total, real_total) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), f"{partido} (H:{handicap} W:{int(wp*100)}%)", pred_total, 0))
        conn.commit()
        conn.close()
        st.success("✅ Guardado en historial")
    except Exception as e: st.error(f"Error DB: {e}")

def get_history():
    try:
        conn = sqlite3.connect('nba_data.db')
        df = pd.read_sql_query("SELECT fecha, partido, pred_total FROM historial ORDER BY id DESC LIMIT 5", conn)
        conn.close()
        return df
    except: return pd.DataFrame()

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

def auto_detect_star_out(team_nick, injuries_db):
    bajas = injuries_db.get(team_nick.lower(), [])
    return any(any(s in p.lower() for s in STARS) for p in bajas)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración V7.8")
    
    if st.button("🔄 ACTUALIZAR DATOS (LIVE)"): 
        st.cache_data.clear()
        st.rerun()
    
    st.write("---")
    st.subheader("🔋 Fatiga & Contexto")
    b2b_l, regreso_l = st.toggle("Local B2B"), st.toggle("🔙 Regreso Casa B2B")
    b2b_v, viaje_v = st.toggle("Visita B2B"), st.toggle("✈️ Viaje Largo")
    contexto = st.selectbox("Importancia", ["Regular Season", "Playoff Push", "⚠️ Trap Game Alerta"])
    
    st.subheader("🔥 Rachas Recientes")
    r_l = st.select_slider("Racha Local", ["Frío", "Neutral", "Caliente"], "Neutral")
    r_v = st.select_slider("Racha Visita", ["Frío", "Neutral", "Caliente"], "Neutral")

    st.divider()
    st.subheader("📜 ÚLTIMOS GUARDADOS")
    st.table(get_history())

# --- 5. INTERFAZ: EQUIPOS ---
all_nba_teams = teams.get_teams()
inj_db = get_espn_injuries()

st.title("🏀 NBA AI PRO V7.8: PRO ANALYTICS")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next(t for t in all_nba_teams if t['full_name'] == l_name)['nickname']
    s_l = ADVANCED_STATS.get(l_nick, [112, 114, 1.0, 3.5, 1.0])
    
    st.markdown(f"### Ajustes {l_nick}")
    auto_l = auto_detect_star_out(l_nick, inj_db)
    m_l = st.checkbox("🚨 Baja Estrella", value=auto_l, key="star_l")
    
    with st.expander("📈 Métricas de Impacto (Estrella)"):
        l_per = st.number_input("PER del jugador", 10.0, 35.0, 22.0, key="per_l")
        l_ts = st.slider("True Shooting %", 40, 70, 58, key="ts_l")
        l_gs = st.number_input("Game Score Promedio", 5.0, 40.0, 18.0, key="gs_l")
    
    l_gtd = st.checkbox("⚠️ En Duda (GTD)", key="gtd_l")
    l_pg_out = st.checkbox("Falta Base (PG)", key="l_pg")
    l_c_out = st.checkbox("Falta Pívot (C)", key="l_c")
    venganza_l = st.checkbox("🔥 Venganza", key="rev_l")
    humillacion_l = st.checkbox("🛡️ Viene de Paliza", key="blow_l")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next(t for t in all_nba_teams if t['full_name'] == v_name)['nickname']
    s_v = ADVANCED_STATS.get(v_nick, [111, 115, 1.0, 3.5, 1.0])

    st.markdown(f"### Ajustes {v_nick}")
    auto_v = auto_detect_star_out(v_nick, inj_db)
    m_v = st.checkbox("🚨 Baja Estrella", value=auto_v, key="star_v")
    
    with st.expander("📈 Métricas de Impacto (Estrella)"):
        v_per = st.number_input("PER del jugador", 10.0, 35.0, 22.0, key="per_v")
        v_ts = st.slider("True Shooting %", 40, 70, 58, key="ts_v")
        v_gs = st.number_input("Game Score Promedio", 5.0, 40.0, 18.0, key="gs_v")

    v_gtd = st.checkbox("⚠️ En Duda (GTD)", key="gtd_v")
    v_pg_out = st.checkbox("Falta Base (PG)", key="v_pg")
    v_c_out = st.checkbox("Falta Pívot (C)", key="v_c")
    venganza_v = st.checkbox("🔥 Venganza", key="rev_v")
    humillacion_v = st.checkbox("🛡️ Viene de Paliza", key="blow_v")

# --- 6. MOTOR DE CÁLCULO V7.8 ---
if st.button("🚀 LANZAR PROYECCIÓN"):
    # Cálculo Dinámico de Penalización Estrella (Basado en PER/Game Score)
    # Una estrella promedio (PER 20, GS 15) resta 8%. Una superestrella (PER 30, GS 25) resta hasta 14%.
    penal_star_l = (l_per/200) + (l_gs/200) if m_l else 0
    penal_star_v = (v_per/200) + (v_gs/200) if m_v else 0

    red_l = min(0.25, penal_star_l + (0.025 if l_gtd else 0) + (0.02 if l_pg_out else 0))
    red_v = min(0.25, penal_star_v + (0.025 if v_gtd else 0) + (0.02 if v_pg_out else 0))

    # Factores adicionales
    ritmo_adj = (-0.02 if l_pg_out else 0) + (-0.02 if v_pg_out else 0)
    def_adj_l, def_adj_v = (0.03 if l_c_out else 0), (0.03 if v_c_out else 0)
    b_rev_l, b_rev_v = (0.03 if venganza_l else 0), (0.03 if venganza_v else 0)
    b_racha_l = 0.02 if r_l == "Caliente" else (-0.02 if r_l == "Frío" else 0)
    b_racha_v = 0.02 if r_v == "Caliente" else (-0.02 if r_v == "Frío" else 0)
    d_rev_l, d_rev_v = (0.05 if humillacion_l else 0), (0.05 if humillacion_v else 0)
    trap = 0.95 if contexto == "⚠️ Trap Game Alerta" else 1.0

    # Fatiga y Ritmo
    f_l = 0.045 if regreso_l else (0.035 if b2b_l else 0.0)
    f_v = 0.045 if viaje_v else (0.035 if b2b_v else 0.0)
    ritmo_p = (((s_l[4] + s_v[4]) / 2) + ritmo_adj) * (0.98 if (b2b_l or b2b_v or regreso_l) else 1.0)
    
    # Proyección Final
    pot_l = (((s_l[0] * (1 - (red_l + f_l) + b_rev_l + b_racha_l)) * 0.7) + (s_v[1] * (0.33 + def_adj_v))) * ritmo_p * trap
    pot_v = (((s_v[0] * (1 - (red_v + f_v) + b_rev_v + b_racha_v)) * 0.7) + (s_l[1] * (0.33 + def_adj_l))) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    wp_l = 1 / (1 + (10 ** (-(res_l - res_v) / 18))) # Sensibilidad ajustada

    st.session_state.analisis = {
        "res_l": res_l, "res_v": res_v, "l_nick": l_nick, "v_nick": v_nick,
        "wp_l": wp_l, "total": round(res_l + res_v, 1), "ritmo": ritmo_p, "h": round(-(res_l - res_v), 1)
    }

# --- 7. RESULTADOS Y GRÁFICO ---
if 'analisis' in st.session_state:
    a = st.session_state.analisis
    st.divider()
    c_out1, c_out2 = st.columns([2, 1])
    
    with c_out1:
        st.subheader(f"📊 {a['l_nick']} {a['res_l']} - {a['res_v']} {a['v_nick']}")
        st.progress(a['wp_l'], text=f"Probabilidad Victoria {a['l_nick']}: {round(a['wp_l']*100, 1)}%")
        
        fig, ax = plt.subplots(figsize=(8, 3.5))
        dists = [0.26, 0.52, 0.76, 1.0]
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [a['res_l']*d for d in dists], marker='o', label=a['l_nick'], color='green')
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [a['res_v']*d for d in dists], marker='s', label=a['v_nick'], color='blue')
        ax.set_title("Progresión Proyectada del Partido")
        ax.legend(); st.pyplot(fig)

    with c_out2:
        if st.button("💾 GUARDAR ESTA PREDICCIÓN"):
            save_to_history(f"{a['l_nick']} vs {a['v_nick']}", a['total'], a['h'], a['wp_l'])
        
        st.table(pd.DataFrame({
            "Periodo": ["Q1","Q2","Q3","Q4"],
            a['l_nick']: [round(a['res_l']*0.26,1), round(a['res_l']*0.26,1), round(a['res_l']*0.24,1), round(a['res_l']*0.24,1)],
            a['v_nick']: [round(a['res_v']*0.26,1), round(a['res_v']*0.26,1), round(a['res_v']*0.24,1), round(a['res_v']*0.24,1)]
        }))