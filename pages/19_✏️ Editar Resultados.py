# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerenciar Rodadas", page_icon="🏕️", layout="centered")
st.title("🏕️ Gerenciar Resultados das Rodadas")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = len(admin_ref.data) > 0
if not eh_admin:
    st.error("🔒 Acesso restrito: apenas administradores.")
    st.stop()

# 🔽 Seleção da divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Selecione a Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])

numero_divisao = divisao.split()[-1]
numero_temporada = temporada.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}_temp{numero_temporada}"

# 📌 Buscar times da divisão
def obter_times(divisao):
    res = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute()
    return [u["time_id"] for u in res.data if u.get("time_id")]

def obter_nomes_times():
    res = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

# 🔎 Rodadas existentes
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

# 🔁 Buscar dados
rodadas_existentes = buscar_rodadas()
times_map = obter_nomes_times()

if rodadas_existentes:
    st.subheader("📅 Editar Resultados")
    numeros = [r["numero"] for r in rodadas_existentes]
    rodada_escolhida = st.selectbox("Escolha a rodada", numeros)
    rodada = next(r for r in rodadas_existentes if r["numero"] == rodada_escolhida)

    # 🔍 Filtro por equipe (dentro da rodada)
    times_disponiveis = list({j["mandante"] for j in rodada["jogos"]} | {j["visitante"] for j in rodada["jogos"]})
    nomes_times_filtrados = {id_: nome for id_, nome in times_map.items() if id_ in times_disponiveis}
    nome_filtrado = st.selectbox("🔎 Filtrar por equipe da rodada", ["Todos"] + list(nomes_times_filtrados.values()))

    for idx, jogo in enumerate(rodada["jogos"]):
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        gols_mandante = jogo.get("gols_mandante") or 0
        gols_visitante = jogo.get("gols_visitante") or 0

        nome_m = times_map.get(mandante, "FOLGA" if mandante == "FOLGA" else "?")
        nome_v = times_map.get(visitante, "FOLGA" if visitante == "FOLGA" else "?")

        if nome_filtrado != "Todos" and nome_filtrado not in [nome_m, nome_v]:
            continue

        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 0.5, 1.5, 2])
        with col1:
            st.markdown(f"**{nome_m}**")
        with col2:
            gm = st.number_input(f"Gols {nome_m}", min_value=0, value=gols_mandante, key=f"gm_{idx}")
        with col3:
            st.markdown("**X**")
        with col4:
            gv = st.number_input(f"Gols {nome_v}", min_value=0, value=gols_visitante, key=f"gv_{idx}")
        with col5:
            st.markdown(f"**{nome_v}**")

        if "FOLGA" in [mandante, visitante]:
            st.info("⚠️ Time folgando.")
            continue

        if st.button("📂 Salvar Resultado", key=f"salvar_{idx}"):
            novos_jogos = []
            for j in rodada["jogos"]:
                if j["mandante"] == mandante and j["visitante"] == visitante:
                    j["gols_mandante"] = gm
                    j["gols_visitante"] = gv
                novos_jogos.append(j)

            supabase.table(nome_tabela_rodadas).update({"jogos": novos_jogos}).eq("numero", rodada_escolhida).execute()
            st.success(f"✅ Resultado salvo: {nome_m} {gm} x {gv} {nome_v}")
            st.rerun()

# 📍 Filtro global de jogos por equipe
st.subheader("🔎 Buscar Jogos de uma Equipe (todas as rodadas)")

nomes_ordenados = {v: k for k, v in times_map.items()}
time_selecionado = st.selectbox("Selecione o time", sorted(nomes_ordenados.keys()))

if time_selecionado:
    id_time = nomes_ordenados[time_selecionado]
    jogos_encontrados = []

    for rodada in rodadas_existentes:
        numero = rodada["numero"]
        for jogo in rodada["jogos"]:
            if id_time in [jogo["mandante"], jogo["visitante"]]:
                nome_m = times_map.get(jogo["mandante"], "?")
                nome_v = times_map.get(jogo["visitante"], "?")
                g_m = jogo.get("gols_mandante")
                g_v = jogo.get("gols_visitante")

                placar = f"{g_m} x {g_v}" if g_m is not None and g_v is not None else "⚠️ Sem resultado"

                jogos_encontrados.append({
                    "Rodada": numero,
                    "Mandante": nome_m,
                    "Visitante": nome_v,
                    "Placar": placar
                })

    if jogos_encontrados:
        df = pd.DataFrame(jogos_encontrados).sort_values("Rodada")
        st.table(df)
    else:
        st.info("❌ Nenhum jogo encontrado para esse time.")
