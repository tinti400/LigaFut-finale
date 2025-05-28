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

# 🔀 Navegação entre seções internas
st.markdown("### 🔍 Ações rápidas")

aba = st.radio("Escolha uma seção:", [
    "🔙 Voltar para o Painel",
    "👥 Elenco",
    "🤝 Negociações",
    "📥 Propostas Recebidas",
    "📤 Propostas Enviadas",
    "🔨 Leilão do Sistema"
], index=0, horizontal=True)

st.markdown("---")

# 🔁 Redireciona visualmente sem recarregar o app
if aba == "👥 Elenco":
    with st.spinner("Carregando Elenco..."):
        exec(open("pages/4_Elenco.py").read())
elif aba == "🤝 Negociações":
    with st.spinner("Carregando Negociações..."):
        exec(open("pages/12_Negociacoes.py").read())
elif aba == "📥 Propostas Recebidas":
    with st.spinner("Carregando Propostas Recebidas..."):
        exec(open("pages/13_Propostas_Recebidas.py").read())
elif aba == "📤 Propostas Enviadas":
    with st.spinner("Carregando Propostas Enviadas..."):
        exec(open("pages/16_Propostas_Enviadas.py").read())
elif aba == "🔨 Leilão do Sistema":
    with st.spinner("Carregando Leilão..."):
        exec(open("pages/11_Leilao_Sistema.py").read())
else:
    st.success("Use os botões acima para navegar pelas seções do seu time.")
