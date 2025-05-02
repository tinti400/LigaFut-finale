import streamlit as st

# Função para a página "Home"
def home_page():
    st.title("Bem-vindo ao LigaFut!")
    st.markdown("Aqui você pode gerenciar seu time e competir nas ligas. Escolha a página desejada no menu à esquerda.")

# Função para a página "Gerenciar Rodadas"
def gerenciar_rodadas():
    st.title("Gerenciar Rodadas")
    # Aqui você pode carregar conteúdo relacionado a rodadas, como uma tabela de jogos
    # Exemplo: carregar a lista de rodadas de um banco de dados
    st.write("Aqui você pode gerenciar as rodadas do seu campeonato.")

# Função para a página "Outras Funcionalidades"
def outras_funcionalidades():
    st.title("Outras funcionalidades...")
    # Adicione o conteúdo para outras funcionalidades aqui
    st.write("Mais opções de funcionalidades para o seu campeonato.")

# Definindo a navegação entre as páginas
page = st.sidebar.selectbox("Escolha uma página", ["Home", "Gerenciar Rodadas", "Outras Funcionalidades"])

# Verificando qual página foi escolhida e chamando a função correspondente
if page == "Home":
    home_page()

elif page == "Gerenciar Rodadas":
    gerenciar_rodadas()

elif page == "Outras Funcionalidades":
    outras_funcionalidades()
