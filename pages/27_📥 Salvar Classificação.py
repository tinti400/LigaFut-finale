# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Classificação Final", layout="centered")
st.title("📥 Salvar Classificação e Estatísticas da LigaFut")

divisao = st.selectbox("Selecione a divisão:", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"
tabela_classificacao = f"classificacao_{numero_divisao}_divisao"

usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute().data
time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
res_times = supabase.table("times").select("id", "nome").in_("id", time_ids).execute().data
times_map = {t["id"]: t["nome"] for t in res_times}

res_rodadas = supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

tabela = {}

for rodada in res_rodadas:
    for jogo in rodada.get("jogos", []):
        m = jogo.get("mandante")
        v = jogo.get("visitante")
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")
        if None in [m, v, gm, gv]:
            continue
        for t in [m, v]:
            if t not in tabela:
                tabela[t] = {"v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "p": 0}

        tabela[m]["gp"] += gm
        tabela[m]["gc"] += gv
        tabela[v]["gp"] += gv
        tabela[v]["gc"] += gm

        if gm > gv:
            tabela[m]["v"] += 1
            tabela[v]["d"] += 1
            tabela[m]["p"] += 3
        elif gv > gm:
            tabela[v]["v"] += 1
            tabela[m]["d"] += 1
            tabela[v]["p"] += 3
        else:
            tabela[m]["e"] += 1
            tabela[v]["e"] += 1
            tabela[m]["p"] += 1
            tabela[v]["p"] += 1

ordenado = sorted(tabela.items(), key=lambda x: (x[1]["p"], x[1]["gp"] - x[1]["gc"], x[1]["gp"]), reverse=True)

for posicao, (id_time, dados) in enumerate(ordenado, start=1):
    supabase.table(tabela_classificacao).upsert({
        "id_time": id_time,
        "posicao_final": posicao
    }).execute()

    supabase.table("estatisticas").upsert({
        "id_time": id_time,
        "vitorias": dados["v"],
        "empates": dados["e"],
        "gols_pro": dados["gp"],
        "gols_contra": dados["gc"]
    }).execute()

st.success("✅ Classificação e estatísticas salvas com sucesso!")
