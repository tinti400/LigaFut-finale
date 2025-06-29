# 20_🔧 Admin Leilao.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="🔧 Admin - Leilão e Mercado", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🔧 Painel de Administração - Leilão e Mercado")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🧾 Lista jogadores com destino mercado ou leilao
res = supabase.table("jogadores_base").select("*").in_("destino", ["mercado", "leilao"]).execute()
jogadores = res.data

# 📌 Lista times
res_times = supabase.table("times").select("id", "nome").execute()
times = res_times.data
mapa_times = {t['nome']: t['id'] for t in times}

# 🔍 Filtros
filtro_nome = st.text_input("🔎 Filtrar por nome:")

jogadores_filtrados = [j for j in jogadores if filtro_nome.lower() in j["nome"].lower()]

if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

# 🧩 Exibição
for jogador in jogadores_filtrados:
    with st.container(border=True):
        cols = st.columns([1, 3, 2, 2, 2, 2])

        cols[0].image(jogador["imagem_url"], width=80)
        cols[1].markdown(f"**{jogador['nome']}**\n`{jogador['posicao']}` — {jogador['nacionalidade']}")
        cols[2].markdown(f"💰 Valor: R$ {int(jogador['valor']):,}".replace(",", "."))
        cols[3].markdown(f"🎯 Destino: `{jogador['destino']}`")
        cols[4].markdown(f"📎 [Ficha Técnica](https://sofifa.com/player/{jogador['sofifa_id']}/) ")

        if jogador["destino"] == "mercado":
            if cols[5].button("🛒 Confirmar Mercado", key=f"mercado_{jogador['uuid']}"):
                supabase.table("mercado_transferencias").insert({
                    "uuid": jogador["uuid"],
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                st.success(f"{jogador['nome']} enviado ao mercado com sucesso!")

        elif jogador["destino"] == "leilao":
            if cols[5].button("📢 Confirmar Leilão", key=f"leilao_{jogador['uuid']}"):
                supabase.table("fila_leilao").insert({
                    "uuid": jogador["uuid"],
                    "valor": jogador["valor"],
                    "imagem_url": jogador["imagem_url"],
                    "status": "aguardando"
                }).execute()
                st.success(f"{jogador['nome']} enviado à fila do leilão.")

        # 🟢 Atribuir manualmente a um time existente
        st.divider()
        col_nome, col_valor, col_time, col_botao = st.columns([2, 2, 3, 2])

        novo_valor = col_valor.number_input("💰 Novo valor:", value=int(jogador["valor"]), step=1000000, key=f"val_{jogador['uuid']}")
        nome_time = col_time.selectbox("👔 Atribuir a: ", list(mapa_times.keys()), key=f"time_{jogador['uuid']}")

        if col_botao.button("✅ Atribuir", key=f"atr_{jogador['uuid']}"):
            id_time = mapa_times[nome_time]
            supabase.table("elenco").insert({
                "id_time": id_time,
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador["imagem_url"]
            }).execute()
            supabase.table("jogadores_base").update({"destino": nome_time, "valor": novo_valor}).eq("uuid", jogador["uuid"]).execute()
            st.success(f"✅ {jogador['nome']} atribuído ao {nome_time} com sucesso!")
            st.experimental_rerun()
