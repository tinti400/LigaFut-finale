# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa da LigaFut", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏆 Copa da LigaFut</h1><hr>", unsafe_allow_html=True)

# 🔄 Buscar times
def buscar_times():
    res = supabase.table("times").select("id, nome, logo").execute()
    return {item["id"]: {"nome": item["nome"], "escudo_url": item.get("logo", "")} for item in res.data}

# 🔄 Buscar rodadas da fase
def buscar_fase(fase, data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("data_criacao", data).order("data_criacao", desc=True).execute()
    return res.data[0]["jogos"] if res.data else []

# 🔄 Buscar grupos
def buscar_grupos(data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", "grupos").eq("data_criacao", data).execute()
    return res.data if res.data else []

# 📊 Cálculo da classificação
def calcular_classificacao(jogos):
    tabela = {}
    for jogo in jogos:
        m, v = jogo["mandante"], jogo["visitante"]
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
        for time_id in [m, v]:
            if time_id not in tabela:
                tabela[time_id] = {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0}
        if gm is None or gv is None:
            continue
        tabela[m]["J"] += 1
        tabela[v]["J"] += 1
        tabela[m]["GP"] += gm
        tabela[v]["GP"] += gv
        tabela[m]["GC"] += gv
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
    for time_id in tabela:
        tabela[time_id]["SG"] = tabela[time_id]["GP"] - tabela[time_id]["GC"]
    df = pd.DataFrame.from_dict(tabela, orient="index")
    df["Time"] = df.index.map(lambda x: times[x]["nome"] if x in times else x)
    df["Logo"] = df.index.map(lambda x: f"<img src='{times[x]['escudo_url']}' width='20'>" if x in times else "")
    df = df[["Time", "Logo", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
    df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
    return df

# 🎨 Exibe o card do confronto
def exibir_card(jogo):
    id_m = jogo.get("mandante")
    id_v = jogo.get("visitante")
    gm = jogo.get("gols_mandante")
    gv = jogo.get("gols_visitante")
    placar = f"{gm} x {gv}" if gm is not None and gv is not None else "? x ?"
    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})

    st.markdown(f"""
    <div style='background:#f9f9f9;padding:10px;border-radius:10px;margin-bottom:10px;border:1px solid #ccc'>
        <div style='display:flex;justify-content:space-between;align-items:center;'>
            <div style='text-align:center;width:40%'>
                <img src='{mandante["escudo_url"]}' width='40'><br>{mandante["nome"]}
            </div>
            <div style='width:20%;text-align:center;font-size:18px;font-weight:bold'>{placar}</div>
            <div style='text-align:center;width:40%'>
                <img src='{visitante["escudo_url"]}' width='40'><br>{visitante["nome"]}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 🧠 Inicialização
times = buscar_times()
res_data = supabase.table("copa_ligafut").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
data_atual = res_data.data[0]["data_criacao"] if res_data.data else None

# 📈 CLASSIFICAÇÃO FINAL DOS GRUPOS
st.subheader("📊 Classificação Final da Fase de Grupos")
grupos = buscar_grupos(data_atual)
grupos_por_nome = {}

for grupo in grupos:
    nome_grupo = grupo.get("grupo", "?")
    if nome_grupo not in grupos_por_nome:
        grupos_por_nome[nome_grupo] = []
    grupos_por_nome[nome_grupo].extend(grupo.get("jogos", []))

for grupo_nome, jogos in sorted(grupos_por_nome.items()):
    st.markdown(f"### Grupo {grupo_nome}")
    df = calcular_classificacao(jogos)
    def estilo(row): return ['background-color: #d4edda'] * len(row) if row.name < 4 else [''] * len(row)
    st.markdown(df.style.apply(estilo, axis=1).to_html(escape=False, index=False), unsafe_allow_html=True)

# 🏁 FASES MATA-MATA
st.markdown("<hr><h2 style='text-align:center;'>🏁 Fases Eliminatórias</h2><hr>", unsafe_allow_html=True)
fases = {
    "oitavas": "🔸 Oitavas de Final",
    "quartas": "🔹 Quartas de Final",
    "semifinal": "⚔️ Semifinal",
    "final": "🏆 Final"
}

for fase_key, fase_nome in fases.items():
    st.subheader(fase_nome)
    jogos = buscar_fase(fase_key, data_atual)
    if not jogos:
        st.info("Nenhum confronto registrado.")
        continue
    for jogo in jogos:
        exibir_card(jogo)

