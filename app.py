# app.py
import streamlit as st

st.set_page_config(page_title="LigaFut 2025", page_icon="⚽", layout="wide")

# 🔄 Redireciona para o login ao abrir o app
if "usuario_id" not in st.session_state:
    st.switch_page("pages/1_🔐 Login.py")
else:
    st.switch_page("pages/3_Home.py")
