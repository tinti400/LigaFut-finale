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

# 🔁 Coleta de dados
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

# 🏁 Fase Mata-Mata
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏁 Fase Mata-Mata")
col1, col2, col3, col4 = st.columns(4)
exibir_fase_mata("Oitavas", oitavas, col1)
exibir_fase_mata("Quartas", quartas, col2)
exibir_fase_mata("Semifinal", semis, col3)
exibir_fase_mata("Final", final, col4)

# ⚔️ Sorteio das Oitavas
st.markdown("---")
st.subheader("⚔️ Sorteio das Oitavas")

if st.button("🔄 Avançar para o Mata-Mata (Sorteio)"):
    classificados = []
    for jogos in grupos_por_nome.values():
        df = calcular_classificacao(jogos)
        top4_ids = [idx for idx in df.index[:4]]
        for i in top4_ids:
            nome = df.loc[i, "Time"]
            id_time = next((k for k, v in times.items() if v["nome"] == nome), None)
            if id_time:
                classificados.append(id_time)

    if len(classificados) != 16:
        st.error("Número de classificados diferente de 16. Verifique a fase de grupos.")
        st.stop()

    random.shuffle(classificados)
    confrontos = []

    for i in range(0, 16, 2):
        time_a = classificados[i]
        time_b = classificados[i + 1]

        jogo_ida = {
            "mandante": time_a,
            "visitante": time_b,
            "gols_mandante": None,
            "gols_visitante": None
        }
        jogo_volta = {
            "mandante": time_b,
            "visitante": time_a,
            "gols_mandante": None,
            "gols_visitante": None
        }

        confrontos.extend([jogo_ida, jogo_volta])

    supabase.table("copa_ligafut").insert({
        "fase": "oitavas",
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "jogos": confrontos
    }).execute()

    st.success("✅ Confrontos das oitavas sorteados e salvos com sucesso!")
    st.experimental_rerun()

# 🚀 Avançar fases
def avancar_fase(fase_atual, proxima_fase):
    dados_fase = buscar_fase(fase_atual, data_atual)
    if not dados_fase:
        st.error(f"Nenhuma rodada encontrada para {fase_atual}.")
        return

    jogos = dados_fase[0]["jogos"]
    if any(j["gols_mandante"] is None or j["gols_visitante"] is None for j in jogos):
        st.warning("Preencha todos os resultados antes de avançar.")
        return

    classificados = []
    for i in range(0, len(jogos), 2):
        ida, volta = jogos[i], jogos[i+1]
        total_a = ida["gols_mandante"] + volta["gols_visitante"]
        total_b = ida["gols_visitante"] + volta["gols_mandante"]
        if total_a > total_b:
            classificados.append(ida["mandante"])
        elif total_b > total_a:
            classificados.append(ida["visitante"])
        else:
            classificados.append(random.choice([ida["mandante"], ida["visitante"]]))

    if len(classificados) < 2:
        st.error("Erro ao identificar classificados.")
        return

    jogos_novos = []
    random.shuffle(classificados)
    for i in range(0, len(classificados), 2):
        a, b = classificados[i], classificados[i+1]
        jogos_novos.extend([
            {"mandante": a, "visitante": b, "gols_mandante": None, "gols_visitante": None},
            {"mandante": b, "visitante": a, "gols_mandante": None, "gols_visitante": None},
        ])

    supabase.table("copa_ligafut").insert({
        "fase": proxima_fase,
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "jogos": jogos_novos
    }).execute()
    st.success(f"✅ Avançou de {fase_atual} para {proxima_fase}!")
    st.experimental_rerun()

st.subheader("🚀 Avançar Fases")
if st.button("➡️ Avançar para Quartas"):
    avancar_fase("oitavas", "quartas")
if st.button("➡️ Avançar para Semifinal"):
    avancar_fase("quartas", "semifinal")
if st.button("➡️ Avançar para Final"):
    avancar_fase("semifinal", "final")
