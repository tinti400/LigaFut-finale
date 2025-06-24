# app.py
import streamlit as st
from PIL import Image
import os
import runpy

st.set_page_config(page_title="LigaFut 2025", page_icon="⚽", layout="wide")

# 🛡️ Bloqueio: só permite acesso se estiver logado
if "usuario_id" not in st.session_state:
    st.switch_page("pages/1_🔐 Login.py")

# 🎨 Layout topo
col1, col2 = st.columns([1, 3])
with col1:
    logo = Image.open("logo_ligafut.png") if os.path.exists("logo_ligafut.png") else None
    if logo:
        st.image(logo, width=150)
with col2:
    st.markdown("<h1 style='color: #1E90FF;'>🏆 Bem-vindo à LigaFut 2025</h1>", unsafe_allow_html=True)
    st.markdown("Gerencie sua equipe, participe dos leilões, negocie com outros clubes e dispute títulos!")

st.markdown("---")

# 📂 Menu lateral
st.sidebar.title("📂 Navegação")
pagina = st.sidebar.radio("Ir para:", [
    "Elenco",
    "Classificação & Rodadas",
    "Editar Resultados",
    "Mercado de Transferências",
    "Leilão",
    "Negociações",
    "Propostas Recebidas",
    "Painel Financeiro",
    "Cadastro",
    "Logout"
])

# 🔗 Mapeamento das páginas
paginas_arquivos = {
    "Elenco": "pages/4_Elenco.py",
    "Classificação & Rodadas": "pages/4_📊 Classificacao & Rodadas.py",
    "Editar Resultados": "pages/19_✏️ Editar Resultados.py",
    "Mercado de Transferências": "pages/5_Mercado_Transferencias.py",
    "Leilão": "pages/10_Leilao_Sistema.py",
    "Negociações": "pages/11_Negociacoes.py",
    "Propostas Recebidas": "pages/12_Propostas_Recebidas.py",
    "Painel Financeiro": "pages/7_Painel_Financeiro.py",
    "Cadastro": "pages/2_📝 Cadastro.py",
}

# 🧭 Navegação para cada página
if pagina == "Logout":
    for key in ["usuario", "usuario_id", "id_time", "nome_time", "divisao", "session_id", "administrador"]:
        st.session_state.pop(key, None)
    st.success("✅ Logout realizado com sucesso. Redirecionando...")
    st.switch_page("pages/1_🔐 Login.py")
elif pagina in paginas_arquivos:
    runpy.run_path(paginas_arquivos[pagina], run_name="__main__")
