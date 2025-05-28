# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import uuid

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Copa LigaFut", layout="wide")
st.title("🏆 Copa LigaFut - Mata-mata (Ida e Volta)")

# 🔐 Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👥 Buscar times cadastrados
res_times = supabase.table("times").select("id,nome").execute()
times = res_times.data if res_times.data else []
mapa_times = {t['id']: t['nome'] for t in times}

# 🗓️ Selecionar times
st.subheader("📌 Selecione os times participantes da Copa")
st.caption("Escolha exatamente 19 times para este formato:")

selected_teams = st.multiselect("Times:", [f"{t['nome']} — {t['id']}" for t in times])

if st.button("✨ Gerar Copa"):
    if len(selected_teams) != 19:
        st.error("❌ Este formato exige exatamente 19 times.")
        st.stop()

    time_ids = [t.split(" — ")[-1] for t in selected_teams]
    fase = "preliminar"
    confrontos = []

    # Seleciona 6 times para a preliminar
    times_preliminar = random.sample(time_ids, 6)
    times_classificados = list(set(time_ids) - set(times_preliminar))

    # Gera 3 confrontos na preliminar
    random.shuffle(times_preliminar)
    for i in range(0, 6, 2):
        confrontos.append({
            "mandante_ida": times_preliminar[i],
            "visitante_ida": times_preliminar[i+1],
            "gols_ida_m": None,
            "gols_ida_v": None,
            "gols_volta_m": None,
            "gols_volta_v": None
        })

    supabase.table("copa_ligafut").insert({
        "id": str(uuid.uuid4()),
        "numero": 1,
        "fase": fase,
        "jogos": confrontos,
        "data_criacao": datetime.utcnow().isoformat()
    }).execute()

    st.success("✅ Fase preliminar criada com sucesso!")
    st.experimental_rerun()

# 🗒️ Exibir confrontos + edição dos resultados
res = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
doc = res.data[0] if res.data else {}
if not doc:
    st.stop()

jogos = doc.get("jogos", [])
fase = doc.get("fase", "")
st.subheader(f"📅 Confrontos da Fase: {fase.upper()}")

classificados = []

for i, jogo in enumerate(jogos):
    id_m = jogo.get("mandante_ida")
    id_v = jogo.get("visitante_ida")
    nome_m = mapa_times.get(id_m, f"? ({id_m})")
    nome_v = mapa_times.get(id_v, f"? ({id_v})")

    st.markdown(f"### {nome_m} x {nome_v}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ida_m = st.number_input("Gols Ida (Mandante)", min_value=0, value=jogo.get("gols_ida_m") or 0, key=f"im_{i}")
    with col2:
        ida_v = st.number_input("Gols Ida (Visitante)", min_value=0, value=jogo.get("gols_ida_v") or 0, key=f"iv_{i}")
    with col3:
        volta_m = st.number_input("Gols Volta (Visitante)", min_value=0, value=jogo.get("gols_volta_m") or 0, key=f"vm_{i}")
    with col4:
        volta_v = st.number_input("Gols Volta (Mandante)", min_value=0, value=jogo.get("gols_volta_v") or 0, key=f"vv_{i}")

    total_m = ida_m + volta_v
    total_v = ida_v + volta_m
    resultado = f"{total_m} x {total_v}"

    if total_m > total_v:
        st.success(f"✅ {nome_m} classificado ({resultado})")
        classificados.append(id_m)
    elif total_v > total_m:
        st.success(f"✅ {nome_v} classificado ({resultado})")
        classificados.append(id_v)
    else:
        st.warning(f"⚠️ Empate no agregado: {resultado} - Definir vencedor por pênaltis")

    if st.button("Salvar Resultado", key=f"btn_{i}"):
        jogo.update({
            "gols_ida_m": ida_m,
            "gols_ida_v": ida_v,
            "gols_volta_m": volta_m,
            "gols_volta_v": volta_v
        })
        supabase.table("copa_ligafut").update({"jogos": jogos}).eq("id", doc["id"]).execute()
        st.success("✅ Resultado atualizado com sucesso!")
        st.experimental_rerun()

# Avançar de fase manualmente
if len(classificados) == len(jogos):
    if st.button("➡️ Avançar para próxima fase"):
        nova_fase = {
            "preliminar": "oitavas",
            "oitavas": "quartas",
            "quartas": "semifinal",
            "semifinal": "final",
            "final": "encerrado"
        }.get(fase, "encerrado")

        if nova_fase == "encerrado":
            st.success("🏆 Copa encerrada!")
        else:
            if fase == "preliminar":
                classificados += times_classificados

            random.shuffle(classificados)
            novos_jogos = []
            for i in range(0, len(classificados), 2):
                novos_jogos.append({
                    "mandante_ida": classificados[i],
                    "visitante_ida": classificados[i+1],
                    "gols_ida_m": None,
                    "gols_ida_v": None,
                    "gols_volta_m": None,
                    "gols_volta_v": None
                })

            supabase.table("copa_ligafut").insert({
                "id": str(uuid.uuid4()),
                "numero": doc["numero"] + 1,
                "fase": nova_fase,
                "jogos": novos_jogos,
                "data_criacao": datetime.utcnow().isoformat()
            }).execute()

            st.success(f"✅ Fase '{nova_fase.upper()}' criada com sucesso!")
            st.experimental_rerun()
