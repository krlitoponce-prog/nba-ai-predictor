import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# Intentamos importar librerías de NBA
try:
    from nba_api.stats.static import teams
    from nba_api.stats.endpoints import leaguedashplayerstats
    NBA_API_AVAILABLE = True
except:
    NBA_API_AVAILABLE = False

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V8.0", layout="wide", page_icon="🏀")

# --- 2. BASE DE DATOS ADN NBA (30 Equipos) ---
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

# --- EXTENSIÓN DE MÉTRICAS DE ESTRELLAS (Métricas Reales PER, GS) ---
STARS_METRICS = {
    "tatum": [22.5, 18.5], "brown": [19.0, 16.0], "jokic": [31.5, 25.0], 
    "doncic": [28.1, 23.5], "james": [23.0, 19.0], "curry": [24.5, 20.0], 
    "embiid": [30.2, 24.5], "antetokounmpo": [29.8, 24.0], "davis": [25.0, 20.5], 
    "brunson": [21.5, 17.5], "gilgeous-alexander": [27.5, 22.0], "edwards": [20.5, 16.5], 
    "wembanayama": [21.0, 17.0], "haliburton": [23.5, 20.0], "mitchell": [21.5, 18.0],
    "morant": [22.0, 18.5], "adebayo": [20.0, 17.5], "butler": [21.0, 18.0],
    "banchero": [18.5, 15.5], "sabonis": [22.5, 19.5], "fox": [21.0, 17.5],
    "durant": [24.0, 21.0], "booker": [21.5, 18.5], "leonard": [23.0, 19.5],
    "irving": [21.0, 18.0], "lillard": [20.5, 18.5], "young": [21.0, 19.0],
    "williamson": [22.0, 18.0], "markkanen": [20.0, 17.0], "maxey": [21.0, 17.5],
    "george": [19.5, 16.0], "siakam": [19.0, 15.5], "derozan": [20.0, 17.0]
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

def auto_analyze_injuries(team_nick, injuries_db):
    bajas = injuries_db.get(team_nick.lower(), [])
    impacto_total, gtd_detectado = 0.0, False
    for p in bajas:
        p_low = p.lower()
        for s, metrics in STARS_METRICS.items():
            if s in p_low: impacto_total += (metrics[0]/200) + (metrics[1]/200)
        if any(x in p_low for x in ["cuestionable", "duda", "questionable"]): gtd_detectado = True
    return min(0.25, impacto_total), gtd_detectado

def save_to_history(partido, pred_total):
    try:
        conn = sqlite3.connect('nba_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO historial (fecha, partido, pred_total, real_total) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), partido, pred_total, 0))
        conn.commit(); conn.close()
    except: pass

def get_history():
    try:
        conn = sqlite3.connect('nba_data.db')
        df = pd.read_sql_query("SELECT fecha, partido, pred_total FROM historial ORDER BY id DESC LIMIT 5", conn)
        conn.close(); return df
    except: return pd.DataFrame(columns=["Fecha", "Partido", "Pred"])

# --- 4. SIDEBAR ---
inj_db = get_espn_injuries()
try:
    all_nba_teams = teams.get_teams()
except:
    all_nba_teams = [{"full_name": k, "nickname": k} for k in ADVANCED_STATS.keys()]

with st.sidebar:
    st.header("⚙️ SISTEMA V8.0")
    if st.button("🔄 LIMPIAR CACHÉ Y BUSCAR DATOS FRESCOS"):
        st.cache_data.clear(); st.success("Datos actualizados de ESPN/NBA"); st.rerun()
    
    st.write("---")
    st.subheader("🔋 Fatiga y Giras")
    b2b_l = st.toggle("Local B2B")
    reg_l = st.toggle("🔙 Regreso a Casa")
    viaje_v = st.toggle("✈️ Viaje Largo (Visita)")
    
    st.subheader("📜 HISTORIAL RECIENTE")
    st.dataframe(get_history(), use_container_width=True)

# --- 5. INTERFAZ EQUIPOS ---
st.title("🏀 NBA AI PRO V8.0: PROPORTIONAL IMPACT & QUARTER AVERAGES")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next((t['nickname'] for t in all_nba_teams if t['full_name'] == l_name), l_name)
    s_l = ADVANCED_STATS.get(l_nick, [115, 115, 1.0, 3.5, 1.0])
    
    st.markdown(f"### Ajustes {l_nick}")
    penal_auto_l, gtd_auto_l = auto_analyze_injuries(l_nick, inj_db)
    m_l = st.checkbox("🚨 Baja Estrella (Auto)", value=(penal_auto_l > 0), key="ml")
    l_pg = st.checkbox("Falta Base (PG)", key="lpg")
    l_c = st.checkbox("Falta Pívot (C)", key="lc")
    venganza_l = st.checkbox("🔥 Venganza", key="vl")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next((t['nickname'] for t in all_nba_teams if t['full_name'] == v_name), v_name)
    s_v = ADVANCED_STATS.get(v_nick, [112, 115, 1.0, 3.5, 1.0])

    st.markdown(f"### Ajustes {v_nick}")
    penal_auto_v, gtd_auto_v = auto_analyze_injuries(v_nick, inj_db)
    m_v = st.checkbox("🚨 Baja Estrella (Auto)", value=(penal_auto_v > 0), key="mv")
    v_pg = st.checkbox("Falta Base (PG)", key="vpg")
    v_c = st.checkbox("Falta Pívot (C)", key="vc")
    venganza_v = st.checkbox("🔥 Venganza", key="vv")

# --- 6. MOTOR DE CÁLCULO V8.0 ---
if st.button("🚀 LANZAR ANÁLISIS"):
    # Penalizaciones Proporcionales (Límite 25% para casos críticos)
    red_l = (penal_auto_l if m_l else 0) + (0.02 if l_pg else 0)
    red_v = (penal_auto_v if m_v else 0) + (0.02 if v_pg else 0)
    
    ritmo_adj = (-0.02 if l_pg else 0) + (-0.02 if v_pg else 0)
    f_l = 0.045 if reg_l else (0.035 if b2b_l else 0)
    f_v = 0.045 if viaje_v else 0
    
    ritmo_p = ((s_l[4] + s_v[4])/2 + ritmo_adj) * (0.98 if (b2b_l or b2b_v) else 1.0)
    
    # Potencial (Cualquier bono/penalización se suma aquí)
    pot_l = (((s_l[0] * (1 - red_l - f_l + (0.03 if venganza_l else 0))) * 0.7) + (s_v[1] * (0.33 if l_c else 0.3))) * ritmo_p
    pot_v = (((s_v[0] * (1 - red_v - f_v + (0.03 if venganza_v else 0))) * 0.7) + (s_l[1] * (0.33 if v_c else 0.3))) * ritmo_p
    
    res_l, res_v = round(pot_l + s_l[3], 1), round(pot_v, 1)
    
    # Win Probability (Sigmoide)
    diff = res_l - res_v
    wp_l = 1 / (1 + (10 ** (-diff / 15)))
    
    # Guardado automático e Historial
    st.session_state.analisis = {"l": l_nick, "v": v_nick, "rl": res_l, "rv": res_v, "total": round(res_l+res_v,1), "wp": wp_l}
    save_to_history(f"{l_nick} vs {v_nick}", res_l+res_v)

# --- 7. RESULTADOS ---
if 'analisis' in st.session_state:
    res = st.session_state.analisis
    st.divider()
    col_out1, col_out2 = st.columns([2, 1])
    
    with col_out1:
        st.header(f"📊 {res['l']} {res['rl']} - {res['rv']} {res['v']}")
        st.progress(res['wp'], text=f"Probabilidad Victoria {res['l']}: {round(res['wp']*100, 1)}%")
        
        fig, ax = plt.subplots(figsize=(8, 3.5))
        dists = [0.26, 0.52, 0.76, 1.0]
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [res['rl']*d for d in dists], marker='o', label=res['l'], color='green')
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [res['rv']*d for d in dists], marker='s', label=res['v'], color='blue')
        ax.set_title("Progresión Acumulada de Puntos"); ax.legend(); st.pyplot(fig)

    with col_out2:
        st.metric("Total Proyectado", res['total'])
        
        # Tabla de cuartos con PROMEDIO (PROM/Q)
        dist = [0.26, 0.26, 0.24, 0.24]
        df_qs = pd.DataFrame({
            "Periodo": ["Q1", "Q2", "Q3", "Q4", "PROM/Q"],
            res['l']: [round(res['rl']*dist[0],1), round(res['rl']*dist[1],1), round(res['rl']*dist[2],1), round(res['rl']*dist[3],1), round(res['rl']/4,1)],
            res['v']: [round(res['rv']*dist[0],1), round(res['rv']*dist[1],1), round(res['rv']*dist[2],1), round(res['rv']*dist[3],1), round(res['rv']/4,1)]
        })
        st.table(df_qs)

    # --- 8. MONITOR EN VIVO ---
    st.write("---")
    st.subheader("⏱️ MONITOR DE DESVIACIÓN EN VIVO")
    lx1, lx2, lx3 = st.columns(3)
    live_l = lx1.number_input(f"Puntos en vivo {res['l']}", value=0, key="live_l")
    live_v = lx2.number_input(f"Puntos en vivo {res['v']}", value=0, key="live_v")
    tiempo_live = lx3.selectbox("Tiempo Transcurrido", ["Inicio", "Final Q1", "Medio Tiempo (Q2)", "Final Q3"], key="t_live")
    
    if live_l > 0 or live_v > 0:
        f_m = {"Inicio": 4.0, "Final Q1": 4.0, "Medio Tiempo (Q2)": 2, "Final Q3": 1.33}
        tend = (live_l + live_v) * f_m[tiempo_live]
        st.write(f"**Tendencia Proyectada:** {round(tend, 1)} pts | **Desviación:** {round(tend - res['total'], 1)}")