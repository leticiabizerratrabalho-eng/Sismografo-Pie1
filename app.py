import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Supervisório - Sismógrafo Píer 01",
    page_icon="🌋",
    layout="wide"
)

st.title("🌋 Supervisório Sismógrafo - Píer 01")
st.markdown("---")

# Função para buscar token e dados na API do Arduino Cloud
@st.cache_data(ttl=5)
def buscar_dados_arduino(client_id, client_secret, thing_id):
    try:
        # 1. Requisição do Token
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

        # 2. Requisição das Propriedades
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

# Barra Lateral - Configurações de Acesso
st.sidebar.header("🔑 Credenciais da API")
client_id = st.sidebar.text_input("Client ID", value=st.secrets.get("CLIENT_ID", ""), type="password")
client_secret = st.sidebar.text_input("Client Secret", value=st.secrets.get("CLIENT_SECRET", ""), type="password")
thing_id = st.sidebar.text_input("Thing ID", value="52bbfd4b-ec60-4bd8-b4ee-4533abee77e4")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()

# Processamento e Exibição dos Dados
if client_id and client_secret and thing_id:
    dados_json, erro = buscar_dados_arduino(client_id, client_secret, thing_id)
    
    if erro:
        st.error(f"Não foi possível conectar com o Arduino Cloud: {erro}")
    elif dados_json:
        medidas = {item['name']: item['last_value'] for item in dados_json}
        
        ultima_atualizacao = dados_json[0].get('value_updated_at', 'N/A')
        st.caption(f"Última atualização registrada no servidor: **{ultima_atualizacao}**")

        # --- SEÇÃO 1: ACELERÔMETRO ---
        st.subheader("📊 Aceleração (m/s²)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Aceleração X (accX)", f"{medidas.get('accX', 0):.2f} m/s²")
        col2.metric("Aceleração Y (accY)", f"{medidas.get('accY', 0):.2f} m/s²")
        col3.metric("Aceleração Z (accZ)", f"{medidas.get('accZ', 0):.2f} m/s²")

        st.markdown("---")

        # --- SEÇÃO 2: GIROSCÓPIO ---
        st.subheader("🔄 Giroscópio (rad/s)")
        col4, col5, col6 = st.columns(3)
        col4.metric("Giro X (gyroX)", f"{medidas.get('gyroX', 0):.3f} rad/s")
        col5.metric("Giro Y (gyroY)", f"{medidas.get('gyroY', 0):.3f} rad/s")
        col6.metric("Giro Z (gyroZ)", f"{medidas.get('gyroZ', 0):.3f} rad/s")

        st.markdown("---")

        # --- SEÇÃO 3: AMBIENTE E ESTRUTURA ---
        st.subheader("🌡️ Condições de Operação")
        col7, col8, col9 = st.columns(3)
        
        temp = medidas.get('temperatura', 0)
        vib = medidas.get('vibration', 0)
        reset_status = medidas.get('reset', False)
        
        col7.metric("Temperatura", f"{temp:.1f} °C")
        col8.metric("Nível de Vibração", f"{vib:.2f}")
        col9.metric("Status do Reset", "ATIVO" if reset_status else "NORMAL")

        # --- SEÇÃO 4: GRÁFICO COMPARATIVO ---
        st.markdown("---")
        st.subheader("📈 Comparativo dos Eixos de Aceleração")
        
        df_acc = pd.DataFrame({
            'Eixo': ['Aceleração X', 'Aceleração Y', 'Aceleração Z'],
            'Valor (m/s²)': [medidas.get('accX', 0), medidas.get('accY', 0), medidas.get('accZ', 0)]
        })
        
        fig = px.bar(
            df_acc, 
            x='Eixo', 
            y='Valor (m/s²)', 
            color='Eixo',
            text_auto='.2f',
            title="Leitura Atual do Acelerômetro Triaxial"
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Por favor, insira o **Client ID** e o **Client Secret** na barra lateral para carregar o supervisório.")
