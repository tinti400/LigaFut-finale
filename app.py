import streamlit as st

# Definindo a navegação entre as páginas
page = st.sidebar.selectbox("Escolha uma página", ["Home", "Gerenciar Rodadas", "Outras Funcionalidades"])

if page == "Home":
    st.title("Bem-vindo ao LigaFut!")
    st.markdown("Aqui você pode gerenciar seu time e competir nas ligas. Escolha a página desejada no menu à esquerda.")
    # Aqui você pode adicionar conteúdo específico para a página Home

elif page == "Gerenciar Rodadas":
    # Carregar a página "5_Rodadas.py"
    st.experimental_rerun()

elif page == "Outras Funcionalidades":
    st.title("Outras funcionalidades...")
    # Adicione o conteúdo de outras funcionalidades aqui

