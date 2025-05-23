import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Supabase
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

# 🔢 Saldo
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
st.markdown("### 🔍 Ações rápidas")

# 🔗 Função para criar botão-link
def botao_link(nome, destino):
    st.markdown(
        f"""
        <a href="/{destino}" target="_self">
            <button style='width: 100%; padding: 0.6em; font-size: 16px; margin-bottom: 0.5em;'>{nome}</button>
        </a>
        """,
        unsafe_allow_html=True
    )

col1, col2 = st.columns(2)
with col1:
    botao_link("👥 Ver Elenco", "4_Elenco")
    botao_link("🔄 Negociações", "11_Negociacoes")
    botao_link("🎯 Leilão do Sistema", "10_Leilao_Sistema")
with col2:
    botao_link("📨 Propostas Recebidas", "12_Propostas_Recebidas")
    botao_link("📤 Propostas Enviadas", "13_Propostas_Enviadas")
