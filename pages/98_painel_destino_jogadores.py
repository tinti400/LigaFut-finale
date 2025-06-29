# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# ⚙️ Configuração da Página
st.set_page_config(page_title="🔧 Admin - Leilão e Mercado", layout="wide")
st.title("🔧 Painel de Administração - Jogadores Base")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📦 Buscar jogadores base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data if res.data else []

# 📦 Buscar times
res_times = supabase.table("times").select("id", "nome").execute()
times = res_times.data if res_times.data else []
mapa_times = {t['nome']: t['id'] for t in times}

# 🎯 Filtros no topo
st.subheader("🎯 Filtros")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_nome = st.text_input("🔎 Nome do jogador")
with col_f2:
    filtro_nacionalidade = st.text_input("🌍 Nacionalidade")
with col_f3:
    filtro_overall = st.slider("⭐ Overall mínimo", min_value=0, max_value=99, value=0)

# Aplicar filtros
jogadores_filtrados = []
for j in jogadores:
    if filtro_nome.lower() not in j["nome"].lower():
        continue
    if filtro_nacionalidade and filtro_nacionalidade.lower() not in j.get("nacionalidade", "").lower():
        continue
    if int(j["overall"]) < filtro_overall:
        continue
    jogadores_filtrados.append(j)

# Mostrar jogadores
if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

for jogador in jogadores_filtrados:
    st.markdown("---")
    col1, col2 = st.columns([1, 4])

    # 📸 Imagem e Status
    with col1:
        st.image(jogador.get("imagem_url", ""), width=80)
        destino = jogador.get("destino", "nenhum")
        if destino == "leilao":
            st.markdown("🟡 **Leilão**")
        elif destino == "mercado":
            st.markdown("🔵 **Mercado**")
        elif destino in mapa_times:
            st.markdown("🔴 **Atribuído**")
        else:
            st.markdown("🟢 **Disponível**")

    # 🧾 Dados e Valor
    with col2:
        st.markdown(f"### {jogador['nome']}")
        st.markdown(f"- 📌 Posição: `{jogador.get('posicao', '-')}`")
        st.markdown(f"- 🌍 Nacionalidade: `{jogador.get('nacionalidade', '-')}`")
        st.markdown(f"- ⭐ Overall: `{jogador.get('overall', '-')}`")

        novo_valor = st.number_input(
            f"💰 Valor - {jogador['nome']}",
            value=int(jogador["valor"]),
            step=500_000,
            key=f"valor_{jogador['id']}"
        )

    # 🔘 Ações
    st.markdown("**Ações:**")
    col_a1, col_a2, col_a3 = st.columns(3)

    with col_a1:
        time_escolhido = st.selectbox("👔 Time", list(mapa_times.keys()), key=f"time_{jogador['id']}")
        if st.button("✅ Atribuir", key=f"atr_{jogador['id']}"):
            id_time = mapa_times[time_escolhido]
            supabase.table("elenco").insert({
                "id_time": id_time,
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador.get("imagem_url", "")
            }).execute()
            supabase.table("jogadores_base").update({
                "destino": time_escolhido,
                "valor": novo_valor
            }).eq("id", jogador["id"]).execute()
            st.success(f"{jogador['nome']} atribuído ao {time_escolhido}.")
            st.experimental_rerun()

    with col_a2:
        if st.button("🛒 Mercado", key=f"mercado_{jogador['id']}"):
            try:
                salario = int(novo_valor * 0.007)
                dados_mercado = {
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "foto": jogador.get("imagem_url", ""),
                    "nacionalidade": jogador.get("nacionalidade", ""),
                    "time_origem": jogador["destino"] if jogador["destino"] not in ["nenhum", "livre", ""] else "Livre",
                    "link_sofifa": jogador.get("link_sofifa", ""),
                    "salario": salario
                }
                supabase.table("mercado_transferencias").insert(dados_mercado).execute()
                supabase.table("jogadores_base").update({
                    "destino": "mercado",
                    "valor": novo_valor
                }).eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} enviado ao mercado.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao enviar jogador ao mercado: {e}")

    with col_a3:
        if st.button("📢 Leilão", key=f"leilao_{jogador['id']}"):
            supabase.table("fila_leilao").insert({
                "id_jogador_base": jogador["id"],
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador.get("imagem_url", ""),
                "status": "aguardando"
            }).execute()
            supabase.table("jogadores_base").update({
                "destino": "leilao",
                "valor": novo_valor
            }).eq("id", jogador["id"]).execute()
            st.success(f"{jogador['nome']} enviado para o leilão.")
            st.experimental_rerun()
