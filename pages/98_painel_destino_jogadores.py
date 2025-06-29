# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# ⚙️ Configuração da Página
st.set_page_config(page_title="🔧 Admin - Jogadores Base", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🔧 Painel de Administração - Jogadores Base")
st.markdown("### 🟢 Disponível  |  🟡 Leilão  |  🔵 Mercado  |  🔴 Atribuído a Time")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📦 Buscar jogadores base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data if res.data else []

# 📦 Buscar times
res_times = supabase.table("times").select("id", "nome").execute()
mapa_times = {t["nome"]: t["id"] for t in res_times.data}

# 🔍 Filtros
with st.sidebar:
    st.header("🎯 Filtros")
    filtro_nome = st.text_input("🔎 Nome do jogador")
    filtro_nacionalidade = st.text_input("🌍 Nacionalidade")
    filtro_overall = st.slider("⭐ Overall mínimo", min_value=0, max_value=99, value=0)

# 🎯 Função para status colorido
def status_cor(destino):
    if destino == "leilao":
        return "🟡"
    elif destino == "mercado":
        return "🔵"
    elif destino in mapa_times:
        return "🔴"
    else:
        return "🟢"

# 🔁 Filtrar jogadores
jogadores_filtrados = []
for j in jogadores:
    if filtro_nome.lower() not in j["nome"].lower():
        continue
    if filtro_nacionalidade and filtro_nacionalidade.lower() not in j.get("nacionalidade", "").lower():
        continue
    if int(j["overall"]) < filtro_overall:
        continue
    jogadores_filtrados.append(j)

# ❗ Nenhum jogador
if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

# 🔄 Exibir cada jogador
for jogador in jogadores_filtrados:
    with st.container():
        col1, col2 = st.columns([1, 5])

        with col1:
            st.image(jogador.get("imagem_url", ""), width=80)
            st.markdown(f"{status_cor(jogador.get('destino'))} **Status**")

        with col2:
            st.markdown(f"### {jogador['nome']}")
            st.markdown(f"- 📌 Posição: `{jogador.get('posicao', '-')}`")
            st.markdown(f"- ⭐ Overall: `{jogador.get('overall', '-')}`")
            st.markdown(f"- 🌍 Nacionalidade: `{jogador.get('nacionalidade', 'N/A')}`")
            if jogador.get("sofifa_id"):
                st.markdown(f"[🔗 SoFIFA](https://sofifa.com/player/{jogador['sofifa_id']})", unsafe_allow_html=True)

            novo_valor = st.number_input(
                "💰 Valor do Jogador",
                value=int(jogador["valor"]),
                step=500_000,
                key=f"valor_{jogador['id']}"
            )

            col_a, col_b, col_c = st.columns([3, 2, 2])

            # ✅ Atribuir a time
            time_selecionado = col_a.selectbox("👔 Time", list(mapa_times.keys()), key=f"time_{jogador['id']}")
            if col_b.button("✅ Atribuir", key=f"atribuir_{jogador['id']}"):
                id_time = mapa_times[time_selecionado]
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": time_selecionado, "valor": novo_valor}).eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} atribuído ao time {time_selecionado}.")
                st.experimental_rerun()

            # 🛒 Enviar para o mercado
            if col_c.button("🛒 Mercado", key=f"mercado_{jogador['id']}"):
                supabase.table("mercado_transferencias").insert({
                    "id_jogador_base": jogador["id"],
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": "mercado", "valor": novo_valor}).eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} enviado ao mercado.")
                st.experimental_rerun()

            # 📢 Enviar para o leilão
            if st.button("📢 Leilão", key=f"leilao_{jogador['id']}"):
                supabase.table("leiloes").insert({
                    "nome_jogador": jogador["nome"],
                    "posicao_jogador": jogador["posicao"],
                    "overall_jogador": jogador["overall"],
                    "valor_inicial": novo_valor,
                    "valor_atual": novo_valor,
                    "imagem_url": jogador.get("imagem_url", ""),
                    "nacionalidade": jogador.get("nacionalidade", ""),
                    "origem": "Jogadores Base",
                    "incremento_minimo": 3_000_000,
                    "inicio": None,
                    "fim": None,
                    "ativo": False,
                    "finalizado": False,
                    "enviado_bid": False,
                    "aguardando_validacao": False,
                    "validado": False,
                    "tempo_minutos": 2
                }).execute()
                supabase.table("jogadores_base").update({"destino": "leilao", "valor": novo_valor}).eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} enviado para o leilão.")
                st.experimental_rerun()
