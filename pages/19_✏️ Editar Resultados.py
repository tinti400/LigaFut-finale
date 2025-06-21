# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import pandas as pd
from utils import registrar_movimentacao_simples, registrar_pagamento_salario

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏕️ Gerenciar Resultados", layout="wide")
st.title("🏕️ Gerenciar Resultados das Rodadas")

# ✅ Verifica login e admin
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito apenas para administradores.")
    st.stop()

# 🔽 Seleção da divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = divisao.split()[-1]
numero_temporada = temporada.split()[-1]
tabela_rodadas = f"rodadas_divisao_{numero_divisao}_temp{numero_temporada}"

# 🔄 Times e nomes
def buscar_times_nomes_logos():
    times_data = supabase.table("times").select("id", "nome", "logo").execute().data
    return {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in times_data}

times_info = buscar_times_nomes_logos()

# 🔄 Rodadas
rodadas_data = supabase.table(tabela_rodadas).select("*").order("numero").execute().data
if not rodadas_data:
    st.warning("Nenhuma rodada encontrada.")
    st.stop()

rodada_nums = [r["numero"] for r in rodadas_data]
rodada_atual = st.selectbox("Escolha a rodada para editar:", rodada_nums)
rodada = next(r for r in rodadas_data if r["numero"] == rodada_atual)

# 🔍 Filtro por time
todos_ids = [j["mandante"] for j in rodada["jogos"]] + [j["visitante"] for j in rodada["jogos"]]
nomes_filtrados = {id_: times_info.get(id_, {}).get("nome", "?") for id_ in todos_ids}
nome_time_filtro = st.selectbox("🔎 Filtrar por time da rodada", ["Todos"] + list(set(nomes_filtrados.values())))

# 🧮 Função para calcular e aplicar premiação
def processar_pagamentos(id_time, gols_feitos, gols_sofridos, resultado):
    if resultado == "vitoria":
        valor_base = 9000000 if numero_divisao == "1" else 6000000 if numero_divisao == "2" else 4000000
    elif resultado == "empate":
        valor_base = 5000000 if numero_divisao == "1" else 3500000 if numero_divisao == "2" else 2500000
    else:  # derrota
        valor_base = 2500000 if numero_divisao == "1" else 1500000 if numero_divisao == "2" else 1000000

    bonus_gols = gols_feitos * 200000
    penalidade_gols = gols_sofridos * 25000
    total = valor_base + bonus_gols - penalidade_gols

    # 💰 Credita premiação
    supabase.table("times").update({"saldo": f"saldo + {total}"}).eq("id", id_time).execute()
    registrar_movimentacao_simples(id_time, total, f"Premiação rodada (Resultado: {resultado.title()}, Gols: +{bonus_gols:,} / -{penalidade_gols:,})")

    # 💸 Debita salários
    registrar_pagamento_salario(supabase, id_time)

# 🎯 Edição dos jogos
for idx, jogo in enumerate(rodada["jogos"]):
    id_m, id_v = jogo["mandante"], jogo["visitante"]
    if "FOLGA" in [id_m, id_v]:
        continue

    nome_m = times_info.get(id_m, {}).get("nome", "Desconhecido")
    logo_m = times_info.get(id_m, {}).get("logo", "")
    nome_v = times_info.get(id_v, {}).get("nome", "Desconhecido")
    logo_v = times_info.get(id_v, {}).get("logo", "")

    if nome_time_filtro != "Todos" and nome_time_filtro not in [nome_m, nome_v]:
        continue

    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns([2, 1, 0.5, 1, 2])

    with col1:
        st.image(logo_m or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=50)
        st.markdown(f"**{nome_m}**", unsafe_allow_html=True)

    with col2:
        gols_m = st.number_input(f"Gols {nome_m}", value=jogo.get("gols_mandante") or 0, min_value=0, key=f"gm_{idx}")

    with col3:
        st.markdown("<h4 style='text-align:center;'>X</h4>", unsafe_allow_html=True)

    with col4:
        gols_v = st.number_input(f"Gols {nome_v}", value=jogo.get("gols_visitante") or 0, min_value=0, key=f"gv_{idx}")

    with col5:
        st.image(logo_v or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=50)
        st.markdown(f"**{nome_v}**", unsafe_allow_html=True)

    if st.button("💾 Salvar", key=f"btn_{idx}"):
        novos_jogos = []
        for j in rodada["jogos"]:
            if j["mandante"] == id_m and j["visitante"] == id_v:
                j["gols_mandante"] = gols_m
                j["gols_visitante"] = gols_v
            novos_jogos.append(j)

        supabase.table(tabela_rodadas).update({"jogos": novos_jogos}).eq("numero", rodada_atual).execute()

        # Processa premiação e salários
        if gols_m > gols_v:
            processar_pagamentos(id_m, gols_m, gols_v, "vitoria")
            processar_pagamentos(id_v, gols_v, gols_m, "derrota")
        elif gols_m < gols_v:
            processar_pagamentos(id_m, gols_m, gols_v, "derrota")
            processar_pagamentos(id_v, gols_v, gols_m, "vitoria")
        else:
            processar_pagamentos(id_m, gols_m, gols_v, "empate")
            processar_pagamentos(id_v, gols_v, gols_m, "empate")

        st.success(f"✅ Resultado atualizado: {nome_m} {gols_m} x {gols_v} {nome_v}")
        st.rerun()

# 🔎 Histórico geral
st.markdown("---")
st.subheader("📜 Histórico do Time em Todas Rodadas")
nomes_times = {v["nome"]: k for k, v in times_info.items()}
time_nome = st.selectbox("Selecione um time:", sorted(nomes_times.keys()))
id_escolhido = nomes_times[time_nome]

historico = []
for r in rodadas_data:
    for j in r["jogos"]:
        if id_escolhido in [j["mandante"], j["visitante"]]:
            nome_m = times_info.get(j["mandante"], {}).get("nome", "?")
            nome_v = times_info.get(j["visitante"], {}).get("nome", "?")
            gm = j.get("gols_mandante")
            gv = j.get("gols_visitante")
            placar = f"{gm} x {gv}" if gm is not None and gv is not None else "Não definido"

            historico.append({
                "Rodada": r["numero"],
                "Mandante": nome_m,
                "Visitante": nome_v,
                "Placar": placar
            })

if historico:
    df = pd.DataFrame(historico).sort_values("Rodada")
    st.dataframe(df, use_container_width=True)
else:
    st.info("❌ Nenhum jogo encontrado para este time.")


