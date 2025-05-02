import streamlit as st

st.set_page_config(page_title="Home - LigaFut", page_icon="🏠", layout="centered")

st.markdown("<h2 style='text-align:center;'>🏠 Bem-vindo ao LigaFut</h2>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# 🔐 Verifica se está logado
if "usuario" not in st.session_state:
    st.warning("⚠️ Você precisa fazer login primeiro.")
    st.stop()

# 🔎 Recupera informações da sessão
usuario = st.session_state.get("usuario", "Desconhecido")
nome_time = st.session_state.get("nome_time", "Sem time")
divisao = st.session_state.get("divisao", "Sem divisão")

# 🟢 Exibe informações do técnico logado
st.success(f"🔓 Técnico logado: `{usuario}`")
st.info(f"🏆 Time: `{nome_time}`")
st.info(f"📊 Divisão atual: `{divisao}`")
