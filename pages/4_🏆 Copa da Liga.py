# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import random

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

# 🔄 Buscar data mais recente
def buscar_data_mais_recente():
    res = supabase.table("copa_ligafut").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    return res.data[0]["data_criacao"] if res.data else None

# 🔄 Buscar fase
def buscar_fase(fase, data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("data_criacao", data).execute()
    return res.data if res.data else []

# 🔄 Buscar fase de grupos
def buscar_grupos(data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", "grupos").eq("data_criacao", data).execute()
    return res.data if res.data else []

# 🎨 Card visual dos jogos
def exibir_card(jogo):
    id_m, id_v = jogo.get("mandante"), jogo.get("visitante")
    gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})
    placar = f"{gm} x {gv}" if gm is not None and gv is not None else "? x ?"

    card = f"""
    <div style='background:#f0f0f0;padding:10px;border-radius:8px;margin-bottom:8px;
                color:black;text-align:center;box-shadow:0 0 4px rgba(0,0,0,0.1)'>
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

# 📊 Classificação dos grupos
def calcular_classificacao(jogos):
    tabela = {}
    for jogo in jogos:
        m, v = jogo["mandante"], jogo["visitante"]
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
        for t in [m, v]:
            if t not in tabela:
                tabela[t] = {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0}
        if gm is None or gv is None: continue
        tabela[m]["J"] += 1; tabela[v]["J"] += 1
        tabela[m]["GP"] += gm; tabela[m]["GC"] += gv
        tabela[v]["GP"] += gv; tabela[v]["GC"] += gm
        if gm > gv:
            tabela[m]["V"] += 1; tabela[v]["D"] += 1; tabela[m]["P"] += 3
        elif gv > gm:
            tabela[v]["V"] += 1; tabela[m]["D"] += 1; tabela[v]["P"] += 3
        else:
            tabela[m]["E"] += 1; tabela[v]["E"] += 1; tabela[m]["P"] += 1; tabela[v]["P"] += 1
    for t in tabela:
        tabela[t]["SG"] = tabela[t]["GP"] - tabela[t]["GC"]
    df = pd.DataFrame.from_dict(tabela, orient="index")
    df["Time"] = df.index.map(lambda x: times[x]["nome"] if x in times else x)
    df = df[["Time", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
    df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
    return df

# 📋 Mostrar jogos por fase
def exibir_fase_mata(nome, dados, col):
    with col:
        st.markdown(f"### {nome}")
        for rodada in dados:
            for jogo in rodada.get("jogos", []):
                exibir_card(jogo)

# ⚙️ Funções auxiliares para mata-mata ida/volta
def criar_jogos_ida_volta(classificados):
    random.shuffle(classificados)
    jogos = []
    for i in range(0, len(classificados), 2):
        a, b = classificados[i], classificados[i+1]
        jogos.append({"mandante": a, "visitante": b, "gols_mandante": None, "gols_visitante": None})
        jogos.append({"mandante": b, "visitante": a, "gols_mandante": None, "gols_visitante": None})
    return jogos

def obter_vencedores_ida_volta(jogos):
    confrontos = {}
    for jogo in jogos:
        chave = frozenset([jogo["mandante"], jogo["visitante"]])
        confrontos.setdefault(chave, []).append(jogo)

    vencedores = []
    for chave, partidas in confrontos.items():
        if len(partidas) != 2:
            return None
        g1 = partidas[0]; g2 = partidas[1]
        if None in [g1["gols_mandante"], g1["gols_visitante"], g2["gols_mandante"], g2["gols_visitante"]]:
            return None
        time1 = g1["mandante"]
        time2 = g1["visitante"]
        gols1 = g1["gols_mandante"] + g2["gols_visitante"]
        gols2 = g1["gols_visitante"] + g2["gols_mandante"]
        vencedor = time1 if gols1 > gols2 else time2
        vencedores.append(vencedor)
    return vencedores

# ✅ Continuação do app: carregamento de dados, exibição dos grupos, botões para avançar fases e definição do campeão...
# (continue daqui no seu projeto com os blocos que já usava para mostrar classificação e usar essas funções novas nas fases do mata-mata)
