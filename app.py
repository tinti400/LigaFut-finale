# app.py
import streamlit as st

# Configurações da página principal
st.set_page_config(
    page_title="LigaFut 2025",
    page_icon="⚽",
    layout="wide"
)

# Conteúdo da Home
st.markdown("<h1 style='text-align: center;'>⚽ Bem-vindo à LigaFut</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Gerencie sua liga, negocie jogadores e acompanhe seu elenco com seus amigos.</h4>", unsafe_allow_html=True)

# Imagem ilustrativa (pode ser personalizada)
st.image("https://via.placeholder.com/900x300.png", use_column_width=True)

# Instruções
st.info("👉 Use o menu lateral para navegar pelas funcionalidades da sua liga.")
