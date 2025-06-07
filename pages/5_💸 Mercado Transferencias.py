# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz
from utils import registrar_movimentacao

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📅 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🛡️ Verifica se o mercado está aberto
try:
    status_res = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
    mercado_aberto = status_res.data[0]["mercado_aberto"] if status_res.data else False
except Exception as e:
    st.error(f"Erro ao verificar status do mercado: {e}")
    mercado_aberto = False

if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento. Aguarde a próxima janela de transferências.")
    st.stop()

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

# 🌟 Aplica filtros
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

jogadores_por_pagina = 10
total_jogadores = len(jogadores_filtrados)
total_paginas = (total_jogadores + jogadores_por_pagina - 1) // jogadores_por_pagina

pagina_atual = st.session_state["pagina_mercado"]
inicio = (pagina_atual - 1) * jogadores_por_pagina
fim = inicio + jogadores_por_pagina
jogadores_pagina = jogadores_filtrados[inicio:fim]

# 🔄 Navegação
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav1:
    if st.button("⏪ Anterior", disabled=pagina_atual <= 1):
        st.session_state["pagina_mercado"] -= 1
        st.rerun()
with col_nav2:
    st.markdown(f"<p style='text-align: center;'>Página {pagina_atual} de {total_paginas}</p>", unsafe_allow_html=True)
with col_nav3:
    if st.button("⏩ Próxima", disabled=pagina_atual >= total_paginas):
        st.session_state["pagina_mercado"] += 1
        st.rerun()

# 📋 Exibição dos jogadores
if not jogadores_pagina:
    st.info("Nenhum jogador disponível com os filtros selecionados.")
else:
    for jogador in jogadores_pagina:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2])
        with col1:
            st.image(jogador.get("foto") or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
        with col2:
            st.markdown(f"**🎯 Jogador alvo:** {jogador.get('nome', 'Desconhecido')}")
            st.markdown(f"**📌 Posição:** {jogador.get('posicao', 'Desconhecida')}")
            st.markdown(f"**⭐ Overall:** {jogador.get('overall', 'N/A')}")
            st.markdown(f"**🌍 Nacionalidade:** {jogador.get('nacionalidade', 'Desconhecida')}")
            st.markdown(f"**🏠 Origem:** {jogador.get('time_origem', 'Desconhecida')}")
        with col3:
            st.markdown(f"**💰 Valor:** R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))

        # ✅ Comprar
        if st.button(f"✅ Comprar {jogador['nome']}", key=f"comprar_{jogador['id']}"):
            try:
                elenco_res = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
                if elenco_res.data and len(elenco_res.data) >= 35:
                    st.error("❌ Você já tem o número máximo de jogadores (35). Venda alguém para continuar.")
                    st.stop()

                if saldo_time < jogador.get("valor", 0):
                    st.error("❌ Saldo insuficiente.")
                    st.stop()

                jogador_data = {
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time
                }
                supabase.table("elenco").insert(jogador_data).execute()
                supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                registrar_movimentacao(
                    supabase,
                    id_time,
                    jogador["nome"],
                    tipo="compra",
                    categoria="mercado",
                    valor=-abs(jogador["valor"])
                )

                st.success(f"Você comprou {jogador['nome']} com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao comprar jogador: {e}")

        # ❌ Excluir jogador do mercado
        if st.button(f"❌ Excluir {jogador['nome']} do Mercado", key=f"excluir_{jogador['id']}"):
            try:
                supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()
                st.success(f"Jogador {jogador['nome']} foi excluído do mercado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir jogador: {e}")
