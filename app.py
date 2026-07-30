import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(
    page_title="Supervisório - Sismógrafo Píer 01",
    page_icon="🌋",
    layout="wide"
)

# Atualização automática contínua
st.fragment(run_every="5s")

st.title("🌋 Supervisório Sismógrafo - Píer 01")
st.markdown("---")

# Função para buscar token e dados na API do Arduino Cloud
@st.cache_data(ttl=3)
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

# Barra Lateral
st.sidebar.header("🔑 Credenciais da API")
client_id = st.sidebar.text_input("Client ID", value=st.secrets.get("CLIENT_ID", ""), type="password")
client_secret = st.sidebar.text_input("Client Secret", value=st.secrets.get("CLIENT_SECRET", ""), type="password")
thing_id = st.sidebar.text_input("Thing ID", value="52bbfd4b-ec60-4bd8-b4ee-4533abee77e4")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()

if client_id and client_secret and thing_id:
    dados_json, erro = buscar_dados_arduino(client_id, client_secret, thing_id)
    
    if erro:
        st.error(f"Não foi possível conectar com o Arduino Cloud: {erro}")
    elif dados_json:
        medidas = {item['name']: item['last_value'] for item in dados_json}
        ultima_atualizacao = dados_json[0].get('value_updated_at', 'N/A')
        
        st.caption(f"Última atualização registrada no servidor: **{ultima_atualizacao}**")

        # --- CARTÕES DE KPI PRINCIPAIS ---
        st.subheader("📌 Indicadores Principais")
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        col_kpi1.metric("Aceleração Z (Gravidade)", f"{medidas.get('accZ', 0):.2f} m/s²")
        col_kpi2.metric("Temperatura Operacional", f"{medidas.get('temperatura', 0):.1f} °C")
        col_kpi3.metric("Nível de Vibração", f"{medidas.get('vibration', 0):.2f}")
        
        reset_status = medidas.get('reset', False)
        col_kpi4.metric("Status do Equipamento", "RESET ATIVO" if reset_status else "NORMAL")

        st.markdown("---")

        # --- SEÇÃO DE GRÁFICOS ---
        st.subheader("📈 Monitoramento Gráfico em Tempo Real")
        
        col_graf1, col_graf2 = st.columns(2)

        # GRÁFICO 1: Acelerômetro (Barras Verticais)
        with col_graf1:
            df_acc = pd.DataFrame({
                'Eixo': ['Aceleração X', 'Aceleração Y', 'Aceleração Z'],
                'Valor (m/s²)': [medidas.get('accX', 0), medidas.get('accY', 0), medidas.get('accZ', 0)]
            })
            
            fig_acc = px.bar(
                df_acc, 
                x='Eixo', 
                y='Valor (m/s²)', 
                color='Eixo',
                text_auto='.2f',
                title="<b>Acelerômetro Triaxial (m/s²)</b>"
            )
            fig_acc.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_acc, use_container_width=True)

        # GRÁFICO 2: Giroscópio (Barras Horizontais)
        with col_graf2:
            df_gyro = pd.DataFrame({
                'Eixo': ['Giro X', 'Giro Y', 'Giro Z'],
                'Velocidade Angular (rad/s)': [medidas.get('gyroX', 0), medidas.get('gyroY', 0), medidas.get('gyroZ', 0)]
            })
            
            fig_gyro = px.bar(
                df_gyro, 
                y='Eixo', 
                x='Velocidade Angular (rad/s)', 
                color='Eixo',
                orientation='h',
                text_auto='.3f',
                title="<b>Giroscópio Triaxial (rad/s)</b>"
            )
            fig_gyro.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_gyro, use_container_width=True)

        # GRÁFICO 3: Gauge/Velocímetro de Temperatura
        col_graf3, col_graf4 = st.columns(2)
        
        with col_graf3:
            temp_val = medidas.get('temperatura', 0)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=temp_val,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "<b>Temperatura do Sensor (°C)</b>"},
                gauge={
                    'axis': {'range': [0, 60]},
                    'bar': {'color': "#ff4b4b"},
                    'steps': [
                        {'range': [0, 30], 'color': "#1e3d59"},
                        {'range': [30, 45], 'color': "#f5af19"},
                        {'range': [45, 60], 'color': "#e65c00"}
                    ],
                }
            ))
            fig_gauge.update_layout(height=320)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # GRÁFICO 4: Comparativo de Vibração x Temperatura
        with col_graf4:
            df_vib = pd.DataFrame({
                'Parâmetro': ['Vibração Absoluta', 'Temperatura (°C)'],
                'Valor': [medidas.get('vibration', 0), medidas.get('temperatura', 0)]
            })
            fig_vib = px.bar(
                df_vib,
                x='Parâmetro',
                y='Valor',
                color='Parâmetro',
                text_auto='.2f',
                title="<b>Status Operacional (Vibração & Temp)</b>"
            )
            fig_vib.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig_vib, use_container_width=True)

else:
    st.info("👈 Por favor, insira o **Client ID** e o **Client Secret** na barra lateral para carregar o supervisório.")
