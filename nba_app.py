import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V7.4", layout="wide", page_icon="🚀")

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

# --- 3. EXTRACCIÓN DE LESIONES ---
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

# --- 4. SIDEBAR: FATIGA Y CONTEXTO ---
with st.sidebar:
    st.header("⚙️ Configuración V7.4")
    
    st.subheader("🔋 Fatiga & Giras")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        b2b_l = st.toggle("Local B2B")
        regreso_l = st.toggle("🔙 Casa B2B")
        gira_l = st.toggle("🏠 Estancia Local")
    with col_f2:
        b2b_v = st.toggle("Visita B2B")
        viaje_v = st.toggle("✈️ Viaje Largo")
    
    st.subheader("🎯 Contexto de Liga")
    contexto = st.selectbox("Importancia del Partido", 
                            ["Regular Season", "Duelo Directo / Playoff Push", "Último de Gira (Agotamiento)"])

    st.divider()
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    st.write(f"{'🔴' if any(s in p.lower() for s in STARS) else '🟡'} {p}")
            else: st.write("✅ Plantilla Completa")

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V7.4: BALANCED ANALYTICS")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next(t for t in all_nba_teams if t['full_name'] == l_name)['nickname']
    s_l = ADVANCED_STATS.get(l_nick, [112, 114, 1.0, 3.5, 1.0])
    st.metric("Base Offense", s_l[0], f"+{s_l[3]} Home")
    
    st.markdown("---")
    m_l = st.checkbox(f"🚨 Baja Estrella ({l_nick})")
    l_pg_out = st.checkbox("Falta Base (PG)", key="l_pg")
    l_c_out = st.checkbox("Falta Pívot (C)", key="l_c")
    venganza_l = st.checkbox("🔥 Venganza (Local)", key="rev_l")
    humillacion_l = st.checkbox("🛡️ Recuperación Paliza (Local)", key="blow_l")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next(t for t in all_nba_teams if t['full_name'] == v_name)['nickname']
    s_v = ADVANCED_STATS.get(v_nick, [111, 115, 1.0, 3.5, 1.0])
    st.metric("Base Offense", s_v[0], "Visitor")

    st.markdown("---")
    m_v = st.checkbox(f"🚨 Baja Estrella ({v_nick})")
    v_pg_out = st.checkbox("Falta Base (PG)", key="v_pg")
    v_c_out = st.checkbox("Falta Pívot (C)", key="v_c")
    venganza_v = st.checkbox("🔥 Venganza (Visita)", key="rev_v")
    humillacion_v = st.checkbox("🛡️ Recuperación Paliza (Visita)", key="blow_v")

# --- 6. MOTOR DE CÁLCULO ---
if 'analisis' not in st.session_state: st.session_state.analisis = None

if st.button("🚀 INICIAR ANÁLISIS"):
    # Penalizaciones Lesiones (Límite aumentado a 0.22 para casos críticos)
    red_l = min(0.22, (0.08 if m_l else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(l_nick.lower(), [])))
    red_v = min(0.22, (0.08 if m_v else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(v_nick.lower(), [])))

    # Factores Alineación
    ritmo_adj = (-0.02 if l_pg_out else 0) + (-0.02 if v_pg_out else 0)
    def_adj_l = 0.025 if l_c_out else 0 
    def_adj_v = 0.025 if v_c_out else 0 

    # Motivación (Ajustada a 3%)
    bonus_rev_l = 0.03 if venganza_l else 0.0
    bonus_rev_v = 0.03 if venganza_v else 0.0
    
    # Intensidad Defensiva (Ajustada a 5%)
    def_rev_l = 0.05 if humillacion_l else 0.0
    def_rev_v = 0.05 if humillacion_v else 0.0

    # Contexto & Fatiga (Preservados)
    fat_gira_v = -0.035 if "Gira" in contexto else 0.0
    playoff_intensidad = 0.97 if "Playoff" in contexto else 1.0 
    f_l = 0.045 if regreso_l else (0.035 if b2b_l else 0.0)
    f_v = 0.045 if viaje_v else (0.035 if b2b_v else 0.0)
    b_gira_l = 0.015 if gira_l else 0.0
    
    alt_bonus = 1.012 if l_nick in ["Nuggets", "Jazz"] else 1.0
    ritmo_p = (((s_l[4] + s_v[4]) / 2) + ritmo_adj) * (0.98 if (b2b_l or b2b_v or regreso_l) else 1.0) * playoff_intensidad
    
    # Potencial Final
    pot_l = (((s_l[0] * (1 - (red_l + f_l) + bonus_rev_l + b_gira_l)) * 0.7) + (s_v[1] * (0.33 + def_adj_v) if (b2b_v or viaje_v) else s_v[1] * (0.3 + def_adj_v))) * ritmo_p * alt_bonus * (1 - def_rev_v)
    pot_v = (((s_v[0] * (1 - (red_v + f_v + fat_gira_v) + bonus_rev_v)) * 0.7) + (s_l[1] * (0.33 + def_adj_l) if (b2b_l or regreso_l) else s_l[1] * (0.3 + def_adj_l))) * ritmo_p * (1 - def_rev_l)
    
    res_l, res_v = round((pot_l + s_l[3]) * s_l[2], 1), round(pot_v * s_v[2], 1)
    
    # Cuartos
    dist = [0.26, 0.26, 0.24, 0.24]
    q_l, q_v = [res_l * d for d in dist], [res_v * d for d in dist]
    
    if abs(res_l - res_v) < 5:
        q_l[3] *= 0.95; q_v[3] *= 0.95
        res_l, res_v = round(sum(q_l), 1), round(sum(q_v), 1)

    st.session_state.analisis = {
        "res_l": res_l, "res_v": res_v, "total": round(res_l + res_v, 1),
        "l_nick": l_nick, "v_nick": v_nick, "q_l": q_l, "q_v": q_v, "ritmo": ritmo_p
    }

# --- 7. RESULTADOS Y MONITOR ---
if st.session_state.analisis:
    a = st.session_state.analisis
    st.divider()
    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        st.subheader(f"📊 PROYECCIÓN: {a['l_nick']} {a['res_l']} - {a['res_v']} {a['v_nick']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Hándicap", round(-(a['res_l'] - a['res_v']), 1))
        m2.metric("Total Puntos", a['total'])
        m3.metric("Ritmo", f"{round(a['ritmo'], 2)}x")
        
        # Gráfico
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [sum(a['q_l'][:i+1]) for i in range(4)], marker='o', label=a['l_nick'], color='#1D428A')
        ax.plot(["Q1", "Q2", "Q3", "Q4"], [sum(a['q_v'][:i+1]) for i in range(4)], marker='s', label=a['v_nick'], color='#CE1141')
        ax.set_title("Progresión Acumulada")
        ax.legend(); st.pyplot(fig)

    with col_res2:
        st.table(pd.DataFrame({"Q": ["Q1","Q2","Q3","Q4","Total"], 
                               a['l_nick']: [round(x,1) for x in a['q_l']] + [a['res_l']], 
                               a['v_nick']: [round(x,1) for x in a['q_v']] + [a['res_v']]}))

    # --- MONITOR DE DESVIACIÓN EN VIVO ---
    st.write("---")
    st.subheader("⏱️ MONITOR DE DESVIACIÓN EN VIVO")
    lx1, lx2, lx3 = st.columns(3)
    live_l = lx1.number_input(f"Puntos en vivo {a['l_nick']}", value=0)
    live_v = lx2.number_input(f"Puntos en vivo {a['v_nick']}", value=0)
    tiempo_trans = lx3.selectbox("Tiempo Transcurrido", ["Inicio", "Final Q1", "Medio Tiempo (Q2)", "Final Q3"])
    
    if live_l > 0 or live_v > 0:
        # Factores de proyección según tiempo
        f_tiempos = {"Inicio": 4.0, "Final Q1": 4.0, "Medio Tiempo (Q2)": 2.0, "Final Q3": 1.33}
        factor = f_tiempos[tiempo_trans]
        p_final_total = (live_l + live_v) * factor
        desv = round(p_final_total - a['total'], 1)
        
        st.write(f"**Tendencia Proyectada:** {round(p_final_total, 1)} pts")
        if desv > 8: st.error(f"🔥 DESVIACIÓN ALTA (OVER): +{desv}")
        elif desv < -8: st.success(f"❄️ DESVIACIÓN ALTA (UNDER): {desv}")
        else: st.info(f"✅ En línea con la proyección: {desv}")