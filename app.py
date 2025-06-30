# app.py
# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image
import os

st.set_page_config(page_title="LigaFut 2025", page_icon="⚽", layout="wide")

# 🛡️ Verifica se o usuário está logado
if "usuario_id" not in st.session_state:
    st.switch_page("pages/1_🔐 Login.py")

# 🎨 Layout de boas-vindas no topo
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists("logo_ligafut.png"):
        st.image("logo_ligafut.png", width=150)
with col2:
    st.markdown("<h1 style='color: #1E90FF;'>🏆 Bem-vindo à LigaFut 2025</h1>", unsafe_allow_html=True)
    st.markdown("Gerencie sua equipe, participe dos leilões, negocie com outros clubes e dispute títulos!")

st.markdown("---")

# 📂 Menu lateral completo
try:
    if os.path.exists("logo_ligafut.png"):
        st.sidebar.image("logo_ligafut.png", width=160)
except:
    st.sidebar.markdown("## LigaFut")

st.sidebar.markdown(f"### 👋 {st.session_state.get('nome_time', 'Técnico')}")

# 🎮 Menu organizado por seções
st.sidebar.markdown("## ⚙️ Meu Time")
st.sidebar.page_link("pages/4_Elenco.py", label="👥 Elenco")
st.sidebar.page_link("pages/5_Estadio.py", label="🏟️ Estádio")
st.sidebar.page_link("pages/6_Painel_Tecnico.py", label="🎮 Painel Técnico")

st.sidebar.markdown("## 🔁 Transferências")
st.sidebar.page_link("pages/5_Mercado_Transferencias.py", label="💼 Mercado de Transferências")
st.sidebar.page_link("pages/11_Negociacoes.py", label="🤝 Negociações")
st.sidebar.page_link("pages/12_Propostas_Recebidas.py", label="📩 Propostas Recebidas")
st.sidebar.page_link("pages/13_Propostas_Enviadas.py", label="📤 Propostas Enviadas")
st.sidebar.page_link("pages/17_Leiloar_Jogador.py", label="📈 Leiloar Jogador")
st.sidebar.page_link("pages/10_Leilao_Sistema.py", label="🔨 Leilão")

st.sidebar.markdown("## 🏆 Competições")
st.sidebar.page_link("pages/3_Painel_Classificacao.py", label="📊 Classificação & Rodadas")
st.sidebar.page_link("pages/8_Copa_Liga.py", label="🏆 Copa da Liga")
st.sidebar.page_link("pages/24_Gerar_Grupos_Copa.py", label="🎯 Grupos da Copa")

st.sidebar.markdown("## 💣 Eventos")
st.sidebar.page_link("pages/19_Evento_Multa.py", label="💸 Evento Multa")
st.sidebar.page_link("pages/20_Evento_Roubo.py", label="🕵️ Evento Roubo")

st.sidebar.markdown("## 📄 Histórico")
st.sidebar.page_link("pages/18_Leiloes_Finalizados.py", label="✅ Leilões Finalizados")
st.sidebar.page_link("pages/16_Movimentacoes_Financeiras.py", label="📊 Painel Financeiro")

# 🔐 Admin (somente se for admin)
if st.session_state.get("administrador", False):
    st.sidebar.markdown("## 🛠️ Administração")
    st.sidebar.page_link("pages/14_Admin_Times.py", label="📋 Admin Times")
    st.sidebar.page_link("pages/15_Admin_Usuarios.py", label="👑 Admin Usuários")
    st.sidebar.page_link("pages/22_Painel_Salarios.py", label="💰 Painel Salários")
    st.sidebar.page_link("pages/23_Gerar_Rodadas.py", label="🗓️ Gerar Rodadas")
    st.sidebar.page_link("pages/9_Admin_Leilao.py", label="🛠️ Admin Leilões")

# 🚪 Logout
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    for key in ["usuario", "usuario_id", "id_time", "nome_time", "divisao", "session_id", "administrador"]:
        st.session_state.pop(key, None)
    st.success("✅ Logout realizado com sucesso.")
    st.switch_page("pages/1_🔐 Login.py")
