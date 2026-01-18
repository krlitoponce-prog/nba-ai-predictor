import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from nba_api.stats.static import teams

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="NBA AI ELITE V7.2", layout="wide", page_icon="🔋")

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

# --- 3. EXTRACCIÓN DE LESIONES ---
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

# --- 4. SIDEBAR: CONTROL DE FATIGA Y GIRAS ---
with st.sidebar:
    st.header("📂 Carrito Permanente")
    st.write("---")
    st.subheader("🔋 Control de Fatiga")
    
    st.markdown("**Local:**")
    b2b_l = st.toggle("Local jugó ayer (B2B)")
    regreso_l = st.toggle("🔙 Regreso a Casa (B2B desde Visita)")
    gira_l = st.toggle("🏠 Gira Local (Estancia en Casa)")
    
    st.write("---")
    st.markdown("**Visitante:**")
    b2b_v = st.toggle("Visita jugó ayer (B2B)")
    viaje_v = st.toggle("✈️ Gira de Visitante / Viaje Largo")
    
    st.write("---")
    for t_info in sorted(all_nba_teams, key=lambda x: x['nickname']):
        nick = t_info['nickname'].lower()
        bajas = inj_db.get(nick, [])
        with st.expander(f"📍 {nick.upper()}"):
            if bajas:
                for p in bajas:
                    impacto = "🔴" if any(s in p.lower() for s in STARS) else "🟡"
                    st.write(f"{impacto} {p}")
            else: st.write("✅ Plantilla Completa")
    if st.button("🔄 ACTUALIZAR WEB"): st.rerun()

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🏀 NBA AI PRO V7.2: ULTIMATE ENGINE")

c1, c2 = st.columns(2)
with c1:
    l_name = st.selectbox("LOCAL", sorted([t['full_name'] for t in all_nba_teams]), index=0)
    l_data = next(t for t in all_nba_teams if t['full_name'] == l_name)
    s_l = ADVANCED_STATS.get(l_data['nickname'], [112, 114, 1.0, 3.5, 1.0])
    m_l = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({l_data['nickname']})")
    st.metric(f"Ritmo {l_data['nickname']}", f"{s_l[4]}x", f"Localía: +{s_l[3]}")

with c2:
    v_name = st.selectbox("VISITANTE", sorted([t['full_name'] for t in all_nba_teams]), index=1)
    v_data = next(t for t in all_nba_teams if t['full_name'] == v_name)
    s_v = ADVANCED_STATS.get(v_data['nickname'], [111, 115, 1.0, 3.5, 1.0])
    m_v = st.checkbox(f"🚨 FORZAR BAJA ESTRELLA ({v_data['nickname']})")
    st.metric(f"Ritmo {v_data['nickname']}", f"{s_v[4]}x", "Visitante")

# --- 6. LÓGICA DE PROYECCIÓN AVANZADA ---
if 'analisis' not in st.session_state: st.session_state.analisis = None

if st.button("🚀 INICIAR ANÁLISIS"):
    # Penalizaciones por Lesiones
    red_l = min(0.15, (0.08 if m_l else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(l_data['nickname'].lower(), [])))
    red_v = min(0.15, (0.08 if m_v else 0) + sum(0.045 if any(s in p.lower() for s in STARS) else 0.015 for p in inj_db.get(v_data['nickname'].lower(), [])))
    
    # NUEVA LÓGICA: Fatiga y Bonos de Gira
    # Local: Si es regreso a casa B2B, penaliza 4.5%. Si es B2B normal, 3.5%.
    fatiga_l = 0.045 if regreso_l else (0.035 if b2b_l else 0.0)
    bonus_gira_l = 0.015 if gira_l else 0.0
    
    # Visitante: Si es viaje largo 4.5%, si solo es B2B 3.5%
    fatiga_v = 0.045 if viaje_v else (0.035 if b2b_v else 0.0)
    
    # Bono Altitud
    altitud_bonus = 1.012 if l_data['nickname'] in ["Nuggets", "Jazz"] else 1.0
    
    # Ritmo Combinado (Baja si hay cansancio)
    ritmo_p = ((s_l[4] + s_v[4]) / 2) * (0.98 if (b2b_l or b2b_v or viaje_v or regreso_l) else 1.0)
    
    # Cálculo de Potencial (Factor defensivo 0.33 para realismo)
    pot_l = ((((s_l[0] * (1 - (red_l + fatiga_l) + bonus_gira_l)) * 0.7) + (s_v[1] * 0.33 if (b2b_v or viaje_v) else s_v[1] * 0.3)) * ritmo_p) * altitud_bonus
    pot_v = (((s_v[0] * (1 - (red_v + fatiga_v))) * 0.7) + (s_l[1] * 0.33 if (b2b_l or regreso_l) else s_l[1] * 0.3)) * ritmo_p
    
    res_l, res_v = round((pot_l + s_l[3]) * s_l[2], 1), round(pot_v * s_v[2], 1)
    
    # Distribución de Cuartos (26%, 26%, 24%, 24%)
    dist = [0.26, 0.26, 0.24, 0.24]
    q_l_base = [res_l * d for d in dist]
    q_v_base = [res_v * d for d in dist]
    
    # MODO CLUTCH (Ajuste si diferencia < 5)
    clutch_mode = False
    if abs(res_l - res_v) < 5:
        clutch_mode = True
        q_l_base[3] *= 0.95 # Baja el puntaje por defensa cerrada
        q_v_base[3] *= 0.95
        res_l = round(sum(q_l_base), 1)
        res_v = round(sum(q_v_base), 1)

    st.session_state.analisis = {
        "res_l": res_l, "res_v": res_v, "h_final": round(-(res_l - res_v), 1),
        "total": round(res_l + res_v, 1), "ritmo_p": ritmo_p,
        "l_nick": l_data['nickname'], "v_nick": v_data['nickname'],
        "b2b_l": b2b_l, "b2b_v": b2b_v, "viaje": viaje_v, "regreso": regreso_l, "gira": gira_l,
        "altitud": altitud_bonus > 1.0, "clutch": clutch_mode,
        "q_l": q_l_base, "q_v": q_v_base
    }

# --- 7. RESULTADOS ---
if st.session_state.analisis:
    a = st.session_state.analisis
    st.divider()
    
    # Panel de Alertas Dinámicas
    warn_cols = st.columns(4)
    if a['regreso']: warn_cols[0].error("🔙 REGRESO A CASA: Fatiga de re-entrada (-4.5%)")
    if a['gira']: warn_cols[1].success("🏠 GIRA LOCAL: Bono por estabilidad (+1.5%)")
    if a['viaje']: warn_cols[2].error("✈️ GIRA VISITA: Fatiga de viaje (-4.5%)")
    if a['altitud']: warn_cols[3].info("🏔️ ALTITUD: Bono Denver/Utah (+1.2%)")
    if a['clutch']: st.warning("🔒 MODO CLUTCH: Partido cerrado, defensa intensificada en Q4.")
    
    st.subheader(f"📊 PROYECCIÓN: {a['l_nick']} {a['res_l']} - {a['res_v']} {a['v_nick']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Hándicap Sugerido", a['h_final'])
    m2.metric("Total Puntos (O/U)", a['total'])
    m3.metric("Ritmo Combinado", f"{round(a['ritmo_p'], 2)}x")

    st.write("---")
    st.subheader("⏱️ MONITOR DE DESVIACIÓN EN VIVO")
    lc1, lc2, lc3 = st.columns(3)
    with lc1: live_l = st.number_input(f"Puntos {a['l_nick']}", value=0, key="live_l")
    with lc2: live_v = st.number_input(f"Puntos {a['v_nick']}", value=0, key="live_v")
    with lc3: tiempo = st.selectbox("Tiempo Transcurrido", ["Final Q2 (Medio Tiempo)", "Final Q3"], key="tiempo_live")

    if live_l > 0 or live_v > 0:
        factor = 2 if "Q2" in tiempo else 1.33
        p_final = (live_l + live_v) * factor
        desv = round(p_final - a['total'], 1)
        st.write(f"**Tendencia Actual:** {round(p_final, 1)} pts")
        if desv > 5: st.error(f"🔥 DESVIACIÓN: +{desv} (OVER)")
        elif desv < -5: st.success(f"❄️ DESVIACIÓN: {desv} (UNDER)")

    # Tabla de Cuartos
    qs = {"Periodo": ["Q1", "Q2", "Q3", "Q4", "TOTAL"],
          a['l_nick']: [round(a['q_l'][0],1), round(a['q_l'][1],1), round(a['q_l'][2],1), round(a['q_l'][3],1), a['res_l']],
          a['v_nick']: [round(a['q_v'][0],1), round(a['q_v'][1],1), round(a['q_v'][2],1), round(a['q_v'][3],1), a['res_v']]}
    st.table(pd.DataFrame(qs))