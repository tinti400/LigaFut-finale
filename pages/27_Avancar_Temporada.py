# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from itertools import combinations
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🔄 Avançar Temporada", layout="centered")
st.title("🔄 Avançar Temporada")

# ⛔️ Verifica login e admin
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

usuario = st.session_state["usuario"]
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("Apenas administradores podem acessar esta página.")
    st.stop()

# 🔹 Escolher divisão
divisao = st.selectbox("Selecione a divisão para encerrar a temporada:", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📊 Buscar resultados
rodadas = supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data
if not rodadas:
    st.info("Nenhuma rodada encontrada.")
    st.stop()

def todos_os_jogos_preenchidos(rodadas):
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            if jogo.get("gols_mandante") is None or jogo.get("gols_visitante") is None:
                return False
    return True

def obter_nomes_times():
    res = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute()
    time_ids = [r["time_id"] for r in res.data if r.get("time_id")]
    if not time_ids:
        return {}
    times = supabase.table("times").select("id", "nome", "logo").in_("id", time_ids).execute().data
    return {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in times}

def calcular_classificacao(rodadas, times_map):
    tabela = {}
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m, v = jogo.get("mandante"), jogo.get("visitante")
            gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
            if None in [m, v, gm, gv]: continue
            gm, gv = int(gm), int(gv)
            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {"nome": times_map[t]["nome"], "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0}
            tabela[m]["gp"] += gm; tabela[m]["gc"] += gv; tabela[m]["sg"] += gm - gv
            tabela[v]["gp"] += gv; tabela[v]["gc"] += gm; tabela[v]["sg"] += gv - gm
            if gm > gv:
                tabela[m]["pontos"] += 3; tabela[m]["v"] += 1; tabela[v]["d"] += 1
            elif gv > gm:
                tabela[v]["pontos"] += 3; tabela[v]["v"] += 1; tabela[m]["d"] += 1
            else:
                tabela[m]["pontos"] += 1; tabela[v]["pontos"] += 1; tabela[m]["e"] += 1; tabela[v]["e"] += 1
    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

def gerar_rodadas_novas_turno_returno(time_ids):
    random.shuffle(time_ids)
    jogos_turno = list(combinations(time_ids, 2))
    random.shuffle(jogos_turno)

    rodadas = []
    rodada_atual = []
    usados_rodada = set()
    rodada_num = 1

    for jogo in jogos_turno:
        mandante, visitante = jogo
        if mandante in usados_rodada or visitante in usados_rodada:
            rodadas.append({"numero": rodada_num, "jogos": rodada_atual})
            rodada_num += 1
            rodada_atual = []
            usados_rodada = set()
        rodada_atual.append({"mandante": mandante, "visitante": visitante})
        usados_rodada.add(mandante)
        usados_rodada.add(visitante)

    if rodada_atual:
        rodadas.append({"numero": rodada_num, "jogos": rodada_atual})

    # Gerar returno invertendo mandos
    rodadas_returno = []
    for i, rodada in enumerate(rodadas, start=rodada_num):
        jogos_invertidos = [{"mandante": jogo["visitante"], "visitante": jogo["mandante"]} for jogo in rodada["jogos"]]
        rodadas_returno.append({"numero": i, "jogos": jogos_invertidos})

    return rodadas + rodadas_returno

# 🔄 Avançar temporada
if todos_os_jogos_preenchidos(rodadas):
    times_map = obter_nomes_times()
    classificacao = calcular_classificacao(rodadas, times_map)

    campeao = classificacao[0][1]["nome"]
    melhor_ataque = max(classificacao, key=lambda x: x[1]["gp"])[1]["nome"]
    melhor_defesa = min(classificacao, key=lambda x: x[1]["gc"])[1]["nome"]

    st.success("Todos os jogos estão preenchidos! Pronto para encerrar a temporada.")
    st.markdown(f"**🏆 Campeão:** `{campeao}`")
    st.markdown(f"**🔥 Melhor ataque:** `{melhor_ataque}`")
    st.markdown(f"**🧱 Melhor defesa:** `{melhor_defesa}`")

    if st.button("🔄 Confirmar avanço de temporada"):
        try:
            # 🕓 Salvar histórico
            supabase.table("historico_temporadas").insert({
                "data_fim": datetime.now().isoformat(),
                "divisao": divisao,
                "campeao": campeao,
                "melhor_ataque": melhor_ataque,
                "melhor_defesa": melhor_defesa
            }).execute()

            # 🟢 Promoções e rebaixamentos
            if divisao == "Divisão 1":
                rebaixados = classificacao[-2:]
                for r in rebaixados:
                    supabase.table("usuarios").update({"Divisão": "Divisão 2"}).eq("time_id", r[0]).execute()
            elif divisao == "Divisão 2":
                promovidos = classificacao[:2]
                for p in promovidos:
                    supabase.table("usuarios").update({"Divisão": "Divisão 1"}).eq("time_id", p[0]).execute()

            # 🧹 Apagar rodadas antigas
            for r in supabase.table(nome_tabela_rodadas).select("id").execute().data:
                supabase.table(nome_tabela_rodadas).delete().eq("id", r["id"]).execute()

            # ♻️ Gerar nova temporada com turno e returno
            time_ids = list(times_map.keys())
            novas_rodadas = gerar_rodadas_novas_turno_returno(time_ids)
            for rodada in novas_rodadas:
                supabase.table(nome_tabela_rodadas).insert(rodada).execute()

            st.success("🌟 Temporada encerrada e nova temporada criada com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao encerrar temporada: {e}")
else:
    st.info("Ainda há jogos sem resultado. Preencha todos os resultados antes de avançar.")

