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
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# ✅ Primeira linha do script
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
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

# 📌 Lista times
res_times = supabase.table("times").select("id", "nome").execute()
times = res_times.data
mapa_times = {t['nome']: t['id'] for t in times}

# 🔍 Filtros
st.sidebar.markdown("### 🎯 Filtros")
filtro_nome = st.sidebar.text_input("🔎 Nome contém:")
filtro_nac = st.sidebar.text_input("🌍 Nacionalidade contém:")
filtro_ovr = st.sidebar.slider("📊 Overall mínimo:", min_value=1, max_value=99, value=1)

jogadores_filtrados = [j for j in jogadores if
    filtro_nome.lower() in j["nome"].lower() and
    filtro_nac.lower() in j.get("nacionalidade", "").lower() and
    int(j["overall"]) >= filtro_ovr
]

if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

# 🧩 Exibição
for jogador in jogadores_filtrados:
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image(jogador["imagem_url"], width=100)
            destino = jogador.get("destino", "disponivel")
            cor = {
                "disponivel": "🟢",
                "leilao": "🟡",
                "mercado": "🔵"
            }.get(destino, "🔴")
            st.markdown(f"{cor} **Status:** `{destino}`")

        with col2:
            st.markdown(f"### {jogador['nome']} ({jogador['posicao']})")
            st.markdown(f"**Overall:** `{jogador['overall']}`")
            st.markdown(f"**Nacionalidade:** {jogador.get('nacionalidade', 'Desconhecida')}")
            st.markdown(f"💰 **Valor Atual:** R$ {int(jogador['valor']):,}".replace(",", "."))
            if jogador.get("sofifa_id"):
                st.markdown(f"[📎 Ficha Técnica](https://sofifa.com/player/{jogador['sofifa_id']})")

            novo_valor = st.number_input("Editar Valor (R$)", value=int(jogador["valor"]), step=500_000, key=f"val_{jogador['id']}")
            if st.button("💾 Salvar Valor", key=f"save_val_{jogador['id']}"):
                supabase.table("jogadores_base").update({"valor": novo_valor}).eq("id", jogador["id"]).execute()
                st.success("Valor atualizado com sucesso!")
                st.experimental_rerun()

            col_a, col_b, col_c = st.columns(3)
            if col_a.button("📤 Mandar pro Mercado", key=f"merc_{jogador['id']}"):
                supabase.table("jogadores_base").update({"destino": "mercado"}).eq("id", jogador["id"]).execute()
                st.success("Jogador enviado ao mercado.")
                st.experimental_rerun()

            if col_b.button("📢 Mandar pro Leilão", key=f"leilao_{jogador['id']}"):
                supabase.table("jogadores_base").update({"destino": "leilao"}).eq("id", jogador["id"]).execute()
                st.success("Jogador enviado à fila do leilão.")
                st.experimental_rerun()

            nome_time = col_c.selectbox("👔 Atribuir a: ", list(mapa_times.keys()), key=f"sb_{jogador['id']}")
            if st.button("✅ Atribuir ao Time", key=f"atr_{jogador['id']}"):
                id_time = mapa_times[nome_time]
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": nome_time}).eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} atribuído ao {nome_time} com sucesso!")
                st.experimental_rerun()
