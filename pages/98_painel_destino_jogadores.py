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
    with st.container():
        cols = st.columns([1, 3, 2, 2, 2, 2])

        cols[0].image(jogador["imagem_url"], width=80)
        cols[1].markdown(f"**{jogador['nome']}**\n`{jogador['posicao']}` — {jogador['nacionalidade']}")

        novo_valor = cols[2].number_input("💰 Valor:", value=int(jogador["valor"]), step=1000000, key=f"val_{jogador['id']}")
        cols[3].markdown(f"🎯 Destino: `{jogador['destino']}`")

        if "sofifa_id" in jogador and jogador["sofifa_id"]:
            cols[4].markdown(f"📎 [Ficha Técnica](https://sofifa.com/player/{jogador['sofifa_id']}/)")
        else:
            cols[4].markdown("📎 Ficha Técnica não disponível")

        status_cor = {
            "disponivel": "🟢",
            "leilao": "🟡",
            "mercado": "🔵",
            "atribuidotime": "🔴"
        }.get(jogador["destino"], "⚪")

        cols[5].markdown(f"{status_cor} Status")

        # Botões de ação
        bcols = st.columns([2, 2, 3, 2])

        if jogador["destino"] == "mercado":
            if bcols[0].button("🛒 Mandar p/ Mercado", key=f"mercado_{jogador['id']}"):
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                st.success(f"{jogador['nome']} enviado ao mercado com sucesso!")

        elif jogador["destino"] == "leilao":
            if bcols[0].button("📢 Mandar p/ Leilão", key=f"leilao_{jogador['id']}"):
                supabase.table("leiloes").insert({
                    "nome_jogador": jogador["nome"],
                    "posicao_jogador": jogador["posicao"],
                    "overall_jogador": jogador["overall"],
                    "valor_inicial": novo_valor,
                    "valor_atual": novo_valor,
                    "incremento_minimo": 3000000,
                    "inicio": None,
                    "fim": None,
                    "ativo": False,
                    "finalizado": False,
                    "origem": jogador.get("origem", ""),
                    "nacionalidade": jogador.get("nacionalidade", ""),
                    "imagem_url": jogador.get("imagem_url", ""),
                    "link_sofifa": jogador.get("link_sofifa", ""),
                    "enviado_bid": False,
                    "validado": False,
                    "aguardando_validacao": False,
                    "tempo_minutos": 2,
                    "id_time_atual": None
                }).execute()
                st.success(f"{jogador['nome']} enviado à fila de leilão.")

        nome_time = bcols[2].selectbox("👔 Atribuir a:", list(mapa_times.keys()), key=f"time_{jogador['id']}")
        if bcols[3].button("✅ Atribuir", key=f"atr_{jogador['id']}"):
            id_time = mapa_times[nome_time]
            supabase.table("elenco").insert({
                "id_time": id_time,
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador["imagem_url"]
            }).execute()
            supabase.table("jogadores_base").update({"destino": "atribuidotime", "valor": novo_valor}).eq("id", jogador["id"]).execute()
            st.success(f"✅ {jogador['nome']} atribuído ao {nome_time} com sucesso!")
            st.experimental_rerun()
