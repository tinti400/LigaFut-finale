import streamlit as st

st.set_page_config(page_title="Painel Inicial", page_icon="⚽", layout="wide")

st.markdown("<h1 style='text-align: center;'>⚽ LigaFut - Painel Inicial</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Gerencie seu time, participe de eventos e acompanhe o mercado.</h4>", unsafe_allow_html=True)
st.markdown("---")

# 🔐 Se for admin, mostra o botão para cadastro
if st.session_state.get("usuario") == "admin@ligafut.com":
    st.markdown("### 👑 Área Administrativa")
    st.markdown("[📝 Cadastrar Técnico e Time](/_Cadastro)")

st.markdown("### 👥 Ações disponíveis")
st.info("Use o menu lateral para acessar as funcionalidades da sua liga.")
