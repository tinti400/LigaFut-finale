# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="🏆 Copa da Liga", layout="wide")
st.title("🏆 Copa da Liga")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

id_time = st.session_state["id_time"]
email_usuario = st.session_state.get("usuario", "")

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

# 🔄 Buscar times
res = supabase.table("times").select("id", "nome", "escudo_url").execute()
times = {t["id"]: t for t in res.data}

# 📊 Classificação por grupo
def calcular_classificacao(jogos):
    tabela = {}
    for jogo in jogos:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        gols_mandante = jogo.get("gols_mandante")
        gols_visitante = jogo.get("gols_visitante")

        for time_id in [mandante, visitante]:
            if time_id not in tabela:
                tabela[time_id] = {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0}

        if gols_mandante is None or gols_visitante is None:
            continue

        tabela[mandante]["J"] += 1
        tabela[visitante]["J"] += 1

        tabela[mandante]["GP"] += gols_mandante
        tabela[mandante]["GC"] += gols_visitante
        tabela[visitante]["GP"] += gols_visitante
        tabela[visitante]["GC"] += gols_mandante

        if gols_mandante > gols_visitante:
            tabela[mandante]["V"] += 1
            tabela[visitante]["D"] += 1
            tabela[mandante]["P"] += 3
        elif gols_visitante > gols_mandante:
            tabela[visitante]["V"] += 1
            tabela[mandante]["D"] += 1
            tabela[visitante]["P"] += 3
        else:
            tabela[mandante]["E"] += 1
            tabela[visitante]["E"] += 1
            tabela[mandante]["P"] += 1
            tabela[visitante]["P"] += 1

    for time_id in tabela:
        tabela[time_id]["SG"] = tabela[time_id]["GP"] - tabela[time_id]["GC"]

    df = pd.DataFrame.from_dict(tabela, orient="index")
    df["Time"] = df.index.map(
        lambda x: f"<img src='{times[x]['escudo_url']}' width='20'> {times[x]['nome']}" if x in times else str(x)
    )
    df = df[["Time", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
    df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
    return df

# 🔄 Buscar jogos
res = supabase.table("copa_jogos").select("*").order("grupo", desc=False).execute()
jogos = res.data if res.data else []

# Organizar por grupo
grupos = {}
for jogo in jogos:
    grupo = jogo["grupo"]
    if grupo not in grupos:
        grupos[grupo] = []
    grupos[grupo].append(jogo)

# ⟳ Avançar fase (só ADM)
if is_admin:
    if st.button("➡️ Avançar para Fase Eliminatória"):
        for jogo in jogos:
            supabase.table("copa_jogos_historico").insert(jogo).execute()
        supabase.table("copa_jogos").delete().neq("grupo", "").execute()
        st.success("Fase avançada! Jogos arquivados.")
        st.experimental_rerun()

# Mostrar histórico
res_historico = supabase.table("copa_jogos_historico").select("*").order("grupo", desc=False).execute()
historico = res_historico.data if res_historico.data else []
grupos_historico = {}
for jogo in historico:
    grupo = jogo["grupo"]
    if grupo not in grupos_historico:
        grupos_historico[grupo] = []
    grupos_historico[grupo].append(jogo)

# Exibir fase atual
st.header("📅 Rodadas da Fase de Grupos")
for grupo, jogos in grupos.items():
    st.subheader(f"Grupo {grupo}")
    df = calcular_classificacao(jogos)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Exibir histórico
if historico:
    st.header("🕓 Histórico - Fase de Grupos Anterior")
    for grupo, jogos in grupos_historico.items():
        st.subheader(f"Grupo {grupo}")
        df = calcular_classificacao(jogos)
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
