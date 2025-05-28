# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="⚽ Copa LigaFut", layout="centered")
st.title("\U0001f3c6 Copa LigaFut - Resultados")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📅 Buscar fase atual da copa
res = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
dados_copa = res.data[0] if res.data else {}
fase = dados_copa.get("fase", "")
jogos = dados_copa.get("jogos", [])

# 🔍 Obter nomes dos times
res_times = supabase.table("times").select("id", "nome").execute()
times_map = {t["id"]: t["nome"] for t in res_times.data}

st.subheader(f"⚔️ Resultados da fase: {fase.capitalize()}")
novos_jogos = []

for i, jogo in enumerate(jogos):
    # Verifica o formato do confronto
    if "mandante_ida" in jogo and "visitante_ida" in jogo:
        id_m = jogo["mandante_ida"]
        id_v = jogo["visitante_ida"]
        gols_ida_m = jogo.get("gols_ida_mandante", 0)
        gols_ida_v = jogo.get("gols_ida_visitante", 0)
        gols_volta_m = jogo.get("gols_volta_mandante", 0)
        gols_volta_v = jogo.get("gols_volta_visitante", 0)
    else:
        id_m = jogo["mandante"]
        id_v = jogo["visitante"]
        gols_ida_m = jogo.get("gols_mandante", 0)
        gols_ida_v = jogo.get("gols_visitante", 0)
        gols_volta_m = 0
        gols_volta_v = 0

    nome_m = times_map.get(id_m, "?")
    nome_v = times_map.get(id_v, "?")

    st.markdown(f"**{nome_m} x {nome_v}**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ida_m = st.number_input("Gols ida mandante", min_value=0, value=gols_ida_m, key=f"gm_ida_{i}")
    with col2:
        ida_v = st.number_input("Gols ida visitante", min_value=0, value=gols_ida_v, key=f"gv_ida_{i}")
    with col3:
        volta_m = st.number_input("Gols volta mandante", min_value=0, value=gols_volta_m, key=f"gm_volta_{i}")
    with col4:
        volta_v = st.number_input("Gols volta visitante", min_value=0, value=gols_volta_v, key=f"gv_volta_{i}")

    novos_jogos.append({
        "mandante_ida": id_m,
        "visitante_ida": id_v,
        "gols_ida_mandante": ida_m,
        "gols_ida_visitante": ida_v,
        "gols_volta_mandante": volta_m,
        "gols_volta_visitante": volta_v
    })

if st.button("📉 Salvar Resultados"):
    supabase.table("copa_ligafut").update({"jogos": novos_jogos}).eq("id", dados_copa["id"]).execute()
    st.success("Resultados salvos com sucesso!")
    st.rerun()

