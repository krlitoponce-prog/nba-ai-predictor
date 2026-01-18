import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V7.3", layout="wide", page_icon="🚀")

# --- 2. BASE DE DATOS ADN NBA (Preservada íntegramente) ---
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

# --- 3. EXTRACCIÓN Y UTILIDADES ---
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

# --- 4. SIDEBAR: FACTORES AVANZADOS ---
with st.sidebar:
    st.header("⚙️ Configuración V7.3")
    
    st.subheader("🔋 Fatiga & Giras")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        b2b_l = st.toggle("Local B2B")
        regreso_l = st.toggle("🔙 Casa B2B")
    with col_f2:
        b2b_v = st.toggle("Visita B2B")
        viaje_v = st.toggle("✈️ Viaje Largo")
    
    st.subheader("🎯 Contexto & Motivación")
    contexto = st.selectbox("Importancia del Partido", 
                            ["Regular Season", "Duelo Directo / Playoff Push", "Último de Gira (Agotamiento)"])
    venganza = st.checkbox("🔥 Revenge Game (Venganza)")
    humillacion = st.checkbox("🛡️ Blowout Recovery (Viene de paliza)")

    st.subheader("🏀 Lineup Depth (Faltas Clave)")
    c_pg, c_c = st.columns(2)
    pg_out = c_pg.checkbox("Falta Base (PG)")
    c_out = c_c.checkbox("Falta Pívot (C)")

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
st.title("🏀 NBA AI PRO V7.3: ANALYTICS ENGINE")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_nick = next(t for t in all_nba_teams if t['full_name'] == l_name)['nickname']
    s_l = ADVANCED_STATS.get(l_nick, [112, 114, 1.0, 3.5, 1.0])
    m_l = st.checkbox(f"🚨 Baja Estrella ({l_nick})")
    st.metric("Potencial Base", s_l[0], f"+{s_l[3]} Home")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_nick = next(t for t in all_nba_teams if t['full_name'] == v_name)['nickname']
    s_v = ADVANCED_STATS.get(v_nick, [111, 115, 1.0, 3.5, 1.0])
    m_v = st.checkbox(f"🚨 Baja Estrella ({v_nick})")
    st.metric("Potencial Base", s_v[0], "Visitor")

# --- 6. MOTOR DE CÁLCULO V7.3 ---
if st.button("🚀 INICIAR ANÁLISIS"):
    # 1. Lesiones & Estrellas
    red_l = min(0.15, (0.08 if m_l else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(l_nick.lower(), [])))
    red_v = min(0.15, (0.08 if m_v else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(v_nick.lower(), [])))

    # 2. Factores de Posición (PG/C)
    ritmo_adj = -0.02 if pg_out else 0.0 # Falta de Base frena el ritmo
    defensa_adj = 0.025 if c_out else 0.0 # Falta de Pívot facilita puntos rivales

    # 3. Contexto & Motivación
    bonus_revenge = 0.015 if venganza else 0.0
    bonus_defensa = 0.02 if humillacion else 0.0 # Equipo se cierra más tras paliza
    fatiga_gira = -0.035 if "Gira" in contexto else 0.0
    playoff_intensidad = 0.97 if "Playoff" in contexto else 1.0 # Menos puntos en playoffs por defensa

    # 4. Fatiga
    f_l = 0.045 if regreso_l else (0.035 if b2b_l else 0.0)
    f_v = 0.045 if viaje_v else (0.035 if b2b_v else 0.0)
    
    altitud = 1.012 if l_nick in ["Nuggets", "Jazz"] else 1.0
    ritmo_p = (((s_l[4] + s_v[4]) / 2) + ritmo_adj) * (0.98 if (b2b_l or b2b_v or regreso_l) else 1.0) * playoff_intensidad
    
    # 5. Potencial Final
    pot_l = ((((s_l[0] * (1 - (red_l + f_l) + bonus_revenge)) * 0.7) + (s_v[1] * (0.33 + defensa_adj) if b2b_v else s_v[1] * 0.3)) * ritmo_p) * altitud
    pot_v = ((((s_v[0] * (1 - (red_v + f_v + fatiga_gira))) * 0.7) + (s_l[1] * (0.33 + defensa_adj) if b2b_l else s_l[1] * 0.3)) * ritmo_p) * (1 - bonus_defensa)
    
    res_l, res_v = round((pot_l + s_l[3]) * s_l[2], 1), round(pot_v * s_v[2], 1)
    
    # 6. Progresión de Cuartos
    dist = [0.26, 0.26, 0.24, 0.24]
    q_l = [res_l * d for d in dist]
    q_v = [res_v * d for d in dist]
    
    # Ajuste Clutch
    clutch = False
    if abs(res_l - res_v) < 5:
        clutch = True
        q_l[3] *= 0.95; q_v[3] *= 0.95
        res_l, res_v = round(sum(q_l), 1), round(sum(q_v), 1)

    # --- 7. RESULTADOS VISUALES ---
    st.divider()
    col_res1, col_res2 = st.columns([2, 1])
    
    with col_res1:
        st.subheader(f"📊 PROYECCIÓN: {l_nick} {res_l} - {res_v} {v_nick}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Hándicap Sugerido", round(-(res_l - res_v), 1))
        m2.metric("Total Puntos (O/U)", round(res_l + res_v, 1))
        m3.metric("Ritmo Combinado", f"{round(ritmo_p, 2)}x")
        
        # Gráfico de Tendencia
        fig, ax = plt.subplots(figsize=(8, 4))
        ac_l = [sum(q_l[:i+1]) for i in range(4)]
        ac_v = [sum(q_v[:i+1]) for i in range(4)]
        ax.plot(["Q1", "Q2", "Q3", "Q4"], ac_l, marker='o', label=l_nick, color='green')
        ax.plot(["Q1", "Q2", "Q3", "Q4"], ac_v, marker='s', label=v_nick, color='blue')
        ax.set_title("Progresión Acumulada de Puntos")
        ax.legend()
        st.pyplot(fig)

    with col_res2:
        st.info("💡 Factores Aplicados")
        if venganza: st.write("🔥 Bono Venganza Activo")
        if pg_out: st.write("🐢 Ritmo lento (Falta Base)")
        if c_out: st.write("📂 Pintura débil (Falta Pívot)")
        if clutch: st.write("🔒 Ajuste Clutch (Defensa Q4)")
        if fatiga_gira: st.write("😴 Agotamiento fin de gira")
        
        # Tabla de cuartos
        st.table(pd.DataFrame({
            "Q": ["Q1", "Q2", "Q3", "Q4", "Total"],
            l_nick: [round(x,1) for x in q_l] + [res_l],
            v_nick: [round(x,1) for x in q_v] + [res_v]
        }))

    # --- 8. MONITOR DE DESVIACIÓN ---
    st.write("---")
    st.subheader("⏱️ MONITOR EN VIVO")
    lx1, lx2, lx3 = st.columns(3)
    live_l = lx1.number_input(f"Puntos {l_nick}", value=0)
    live_v = lx2.number_input(f"Puntos {v_nick}", value=0)
    tiempo = lx3.selectbox("Tiempo", ["Medio Tiempo (Q2)", "Final Q3"])
    
    if live_l > 0 or live_v > 0:
        factor = 2 if "Q2" in tiempo else 1.33
        p_final = (live_l + live_v) * factor
        desv = round(p_final - (res_l + res_v), 1)
        st.write(f"Tendencia: {round(p_final, 1)} pts | Desv: {'🔥' if desv > 5 else '❄️' if desv < -5 else '✅'} {desv}")