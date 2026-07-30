import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="PGL 01- Sismógrafo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Atualização automática contínua
st.fragment(run_every="3s")

# Estilo para tema escuro e layout limpo similar ao Arduino Cloud
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar histórico na sessão
if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=[
        "Horário", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ", "vibration", "temperatura"
    ])

# Função para buscar token e dados na API do Arduino Cloud
@st.cache_data(ttl=2)
def buscar_dados_arduino(client_id, client_secret, thing_id):
    try:
        token_url = "https://api2.arduino.cc/iot/v1/clients/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": "https://api2.arduino.cc/iot"
        }
        headers = {"Content-Type": "application/json"}
        
        token_res = requests.post(token_url, json=payload, headers=headers, timeout=10)
        if token_res.status_code != 200:
            return None, f"Erro na Autenticação ({token_res.status_code})"
            
        token = token_res.json().get("access_token")

        data_url = f"https://api2.arduino.cc/iot/v2/things/{thing_id}/properties"
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data_res = requests.get(data_url, headers=auth_headers, timeout=10)
        if data_res.status_code == 200:
            return data_res.json(), None
        else:
            return None, f"Erro ao buscar propriedades ({data_res.status_code})"
            
    except Exception as e:
        return None, str(e)

# Configurações na Barra Lateral
st.sidebar.header("🔑 Credenciais da API")
client_id = st.sidebar.text_input("Client ID", value=st.secrets.get("CLIENT_ID", ""), type="password")
client_secret = st.sidebar.text_input("Client Secret", value=st.secrets.get("CLIENT_SECRET", ""), type="password")
thing_id = st.sidebar.text_input("Thing ID", value="52bbfd4b-ec60-4bd8-b4ee-4533abee77e4")

if client_id and client_secret and thing_id:
    dados_json, erro = buscar_dados_arduino(client_id, client_secret, thing_id)
    
    if erro:
        st.error(f"Erro na conexão: {erro}")
    elif dados_json:
        medidas = {item['name']: item['last_value'] for item in dados_json}
        
        # Adiciona nova leitura ao histórico
        nova_linha = {
            "Horário": datetime.now().strftime("%H:%M:%S"),
            "accX": medidas.get('accX', 0),
            "accY": medidas.get('accY', 0),
            "accZ": medidas.get('accZ', 0),
            "gyroX": medidas.get('gyroX', 0),
            "gyroY": medidas.get('gyroY', 0),
            "gyroZ": medidas.get('gyroZ', 0),
            "vibration": medidas.get('vibration', 0),
            "temperatura": medidas.get('temperatura', 0)
        }
        
        df_novo = pd.DataFrame([nova_linha])
        st.session_state.historico = pd.concat([st.session_state.historico, df_novo], ignore_index=True).tail(30)
        df_hist = st.session_state.historico

        # --- CABEÇALHO ---
        st.title("PGL 01- Sismógrafo")
        st.markdown("---")

        # --- LINHA TOP: LOGO / CARTOES AMBIENTE & VIBRAÇÃO HISTÓRICO ---
        c_top1, c_top2 = st.columns([1, 2])
        
        with c_top1:
            sub1, sub2, sub3 = st.columns(3)
            sub1.metric("Redefinir online", "OFF" if not medidas.get('reset') else "ON")
            sub2.metric("Temperatura Ambiente", f"{medidas.get('temperatura', 0):.1f} °C")
            sub3.metric("Vibração", f"{medidas.get('vibration', 0):.1f}")

        with c_top2:
            fig_vib = px.line(df_hist, x="Horário", y="vibration", title="<b>Vibração (AO VIVO)</b>", color_discrete_sequence=['#ff4b4b'])
            fig_vib.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), template="plotly_dark")
            st.plotly_chart(fig_vib, use_container_width=True)

        st.markdown("---")

        # --- SEÇÃO PRINCIPAL: GIROSCÓPIO X ACELERÔMETRO ---
        col_giro, col_acc = st.columns(2)

        # COLUNA 1: GIROSCÓPIO (Torção Estrutural)
        with col_giro:
            st.markdown("### Giroscópio - (Torção Estrutural)")
            
            # Giro X
            g1_kpi, g1_chart = st.columns([1, 3])
            g1_kpi.metric("GiroX - °/s", f"{medidas.get('gyroX', 0):.2e}")
            fig_gx = px.line(df_hist, x="Horário", y="gyroX", color_discrete_sequence=['#2ecc71'])
            fig_gx.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            g1_chart.plotly_chart(fig_gx, use_container_width=True)

            # Giro Y
            g2_kpi, g2_chart = st.columns([1, 3])
            g2_kpi.metric("GiroY - °/s", f"{medidas.get('gyroY', 0):.2e}")
            fig_gy = px.line(df_hist, x="Horário", y="gyroY", color_discrete_sequence=['#3498db'])
            fig_gy.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            g2_chart.plotly_chart(fig_gy, use_container_width=True)

            # Giro Z
            g3_kpi, g3_chart = st.columns([1, 3])
            g3_kpi.metric("Giroscópio - °/s", f"{medidas.get('gyroZ', 0):.2e}")
            fig_gz = px.line(df_hist, x="Horário", y="gyroZ", color_discrete_sequence=['#9b59b6'])
            fig_gz.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            g3_chart.plotly_chart(fig_gz, use_container_width=True)

        # COLUNA 2: ACELERÔMETRO (Inclinação e Impacto)
        with col_acc:
            st.markdown("### Acelerômetro - Inclinação e Impacto Lateral/Vertical")
            
            # Acc X
            a1_kpi, a1_chart = st.columns([1, 3])
            a1_kpi.metric("AccX - m/s² (Inclinação)", f"{medidas.get('accX', 0):.3f}")
            fig_ax = px.line(df_hist, x="Horário", y="accX", color_discrete_sequence=['#2ecc71'])
            fig_ax.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            a1_chart.plotly_chart(fig_ax, use_container_width=True)

            # Acc Y
            a2_kpi, a2_chart = st.columns([1, 3])
            a2_kpi.metric("AccY - m/s² (Inclinação)", f"{medidas.get('accY', 0):.3f}")
            fig_ay = px.line(df_hist, x="Horário", y="accY", color_discrete_sequence=['#1abc9c'])
            fig_ay.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            a2_chart.plotly_chart(fig_ay, use_container_width=True)

            # Acc Z
            a3_kpi, a3_chart = st.columns([1, 3])
            a3_kpi.metric("AccZ - m/s² (Impacto Vertical)", f"{medidas.get('accZ', 0):.3f}")
            fig_az = px.line(df_hist, x="Horário", y="accZ", color_discrete_sequence=['#8e44ad'])
            fig_az.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
            a3_chart.plotly_chart(fig_az, use_container_width=True)

else:
    st.info("👈 Por favor, insira as credenciais na barra lateral para carregar o painel.")
