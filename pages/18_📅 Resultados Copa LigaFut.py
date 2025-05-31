# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📅 Resultados Fase de Grupos", layout="wide")
st.title("📅 Fase de Grupos - Resultados")

# ✅ Verifica login
dados_sessao = st.session_state
if "usuario_id" not in dados_sessao:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# ⚡️ Verifica se é administrador
email_usuario = dados_sessao.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if len(admin_ref.data) == 0:
    st.warning("⛔️ Acesso restrito aos administradores.")
    st.stop()

# ⏲️ Data da copa mais recente
def buscar_data_recente():
    res = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    return res.data[0]["data_criacao"] if res.data else None

data_atual = buscar_data_recente()
if not data_atual:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# 🔄 Buscar times (id e nome)
def buscar_times():
    res = supabase.table("times").select("id, nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

times = buscar_times()

# 🔢 Buscar jogos da fase de grupos
res = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual).execute()
grupo_data = res.data if res.data else []

if not grupo_data:
    st.info("A fase de grupos ainda não foi gerada.")
    st.stop()

# 📈 Função para calcular classificação
from collections import defaultdict

def calcular_classificacao(jogos):
    tabela = defaultdict(lambda: {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0})
    for jogo in jogos:
        m = jogo.get("mandante")
        v = jogo.get("visitante")
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")
        if None in (m, v, gm, gv):
            continue

        tabela[m]["J"] += 1
        tabela[v]["J"] += 1
        tabela[m]["GP"] += gm
        tabela[m]["GC"] += gv
        tabela[v]["GP"] += gv
        tabela[v]["GC"] += gm

        if gm > gv:
            tabela[m]["V"] += 1
            tabela[v]["D"] += 1
            tabela[m]["P"] += 3
        elif gv > gm:
            tabela[v]["V"] += 1
            tabela[m]["D"] += 1
            tabela[v]["P"] += 3
        else:
            tabela[m]["E"] += 1
            tabela[v]["E"] += 1
            tabela[m]["P"] += 1
            tabela[v]["P"] += 1

    for t in tabela:
        tabela[t]["SG"] = tabela[t]["GP"] - tabela[t]["GC"]
    return tabela

# 🏋️ Interface para editar jogos por grupo
grupos = sorted(set([g["grupo"] for g in grupo_data]))

tab = st.selectbox("Escolha o grupo para editar resultados:", grupos)

grupo_jogos = next((g for g in grupo_data if g["grupo"] == tab), None)
if not grupo_jogos:
    st.error("Grupo não encontrado.")
    st.stop()

jogos = grupo_jogos.get("jogos", [])

st.markdown(f"### Jogos do Grupo {tab}")

novo_resultado = []
for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        mandante = times.get(jogo["mandante"], "?")
        visitante = times.get(jogo["visitante"], "?")
        st.write(mandante)
    with col2:
        gols_m = st.number_input("Gols M", min_value=0, value=jogo.get("gols_mandante") or 0, key=f"gm_{idx}")
    with col3:
        st.write("x")
    with col4:
        gols_v = st.number_input("Gols V", min_value=0, value=jogo.get("gols_visitante") or 0, key=f"gv_{idx}")
    with col5:
        st.write(visitante)

    novo_resultado.append({
        "mandante": jogo["mandante"],
        "visitante": jogo["visitante"],
        "gols_mandante": gols_m,
        "gols_visitante": gols_v
    })

if st.button("✅ Salvar Resultados"):
    try:
        supabase.table("copa_ligafut").update({"jogos": novo_resultado}).eq("grupo", tab).eq("data_criacao", data_atual).execute()
        st.success("Resultados atualizados com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# 📊 Classificação
st.markdown(f"### 📊 Classificação do Grupo {tab}")
tabela = calcular_classificacao(novo_resultado)

import pandas as pd

df = pd.DataFrame.from_dict(tabela, orient="index")
df["Time"] = df.index.map(lambda tid: times.get(tid, "?"))
df = df[["Time", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)

st.dataframe(df, use_container_width=True)
