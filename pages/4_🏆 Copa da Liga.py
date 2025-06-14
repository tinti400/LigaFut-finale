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
    return {
        item["id"]: {"nome": item["nome"], "escudo_url": item.get("logo", "")}
        for item in res.data
    }

# 🔄 Buscar data mais recente
def buscar_data_mais_recente():
    res = supabase.table("copa_ligafut").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    if res.data:
        return res.data[0]["data_criacao"]
    return None

# 🔄 Buscar fases
def buscar_fase(fase, data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("data_criacao", data).execute()
    return res.data if res.data else []

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

# 📊 Classificação
def calcular_classificacao(jogos):
    tabela = {}
    for jogo in jogos:
        m, v = jogo["mandante"], jogo["visitante"]
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
        for t in [m, v]:
            if t not in tabela:
                tabela[t] = {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0, "SG": 0}
        if gm is None or gv is None:
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
    df["Time"] = df.index.map(lambda x: times[x]["nome"] if x in times else x)
    df["Logo"] = df.index.map(lambda x: f"<img src='{times[x]['escudo_url']}' width='20'>" if x in times else "")
    df = df[["Time", "Logo", "P", "J", "V", "E", "D", "GP", "GC", "SG"]]
    df = df.sort_values(by=["P", "SG", "GP"], ascending=False).reset_index(drop=True)
    return df

# 📋 Exibição por fase
def exibir_fase_mata(nome, dados, col):
    with col:
        st.markdown(f"### {nome}")
        for rodada in dados:
            for jogo in rodada.get("jogos", []):
                exibir_card(jogo)

# ♻️ Coleta de dados
times = buscar_times()
data_atual = buscar_data_mais_recente()
grupos = buscar_grupos(data_atual)
oitavas = buscar_fase("oitavas", data_atual)
quartas = buscar_fase("quartas", data_atual)
semis = buscar_fase("semifinal", data_atual)
final = buscar_fase("final", data_atual)

# ✅ Organização dos grupos
grupos_por_nome = {}
for g in grupos:
    nome = g.get("grupo", "?")
    if nome not in grupos_por_nome:
        grupos_por_nome[nome] = []
    grupos_por_nome[nome].extend(g.get("jogos", []))

# 📈 Classificação no topo
st.subheader("📈 Classificação dos Grupos")
for grupo, jogos in sorted(grupos_por_nome.items()):
    st.markdown(f"#### {grupo}")
    df = calcular_classificacao(jogos)
    def estilo(row): return ['background-color: #d4edda'] * len(row) if row.name < 4 else [''] * len(row)
    st.markdown(df.style.apply(estilo, axis=1).to_html(escape=False, index=False), unsafe_allow_html=True)

# 🏑 Fase Mata-Mata
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏑 Fase Mata-Mata")
col1, col2, col3, col4 = st.columns(4)
exibir_fase_mata("Oitavas", oitavas, col1)
exibir_fase_mata("Quartas", quartas, col2)
exibir_fase_mata("Semifinal", semis, col3)
exibir_fase_mata("Final", final, col4)

# 🌟 Finalização e Histórico
st.markdown("<hr>")
st.subheader("🌟 Finalização e Histórico")

# ✅ Condição de finalização
def todos_jogos_preenchidos(grupos):
    for jogos in grupos.values():
        for jogo in jogos:
            if jogo.get("gols_mandante") is None or jogo.get("gols_visitante") is None:
                return False
    return True

def final_jogada_ok(final):
    if final and final[0].get("jogos"):
        jogo = final[0]["jogos"][0]
        return jogo.get("gols_mandante") is not None and jogo.get("gols_visitante") is not None
    return False

if final_jogada_ok(final) and todos_jogos_preenchidos(grupos_por_nome):
    jogo = final[0]["jogos"][0]
    vencedor_id = jogo["mandante"] if jogo["gols_mandante"] > jogo["gols_visitante"] else jogo["visitante"]
    campeao = times.get(vencedor_id, {}).get("nome", "Desconhecido")
    jogos_grupo = sum(grupos_por_nome.values(), [])
    classif = calcular_classificacao(jogos_grupo)
    melhor_ataque = classif.sort_values("GP", ascending=False).iloc[0]["Time"]
    melhor_defesa = classif.sort_values("GC", ascending=True).iloc[0]["Time"]

    st.success(f"🏆 Campeão: **{campeao}**")
    st.info(f"🔥 Melhor Ataque: **{melhor_ataque}**")
    st.info(f"🛡️ Melhor Defesa: **{melhor_defesa}**")

    try:
        supabase.table("historico_copa").insert({
            "data_fim": datetime.now().isoformat(),
            "campeao": campeao,
            "melhor_ataque": melhor_ataque,
            "melhor_defesa": melhor_defesa
        }).execute()
        st.success("📅 Histórico da Copa salvo com sucesso!")
    except Exception as e:
        st.warning(f"Erro ao salvar histórico: {e}")
