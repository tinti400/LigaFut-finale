# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import uuid

# ⚡️ Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Copa LigaFut", layout="wide")
st.title("\U0001f3c6 Copa LigaFut - Mata-mata")

# 🔐 Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👥 Buscar times cadastrados
res_times = supabase.table("times").select("id,nome").execute()
times = res_times.data if res_times.data else []

# 📅 Exibir seleção manual dos times
st.subheader("\U0001f4cb Selecione os times participantes da Copa")
st.caption("Escolha entre 16 e 20 times:")

selected_teams = st.multiselect("Times:", [f"{t['nome']} — {t['id']}" for t in times])

if st.button("✨ Gerar Copa"):
    if len(selected_teams) < 16:
        st.error("❌ É preciso selecionar no mínimo 16 times.")
        st.stop()
    if len(selected_teams) > 20:
        st.error("❌ O limite máximo são 20 times.")
        st.stop()

    time_ids = [t.split(" — ")[-1] for t in selected_teams]
    fase = "oitavas"
    confrontos = []

    if len(time_ids) > 16:
        # Fase preliminar necessária
        num_jogos_pre = len(time_ids) - 16
        fase = "preliminar"
        st.info(f"\u26a0\ufe0f Criando fase preliminar com {num_jogos_pre} jogos")

        times_pre = random.sample(time_ids, num_jogos_pre * 2)
        restantes = list(set(time_ids) - set(times_pre))

        random.shuffle(times_pre)
        for i in range(0, len(times_pre), 2):
            confrontos.append({
                "mandante": times_pre[i],
                "visitante": times_pre[i+1],
                "gols_mandante": None,
                "gols_visitante": None
            })

        supabase.table("copa_ligafut").insert({
            "id": str(uuid.uuid4()),
            "numero": 1,
            "fase": "preliminar",
            "jogos": confrontos,
            "data_criacao": datetime.utcnow()
        }).execute()

        st.success("✅ Fase preliminar criada com sucesso!")
        st.stop()

    else:
        # Gerar oitavas diretamente
        random.shuffle(time_ids)
        for i in range(0, len(time_ids), 2):
            confrontos.append({
                "mandante": time_ids[i],
                "visitante": time_ids[i+1],
                "gols_mandante": None,
                "gols_visitante": None
            })

        supabase.table("copa_ligafut").insert({
            "id": str(uuid.uuid4()),
            "numero": 1,
            "fase": "oitavas",
            "jogos": confrontos,
            "data_criacao": datetime.utcnow()
        }).execute()

        st.success("✅ Copa criada com sucesso!")

# 🔢 Exibir última rodada criada
res = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
jogos = res.data[0]["jogos"] if res.data else []
fase = res.data[0]["fase"] if res.data else ""

st.subheader("\U0001f4c5 Últimos Confrontos Gerados")
mapa = {t['id']: t['nome'] for t in times}

for jogo in jogos:
    mandante = mapa.get(jogo["mandante"], "Desconhecido")
    visitante = mapa.get(jogo["visitante"], "Desconhecido")
    st.markdown(f"\U0001f537 **{mandante}** x **{visitante}**")


