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

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("👥 Ver Elenco"):
        st.switch_page("4_Elenco")
with col2:
    if st.button("🔄 Negociações"):
        st.switch_page("11_Negociacoes")
with col3:
    if st.button("🎯 Leilão do Sistema"):
        st.switch_page("10_Leilao_Sistema")

col4, col5 = st.columns(2)
with col4:
    if st.button("📨 Propostas Recebidas"):
        st.switch_page("12_Propostas_Recebidas")
with col5:
    if st.button("📤 Propostas Enviadas"):
        st.switch_page("13_Propostas_Enviadas")
