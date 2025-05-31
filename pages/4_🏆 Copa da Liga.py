# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
from collections import defaultdict

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa da LigaFut", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏆 Copa da LigaFut - Chaveamento</h1><hr>", unsafe_allow_html=True)

# 🔄 Buscar times atualizados
def buscar_times():
    res = supabase.table("times").select("id, nome, logo").execute()
    return {
        item["id"]: {
            "nome": item["nome"],
            "escudo_url": item.get("logo", "")
        }
        for item in res.data
    }

# 🔄 Buscar data mais recente da copa
def buscar_data_mais_recente():
    res = supabase.table("copa_ligafut").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    if res.data:
        return res.data[0]["data_criacao"]
    return None

# 🔄 Buscar fase da copa pela data
def buscar_fase(fase, data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("data_criacao", data).execute()
    return res.data if res.data else []

# 🔄 Buscar fase de grupos
def buscar_grupos(data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", "grupos").eq("data_criacao", data).execute()
    return res.data if res.data else []

# 🎨 Exibir card de jogo
def exibir_card_grupo(jogo):
    id_m = jogo.get("mandante")
    id_v = jogo.get("visitante")

    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})

    gm = jogo.get("gols_mandante")
    gv = jogo.get("gols_visitante")

    placar = f"{gm} x {gv}" if gm is not None and gv is not None else "? x ?"

    card = f"""
    <div style='
        background:#f0f0f0;
        padding:10px;
        border-radius:8px;
        margin-bottom:8px;
        color:black;
        text-align:center;
        box-shadow:0 0 4px rgba(0,0,0,0.1)'
    >
        <div style='display:flex;align-items:center;justify-content:space-between'>
            <div style='text-align:center;width:40%'>
                <img src='{mandante["escudo_url"]}' width='40'><br>
                <span style='font-size:13px'>{mandante["nome"]}</span>
            </div>
            <div style='width:20%;font-size:18px;font-weight:bold'>{placar}</div>
            <div style='text-align:center;width:40%'>
                <img src='{visitante["escudo_url"]}' width='40'><br>
                <span style='font-size:13px'>{visitante["nome"]}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# 📊 Calcular classificação por grupo
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

    df = pd.DataFrame.from_dict(tabela, orient="index")
    df["Time"] = df.index.map(lambda tid: times.get(tid, {}).get("nome", "?"))
    df = df[["Time", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
    return df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)

# 🔁 Buscar tudo
times = buscar_times()
data_atual = buscar_data_mais_recente()
grupos = buscar_grupos(data_atual)
oitavas = buscar_fase("oitavas", data_atual)
quartas = buscar_fase("quartas", data_atual)
semis = buscar_fase("semifinal", data_atual)
final = buscar_fase("final", data_atual)

# 🧾 Exibir fase de grupos
st.subheader("📊 Fase de Grupos")
grupos_por_nome = {}
for g in grupos:
    nome_grupo = g.get("grupo", "?")
    if nome_grupo not in grupos_por_nome:
        grupos_por_nome[nome_grupo] = []
    grupos_por_nome[nome_grupo].extend(g.get("jogos", []))

cols = st.columns(4)
for idx, (grupo, jogos) in enumerate(sorted(grupos_por_nome.items())):
    with cols[idx % 4]:
        st.markdown(f"### {grupo}")
        for jogo in jogos:
            exibir_card_grupo(jogo)
        st.markdown("### Classificação")
        df_class = calcular_classificacao(jogos)
        st.dataframe(df_class, use_container_width=True)

# 🧾 Exibir mata-mata
def exibir_fase_mata(nome, dados, coluna):
    with coluna:
        st.markdown(f"### {nome}")
        for rodada in dados:
            for jogo in rodada.get("jogos", []):
                exibir_card_grupo(jogo)

st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏁 Fase Mata-Mata")
col1, col2, col3, col4 = st.columns(4)
exibir_fase_mata("Oitavas", oitavas, col1)
exibir_fase_mata("Quartas", quartas, col2)
exibir_fase_mata("Semifinal", semis, col3)
exibir_fase_mata("Final", final, col4)

# 🏆 Campeão
st.markdown("### 🏆 Campeão")
if final and final[0].get("jogos"):
    jogo_final = final[0]["jogos"][0]
    gm = jogo_final.get("gols_mandante")
    gv = jogo_final.get("gols_visitante")
    if gm is not None and gv is not None:
        vencedor_id = jogo_final["mandante"] if gm > gv else jogo_final["visitante"]
        vencedor = times.get(vencedor_id, {"nome": "?"})
        st.success(f"🏆 Campeão: **{vencedor['nome']}**")
    else:
        st.info("Final ainda sem placar.")
else:
    st.info("Final ainda não cadastrada.")
