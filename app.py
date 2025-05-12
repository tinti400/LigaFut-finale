import streamlit as st

# Função para a página "Home"
def home_page():
    st.title("Bem-vindo ao LigaFut!")
    st.markdown("Aqui você pode gerenciar seu time e competir nas ligas. Escolha a página desejada no menu à esquerda.")
    st.image("https://via.placeholder.com/800x300.png", use_column_width=True)  # Exemplo de imagem

# Função para a página "Gerenciar Rodadas"
def gerenciar_rodadas():
    st.title("Gerenciar Rodadas")
    st.markdown("Aqui você pode gerenciar as rodadas do campeonato.")
    
    # Exemplo de tabela para rodadas
    st.write("Em breve, uma tabela interativa para gerenciar as rodadas será exibida aqui.")
    
    # Exemplo de dados fictícios para rodadas
    data_rodadas = {
        "Rodada": [1, 2, 3],
        "Time A": ["Palmeiras", "Flamengo", "São Paulo"],
        "Time B": ["Corinthians", "Grêmio", "Vasco"],
        "Data": ["2025-05-10", "2025-05-12", "2025-05-14"]
    }
    st.table(data_rodadas)

# Função para a página "Outras Funcionalidades"
def outras_funcionalidades():
    st.title("Outras Funcionalidades")
    st.write("Em breve, mais funcionalidades serão adicionadas ao seu campeonato.")
    
    # Exemplo de botão que poderia abrir uma nova funcionalidade
    if st.button("Adicionar Nova Rodada"):
        st.write("Aqui você pode adicionar novas rodadas ao campeonato.")
    
    st.write("Mais opções de funcionalidades para o seu campeonato virão logo!")

# Função para a página "Painel do Técnico"
def painel_tec():
    st.title("Painel do Técnico")
    st.markdown("Aqui você pode gerenciar o seu time e acompanhar as rodadas da liga.")
    # Conteúdo adicional sobre o painel do técnico pode ser adicionado aqui
    st.write("Mais funcionalidades estão em desenvolvimento...")

# Função para a página "Elenco"
def elenco():
    st.title("Elenco")
    st.markdown("Aqui você pode visualizar e gerenciar os jogadores do seu time.")
    # Aqui poderia ser exibido o elenco do time, como foi descrito antes
    st.write("Em breve, você poderá ver seu elenco e realizar transferências!")

# Definindo a navegação entre as páginas
page = st.sidebar.selectbox(
    "Escolha uma página",
    ["Home", "Gerenciar Rodadas", "Outras Funcionalidades", "Painel do Técnico", "Elenco"]
)

# Verificando qual página foi escolhida e chamando a função correspondente
if page == "Home":
    home_page()

elif page == "Gerenciar Rodadas":
    gerenciar_rodadas()

elif page == "Outras Funcionalidades":
    outras_funcionalidades()

elif page == "Painel do Técnico":
    painel_tec()

elif page == "Elenco":
    elenco()
