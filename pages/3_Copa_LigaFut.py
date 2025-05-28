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
        # Fase Preliminar
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
            "data_criacao": datetime.utcnow()
        }).execute()

        st.success("✅ Fase preliminar criada com sucesso!")
        st.rerun()

    else:
        # Oitavas direto
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
            "data_criacao": datetime.utcnow()
        }).execute()

        st.success("✅ Oitavas de final criadas com sucesso!")
        st.rerun()

# 🔍 Verificar se existe fase preliminar pendente
res_pre = supabase.table("copa_ligafut").select("*").eq("fase", "preliminar").order("data_criacao", desc=True).limit(1).execute()
if res_pre.data:
    preliminar = res_pre.data[0]
    jogos = preliminar["jogos"]
    id_rodada = preliminar["id"]

    st.subheader("📝 Inserir Resultados da Fase Preliminar")

    gols_mandante = []
    gols_visitante = []

    for i, jogo in enumerate(jogos):
        col1, col2, col3 = st.columns([4, 1, 4])
        with col1:
            st.write(f"**{mapa_times.get(jogo['mandante'], 'Desconhecido')}**")
        with col2:
            gol_m = st.number_input("Gols", key=f"gm{i}", min_value=0, step=1, value=0 if jogo["gols_mandante"] is None else jogo["gols_mandante"])
            gols_mandante.append(gol_m)
        with col3:
            st.write(f"**{mapa_times.get(jogo['visitante'], 'Desconhecido')}**")
            gol_v = st.number_input("Gols ", key=f"gv{i}", min_value=0, step=1, value=0 if jogo["gols_visitante"] is None else jogo["gols_visitante"])
            gols_visitante.append(gol_v)

    if st.button("💾 Salvar Resultados"):
        for i in range(len(jogos)):
            jogos[i]["gols_mandante"] = gols_mandante[i]
            jogos[i]["gols_visitante"] = gols_visitante[i]

        supabase.table("copa_ligafut").update({"jogos": jogos}).eq("id", id_rodada).execute()
        st.success("✅ Resultados salvos com sucesso!")
        st.rerun()

    if st.button("➡️ Gerar Oitavas de Final"):
        vencedores = []
        for jogo in jogos:
            if jogo["gols_mandante"] is None or jogo["gols_visitante"] is None:
                st.error("⚠️ Preencha todos os resultados antes de gerar as oitavas.")
                st.stop()
            if jogo["gols_mandante"] > jogo["gols_visitante"]:
                vencedores.append(jogo["mandante"])
            else:
                vencedores.append(jogo["visitante"])

        # Identificar os outros que não participaram da preliminar
        todos = set()
        for j in jogos:
            todos.add(j["mandante"])
            todos.add(j["visitante"])
        all_participantes = supabase.table("copa_ligafut").select("jogos").execute()
        envolvidos = set()
        for r in all_participantes.data:
            for j in r["jogos"]:
                envolvidos.add(j["mandante"])
                envolvidos.add(j["visitante"])
        diretos = list(envolvidos - todos)
        ids_oitavas = diretos + vencedores
        random.shuffle(ids_oitavas)

        confrontos_oitavas = []
        for i in range(0, len(ids_oitavas), 2):
            confrontos_oitavas.append({
                "mandante": ids_oitavas[i],
                "visitante": ids_oitavas[i+1],
                "gols_mandante": None,
                "gols_visitante": None
            })

        supabase.table("copa_ligafut").insert({
            "id": str(uuid.uuid4()),
            "numero": 2,
            "fase": "oitavas",
            "jogos": confrontos_oitavas,
            "data_criacao": datetime.utcnow()
        }).execute()

        st.success("✅ Oitavas de final criadas com sucesso!")
        st.rerun()

# 📺 Exibir últimos confrontos criados
res_ult = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
if res_ult.data:
    st.subheader("📅 Últimos Confrontos Gerados")
    ult = res_ult.data[0]
    for jogo in ult["jogos"]:
        mandante = mapa_times.get(jogo["mandante"], "Desconhecido")
        visitante = mapa_times.get(jogo["visitante"], "Desconhecido")
        st.markdown(f"🔹 **{mandante}** x **{visitante}**")


