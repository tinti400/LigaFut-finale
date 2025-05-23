import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔢 Buscar saldo
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
except Exception as e:
    st.error(f"Erro ao carregar saldo: {e}")
    saldo = 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🏷️ Time: {nome_time}")
with col2:
    st.markdown(f"### 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

st.markdown("---")

# ⚡ Ações rápidas
st.markdown("### 🔍 Ações rápidas")

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/8_1_Elenco.py", label="👥 Ver Elenco", icon="👥")
    st.page_link("pages/12_Negociacoes.py", label="🤝 Negociações", icon="🤝")
    st.page_link("pages/13_Propostas_Recebidas.py", label="📩 Propostas Recebidas", icon="📩")
with col2:
    st.page_link("pages/16_Propostas_Enviadas.py", label="📤 Propostas Enviadas", icon="📤")
    st.page_link("pages/11_Leilao_Sistema.py", label="🏆 Leilão do Sistema", icon="🏆")
