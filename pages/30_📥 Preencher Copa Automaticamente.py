# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Preencher Participantes da Copa", layout="centered")
st.title("📥 Preencher automaticamente os times da Copa")

# 🔎 Buscar todos os jogos da tabela copa_ligafut
res = supabase.table("copa_ligafut").select("jogos").execute()
rodadas = res.data

if not rodadas:
    st.warning("⚠️ Nenhum jogo encontrado na tabela 'copa_ligafut'.")
    st.stop()

# 📦 Coletar todos os IDs únicos de times (mandantes e visitantes)
ids_times = set()
for rodada in rodadas:
    for jogo in rodada.get("jogos", []):
        mandante = jogo.get("mandante")
        visitante = jogo.get("visitante")
        if mandante:
            ids_times.add(mandante)
        if visitante:
            ids_times.add(visitante)

if not ids_times:
    st.warning("⚠️ Nenhum time encontrado nos jogos.")
    st.stop()

# 🎯 Verificar quem já está na tabela copa
res_cadastrados = supabase.table("copa").select("id_time").execute()
ids_ja_cadastrados = {item["id_time"] for item in res_cadastrados.data}

# 🚀 Inserir os que ainda não estão
novos = 0
for id_time in ids_times:
    if id_time not in ids_ja_cadastrados:
        supabase.table("copa").insert({
            "id_time": id_time,
            "fase_alcancada": "grupos"
        }).execute()
        novos += 1

st.success(f"✅ {novos} times inseridos com sucesso na tabela 'copa'.")
