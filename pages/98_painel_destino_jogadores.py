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
