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

# 📅 Jogos e placares
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📅 Jogos por Grupo")
cols = st.columns(4)
for idx, (grupo, jogos) in enumerate(sorted(grupos_por_nome.items())):
    with cols[idx % 4]:
        st.markdown(f"### {grupo}")
        for jogo in jogos:
            exibir_card(jogo)

# 🏆 Campeão
st.markdown("### 🏆 Campeão")
if final and final[0].get("jogos"):
    jogo_final = final[0]["jogos"][0]
    gm = jogo_final.get("gols_mandante")
    gv = jogo_final.get("gols_visitante")
    if gm is not None and gv is not None:
        vencedor_id = jogo_final["mandante"] if gm > gv else jogo_final["visitante"]
        vencedor = times.get(vencedor_id, {"nome": "?"})

        todos_jogos = []
        for rodada in grupos_por_nome.values():
            todos_jogos.extend(rodada)
        for fase in [oitavas, quartas, semis, final]:
            for rodada in fase:
                todos_jogos.extend(rodada.get("jogos", []))

        if all(j.get("gols_mandante") is not None and j.get("gols_visitante") is not None for j in todos_jogos):
            gols_por_time = {}
            for jogo in todos_jogos:
                for time, gols in [(jogo["mandante"], jogo["gols_mandante"]), (jogo["visitante"], jogo["gols_visitante"])]:
                    if time not in gols_por_time:
                        gols_por_time[time] = {"feitos": 0, "tomados": 0}
                    gols_por_time[time]["feitos"] += gols
                    gols_por_time[time]["tomados"] += jogo["gols_mandante"] if time == jogo["visitante"] else jogo["gols_visitante"]

            melhor_ataque = max(gols_por_time.items(), key=lambda x: x[1]["feitos"])[0]
            melhor_defesa = min(gols_por_time.items(), key=lambda x: x[1]["tomados"])[0]

            st.success(f"🏆 Campeão: **{vencedor['nome']}**")
            st.info(f"🔥 Melhor ataque: {times[melhor_ataque]['nome']}")
            st.info(f"🛡️ Melhor defesa: {times[melhor_defesa]['nome']}")

            supabase.table("historico_copa").insert({
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "campeao_id": vencedor_id,
                "melhor_ataque_id": melhor_ataque,
                "melhor_defesa_id": melhor_defesa
            }).execute()
        else:
            st.info("Aguarde: nem todos os resultados foram preenchidos.")
    else:
        st.info("Final ainda sem placar.")
else:
    st.info("Final ainda não cadastrada.")

# ⚔️ Avançar para o Mata-Mata (Sorteio)
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

    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    supabase.table("copa_ligafut").insert({
        "fase": "oitavas",
        "data_criacao": data_hoje,
        "jogos": confrontos
    }).execute()

    st.success("✅ Confrontos das oitavas sorteados e salvos com sucesso!")
    st.experimental_rerun()
