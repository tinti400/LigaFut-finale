# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import uuid

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Copa LigaFut", layout="wide")
st.title("🏆 Copa LigaFut - Mata-mata")

# 🔒 Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Buscar times
res_times = supabase.table("times").select("id,nome").execute()
times = res_times.data if res_times.data else []
mapa_times = {t['id']: t['nome'] for t in times}

# 🔘 Etapa 1 – Selecionar times para a Copa
st.subheader("📋 Selecione os times participantes da Copa")
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
    confrontos = []

    if len(time_ids) > 16:
        fase = "preliminar"
        num_jogos_pre = len(time_ids) - 16
        st.info(f"⚠️ Criando fase preliminar com {num_jogos_pre} jogos")

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
            "data_criacao": datetime.utcnow().isoformat()
        }).execute()

        st.success("✅ Fase preliminar criada com sucesso!")
        st.rerun()

    else:
        fase = "oitavas"
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
            "data_criacao": datetime.utcnow().isoformat()
        }).execute()

        st.success("✅ Copa criada com sucesso!")
        st.rerun()

# 🔍 Exibir e editar resultados das fases existentes
res_fases = supabase.table("copa_ligafut").select("*").order("numero").execute()
if res_fases.data:
    st.subheader("📝 Editar Resultados das Fases")
    fases_disponiveis = [f"{f['numero']} - {f['fase']}" for f in res_fases.data]
    fase_escolhida = st.selectbox("Selecione a fase para editar", fases_disponiveis)
    numero_fase = int(fase_escolhida.split(" - ")[0])
    fase_dados = next(f for f in res_fases.data if f["numero"] == numero_fase)
    jogos = fase_dados["jogos"]

    for jogo in jogos:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        nome_m = mapa_times.get(mandante, mandante)
        nome_v = mapa_times.get(visitante, visitante)

        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            st.markdown(f"**{nome_m}**")
        with col3:
            st.markdown("**x**")
        with col5:
            st.markdown(f"**{nome_v}**")

        with col2:
            gm = st.number_input(" ", min_value=0, value=0 if jogo["gols_mandante"] is None else jogo["gols_mandante"], key=f"gm_{numero_fase}_{mandante}_{visitante}")
        with col4:
            gv = st.number_input("  ", min_value=0, value=0 if jogo["gols_visitante"] is None else jogo["gols_visitante"], key=f"gv_{numero_fase}_{visitante}_{mandante}")

        if st.button("📂 Salvar", key=f"salvar_{numero_fase}_{mandante}_{visitante}"):
            novos_jogos = []
            for j in jogos:
                if j["mandante"] == mandante and j["visitante"] == visitante:
                    j["gols_mandante"] = gm
                    j["gols_visitante"] = gv
                novos_jogos.append(j)

            supabase.table("copa_ligafut").update({"jogos": novos_jogos}).eq("numero", numero_fase).execute()
            st.success(f"✅ Resultado salvo: {nome_m} {gm} x {gv} {nome_v}")
            st.experimental_rerun()

# 📺 Exibir últimos confrontos criados
res_ult = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
if res_ult.data:
    st.subheader("📅 Últimos Confrontos Gerados")
    ult = res_ult.data[0]
    for jogo in ult["jogos"]:
        mandante = mapa_times.get(jogo["mandante"], "Desconhecido")
        visitante = mapa_times.get(jogo["visitante"], "Desconhecido")
        st.markdown(f"🔹 **{mandante}** x **{visitante}**")


