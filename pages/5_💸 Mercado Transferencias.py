# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# Status mercado
status_res = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = status_res.data[0]["mercado_aberto"] if status_res.data else False

if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento.")
    st.stop()

# Saldo
saldo_res = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
saldo_time = saldo_res.data[0]["saldo"] if saldo_res.data else 0
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# Filtros
st.markdown("### 🔍 Filtros de Pesquisa")
filtro_nome = st.text_input("Nome do jogador").strip().lower()
filtro_ordenacao = st.selectbox("Ordenar por", ["Nenhum", "Maior Overall", "Menor Overall", "Nome A-Z", "Nome Z-A"])

# Carrega jogadores
res = supabase.table("mercado_transferencias").select("*").execute()
mercado = res.data if res.data else []

jogadores_filtrados = [j for j in mercado if filtro_nome in j["nome"].lower()] if filtro_nome else mercado

# Ordenação
if filtro_ordenacao == "Maior Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0), reverse=True)
elif filtro_ordenacao == "Menor Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0))
elif filtro_ordenacao == "Nome A-Z":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower())
elif filtro_ordenacao == "Nome Z-A":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower(), reverse=True)

# Exibição
st.title("📈 Mercado de Transferências")

for jogador in jogadores_filtrados:
    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
    with col1:
        st.image(jogador.get("foto") or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
    with col2:
        st.markdown(f"**{jogador.get('nome')}**")
        st.markdown(f"Posição: {jogador.get('posicao')}")
        st.markdown(f"Overall: {jogador.get('overall')}")
    with col3:
        st.markdown(f"💰 Valor: R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
    with col4:
        if st.button(f"Comprar {jogador['nome']}", key=jogador["id"]):
            if saldo_time < jogador["valor"]:
                st.error("❌ Saldo insuficiente.")
            else:
                # Adiciona ao elenco
                jogador_data = {
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time
                }
                supabase.table("elenco").insert(jogador_data).execute()

                # Remove do mercado
                supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                # Registra movimentação e atualiza saldo
                registrar_movimentacao(
                    id_time=id_time,
                    jogador=jogador["nome"],
                    tipo="Mercado",
                    categoria="compra",
                    valor=jogador["valor"],
                    origem=jogador.get("time_origem"),
                    destino=nome_time
                )

                st.success(f"{jogador['nome']} comprado com sucesso!")
                st.experimental_rerun()

