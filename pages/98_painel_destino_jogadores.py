# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Definir Destino dos Jogadores", layout="wide")
st.title("🎯 Painel de Destino dos Jogadores")

# 🎯 Legenda
st.markdown("### 🟢 Disponível  |  🟡 Leilão  |  🔵 Mercado  |  🔴 Atribuído a Time")

# 🧩 Buscar times
res_times = supabase.table("times").select("id", "nome").execute()
mapa_times = {t["nome"]: t["id"] for t in res_times.data}

# 🔎 Buscar todos os jogadores
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

if not jogadores:
    st.info("✅ Nenhum jogador cadastrado.")
    st.stop()

# Função para cor do status
def cor_destino(destino):
    if destino == "nenhum":
        return "🟢"
    elif destino == "leilao":
        return "🟡"
    elif destino == "mercado":
        return "🔵"
    else:
        return "🔴"

# 🔁 Mostrar jogadores
for jogador in jogadores:
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 2.5, 2, 2, 2])

        # 📸 Imagem + status
        with col1:
            if jogador.get("imagem_url"):
                st.image(jogador["imagem_url"], width=60)
            st.markdown(cor_destino(jogador.get("destino", "nenhum")))

        # ℹ️ Info jogador
        with col2:
            st.markdown(f"**{jogador['nome']}**")
            st.caption(f"📍 {jogador['posicao']} | ⭐ Overall: {jogador['overall']}")
            valor_editado = st.number_input("💰 Valor (editável)", value=int(jogador["valor"]), step=1_000_000, key=f"val_{jogador['id']}")

        # 🛒 Mercado
        with col3:
            if st.button("🛒 Mandar p/ Mercado", key=f"mercado_{jogador['id']}"):
                ja_no_mercado = supabase.table("mercado_transferencias").select("id").eq("id_jogador_base", jogador["id"]).execute()
                if ja_no_mercado.data:
                    st.warning("⚠️ Já está no mercado.")
                else:
                    supabase.table("mercado_transferencias").insert({
                        "id_jogador_base": jogador["id"],
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": valor_editado,
                        "imagem_url": jogador["imagem_url"],
                        "nacionalidade": jogador.get("nacionalidade", ""),
                        "clube_original": jogador.get("clube_original", "")
                    }).execute()
                    supabase.table("jogadores_base").update({"destino": "mercado", "valor": valor_editado}).eq("id", jogador["id"]).execute()
                    st.success("✅ Enviado ao mercado.")
                    st.experimental_rerun()

        # 📢 Leilão
        with col4:
            if st.button("📢 Mandar p/ Leilão", key=f"leilao_{jogador['id']}"):
                ja_na_fila = supabase.table("fila_leilao").select("id").eq("id_jogador_base", jogador["id"]).execute()
                if ja_na_fila.data:
                    st.warning("⚠️ Já está na fila.")
                else:
                    supabase.table("fila_leilao").insert({
                        "id_jogador_base": jogador["id"],
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": valor_editado,
                        "imagem_url": jogador["imagem_url"],
                        "status": "aguardando"
                    }).execute()
                    supabase.table("jogadores_base").update({"destino": "leilao", "valor": valor_editado}).eq("id", jogador["id"]).execute()
                    st.success("✅ Enviado para o leilão.")
                    st.experimental_rerun()

        # ✅ Atribuir a time
        with col5:
            nome_time = st.selectbox("👔 Time", options=list(mapa_times.keys()), key=f"time_{jogador['id']}")
            if st.button("✅ Atribuir a Time", key=f"atribuir_{jogador['id']}"):
                id_time = mapa_times[nome_time]
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": valor_editado,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": nome_time, "valor": valor_editado}).eq("id", jogador["id"]).execute()
                st.success(f"✅ Atribuído ao time {nome_time}")
                st.experimental_rerun()
# 20_🔧 Admin Leilao.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

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

# 🎯 FILTROS
st.markdown("### 🎯 Filtros")
col1, col2, col3 = st.columns(3)

with col1:
    filtro_nome = st.text_input("🔠 Nome do jogador")

with col2:
    overall_min = st.number_input("🔻 Overall mínimo", min_value=0, max_value=99, value=0)
    overall_max = st.number_input("🔺 Overall máximo", min_value=0, max_value=99, value=99)

with col3:
    nacionalidades_disponiveis = sorted(list(set([j.get("nacionalidade", "") for j in jogadores if j.get("nacionalidade")])))
    filtro_nacionalidade = st.selectbox("🌍 Nacionalidade", ["Todas"] + nacionalidades_disponiveis)

# Aplicar filtros
jogadores_filtrados = []
for j in jogadores:
    if filtro_nome.lower() in j["nome"].lower() and overall_min <= j["overall"] <= overall_max:
        if filtro_nacionalidade == "Todas" or j.get("nacionalidade", "") == filtro_nacionalidade:
            jogadores_filtrados.append(j)

if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

# 🧩 Exibição
for jogador in jogadores_filtrados:
    with st.container(border=True):
        cols = st.columns([1, 3, 2, 2, 2, 2])

        cols[0].image(jogador["imagem_url"], width=80)
        cols[1].markdown(f"**{jogador['nome']}**\n`{jogador['posicao']}` — {jogador.get('nacionalidade', 'N/A')}")
        cols[2].markdown(f"💰 Valor: R$ {int(jogador['valor']):,}".replace(",", "."))
        cols[3].markdown(f"🎯 Overall: `{jogador['overall']}`")

        cor_status = {
            "disponivel": "🟢",
            "leilao": "🟡",
            "mercado": "🔵",
        }.get(jogador["destino"], "🔴")
        cols[4].markdown(f"Status: {cor_status} `{jogador['destino']}`")

        if "sofifa_id" in jogador and jogador["sofifa_id"]:
            cols[5].markdown(f"📎 [Ficha Técnica](https://sofifa.com/player/{jogador['sofifa_id']}/)")
        else:
            cols[5].markdown("📎 Ficha Técnica não disponível")

        st.divider()
        col_valor, col_mercado, col_leilao = st.columns([3, 2, 2])

        novo_valor = col_valor.number_input("💰 Editar valor:", value=int(jogador["valor"]), step=1000000, key=f"val_{jogador['id']}")

        if col_mercado.button("🛒 Mandar para o Mercado", key=f"merc_{jogador['id']}"):
            supabase.table("mercado_transferencias").insert({
                "uuid": jogador.get("uuid", jogador["id"]),
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador["imagem_url"]
            }).execute()
            supabase.table("jogadores_base").update({"destino": "mercado", "valor": novo_valor}).eq("id", jogador["id"]).execute()
            st.success(f"{jogador['nome']} enviado ao mercado com sucesso!")
            st.experimental_rerun()

        if col_leilao.button("📢 Mandar para o Leilão", key=f"leil_{jogador['id']}"):
            supabase.table("fila_leilao").insert({
                "uuid": jogador.get("uuid", jogador["id"]),
                "valor": novo_valor,
                "imagem_url": jogador["imagem_url"],
                "status": "aguardando",
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"]
            }).execute()
            supabase.table("jogadores_base").update({"destino": "leilao", "valor": novo_valor}).eq("id", jogador["id"]).execute()
            st.success(f"{jogador['nome']} enviado à fila do leilão.")
            st.experimental_rerun()

        # Atribuição manual a um time
        st.markdown("---")
        col_time, col_botao = st.columns([4, 2])
        nome_time = col_time.selectbox("👔 Atribuir a: ", list(mapa_times.keys()), key=f"time_{jogador['id']}")

        if col_botao.button("✅ Atribuir", key=f"atr_{jogador['id']}"):
            id_time = mapa_times[nome_time]
            supabase.table("elenco").insert({
                "id_time": id_time,
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": novo_valor,
                "imagem_url": jogador["imagem_url"]
            }).execute()
            supabase.table("jogadores_base").update({"destino": nome_time, "valor": novo_valor}).eq("id", jogador["id"]).execute()
            st.success(f"✅ {jogador['nome']} atribuído ao {nome_time} com sucesso!")
            st.experimental_rerun()
