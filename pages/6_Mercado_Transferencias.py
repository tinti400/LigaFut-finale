import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

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

# 💰 Verifica saldo do time
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
    if saldo_res.data:
        saldo_time = saldo_res.data[0]["saldo"]
        st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))
    else:
        st.error("❌ Time não encontrado ou saldo indisponível.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao buscar saldo: {e}")
    st.stop()

st.title("🏦 Mercado de Transferências")

# 🔍 Filtros de Pesquisa
st.markdown("### 🔍 Filtros de Pesquisa")
filtro_nome = st.text_input("Nome do jogador").strip().lower()
filtro_ordenacao = st.selectbox("Ordenar por", ["Nenhum", "Maior Overall", "Menor Overall", "Nome A-Z", "Nome Z-A"])

# 🔍 Busca jogadores no mercado
try:
    mercado_ref = supabase.table("mercado_transferencias").select("*").execute()
    mercado = mercado_ref.data
except Exception as e:
    st.error(f"Erro ao carregar o mercado de transferências: {e}")
    mercado = []

# 🎯 Aplica filtros
jogadores_filtrados = []
for j in mercado:
    if filtro_nome and filtro_nome not in j["nome"].lower():
        continue
    jogadores_filtrados.append(j)

# 📊 Ordenação
if filtro_ordenacao == "Maior Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0), reverse=True)
elif filtro_ordenacao == "Menor Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0))
elif filtro_ordenacao == "Nome A-Z":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower())
elif filtro_ordenacao == "Nome Z-A":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower(), reverse=True)

# 🔢 Paginação
if "pagina_mercado" not in st.session_state:
    st.session_state["pagina_mercado"] = 1

# Número de jogadores por página
jogadores_por_pagina = 10
total_jogadores = len(jogadores_filtrados)
total_paginas = (total_jogadores + jogadores_por_pagina - 1) // jogadores_por_pagina

# Obter jogadores da página atual
pagina_atual = st.session_state["pagina_mercado"]
inicio = (pagina_atual - 1) * jogadores_por_pagina
fim = inicio + jogadores_por_pagina
jogadores_pagina = jogadores_filtrados[inicio:fim]

# 🔄 Navegação
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    if st.button("⏪ Anterior", disabled=pagina_atual <= 1):
        st.session_state["pagina_mercado"] -= 1
        st.experimental_rerun()
with col_nav2:
    st.markdown(f"<p style='text-align: center;'>Página {pagina_atual} de {total_paginas}</p>", unsafe_allow_html=True)
with col_nav3:
    if st.button("⏩ Próxima", disabled=pagina_atual >= total_paginas):
        st.session_state["pagina_mercado"] += 1
        st.experimental_rerun()

# 📋 Exibição dos jogadores
if not jogadores_pagina:
    st.info("Nenhum jogador disponível com os filtros selecionados.")
else:
    for jogador in jogadores_pagina:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2])
        with col1:
            if jogador.get("foto"):
                st.image(jogador["foto"], width=60)
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
        with col2:
            st.markdown(f"**🎯 Jogador alvo:** {jogador.get('nome', 'Desconhecido')}")
            st.markdown(f"**📌 Posição:** {jogador.get('posicao', 'Desconhecida')}")
            st.markdown(f"**⭐ Overall:** {jogador.get('overall', 'N/A')}")
            st.markdown(f"**🌍 Nacionalidade:** {jogador.get('nacionalidade', 'Desconhecida')}")
            st.markdown(f"**🏠 Origem:** {jogador.get('time_origem', 'Desconhecida')}")
        with col3:
            st.markdown(f"**💰 Valor:** R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))

        # Botão de Comprar
        if st.button(f"✅ Comprar {jogador['nome']}", key=f"comprar_{jogador['id']}"):
            if saldo_time >= jogador.get("valor", 0):
                try:
                    # Lógica para comprar o jogador
                    # 1. Adiciona o jogador ao elenco do time
                    jogador_data = {
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": jogador["valor"],
                        "id_time": id_time  # Atualiza o time do jogador
                    }
                    supabase.table("elenco").insert(jogador_data).execute()

                    # 2. Remove o jogador do mercado
                    supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                    # 3. Atualiza saldo
                    novo_saldo = saldo_time - jogador.get("valor", 0)
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    st.success(f"Você comprou {jogador['nome']} com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao comprar jogador: {e}")
            else:
                st.error("❌ Saldo insuficiente.")

        # **Botão de Excluir Jogador do Mercado**
        if st.button(f"❌ Excluir {jogador['nome']} do Mercado", key=f"excluir_{jogador['id']}"):
            try:
                # Confirmação para excluir jogador do mercado
                confirm = st.confirm("Tem certeza que deseja excluir esse jogador do mercado?")
                if confirm:
                    # Exclui o jogador do mercado
                    supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()
                    st.success(f"Jogador {jogador['nome']} foi excluído com sucesso do mercado!")
            except Exception as e:
                st.error(f"Erro ao excluir jogador do mercado: {e}")
