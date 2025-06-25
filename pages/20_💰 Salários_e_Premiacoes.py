# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao
import uuid

st.set_page_config(page_title="💰 Salários e Premiações", layout="wide")
st.title("💰 Pagamento de Salários e Premiações")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login e admin
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito apenas para administradores.")
    st.stop()

# 📅 Filtros
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
num_divisao = int(divisao.split()[-1])
num_temporada = int(temporada.split()[-1])

# 🔄 Mapeamento de ID para nome
res_times = supabase.table("times").select("id, nome").execute()
id_para_nome = {item["id"]: item["nome"] for item in res_times.data}

# ⚙️ Valores
premios = {
    1: {"vitoria": 12_000_000, "empate": 8_000_000, "derrota": 5_000_000, "gol_feito": 400_000, "gol_sofrido": 80_000},
    2: {"vitoria": 9_000_000, "empate": 6_000_000, "derrota": 3_000_000, "gol_feito": 300_000, "gol_sofrido": 60_000},
    3: {"vitoria": 6_000_000, "empate": 4_000_000, "derrota": 2_000_000, "gol_feito": 200_000, "gol_sofrido": 40_000},
}

# 🔄 Buscar rodadas e pagamentos realizados
try:
    res_rodadas = supabase.table("rodadas").select("*").eq("temporada", num_temporada).eq("divisao", num_divisao).order("numero", desc=False).execute()
    rodadas = res_rodadas.data if res_rodadas.data else []
    res_pagamentos = supabase.table("pagamentos_realizados").select("*").eq("temporada", num_temporada).eq("divisao", num_divisao).execute()
    pagos = res_pagamentos.data or []
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    st.stop()

# 🔁 Exibir apenas jogos não totalmente pagos
for rodada in rodadas:
    jogos_visiveis = []
    for jogo in rodada["jogos"]:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        numero_rodada = rodada.get("numero", 0)

        tipos_requeridos = {"salario_mandante", "salario_visitante", "premiacao", "bonus"}
        pagos_jogo = {
            p["tipo"] for p in pagos
            if p["rodada"] == numero_rodada and p["mandante"] == mandante and p["visitante"] == visitante
        }

        if not tipos_requeridos.issubset(pagos_jogo):
            jogos_visiveis.append(jogo)

    if jogos_visiveis:
        st.markdown(f"### 📅 Rodada {rodada.get('numero', '?')}")
        for jogo in jogos_visiveis:
            mandante = jogo["mandante"]
            visitante = jogo["visitante"]
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")
            nome_mandante = id_para_nome.get(mandante, mandante)
            nome_visitante = id_para_nome.get(visitante, visitante)

            col1, col2, col3, col4, col5 = st.columns([3, 1, 3, 3, 3])
            col1.markdown(f"**{nome_mandante}**")
            col2.markdown(f"<h3 style='text-align:center'>{gm if gm is not None else '-'} x {gv if gv is not None else '-'}</h3>", unsafe_allow_html=True)
            col3.markdown(f"**{nome_visitante}**")

            if col4.button(f"💸 Cobrar salário ({nome_mandante})", key=f"sal_m_{mandante}_{visitante}"):
                try:
                    elenco = supabase.table("elenco").select("valor").eq("id_time", mandante).execute().data
                    total = round(sum(j.get("valor", 0) * 0.01 for j in elenco if isinstance(j, dict)))
                    saldo = supabase.table("times").select("saldo").eq("id", mandante).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": int(saldo - total)}).eq("id", mandante).execute()
                    registrar_movimentacao(mandante, "saida", total, "Pagamento de salário")
                    supabase.table("pagamentos_realizados").insert({
                        "id": str(uuid.uuid4()), "temporada": num_temporada, "divisao": num_divisao,
                        "rodada": rodada["numero"], "mandante": mandante, "visitante": visitante, "tipo": "salario_mandante",
                        "data": str(datetime.utcnow())
                    }).execute()
                    st.success(f"Salário cobrado de {nome_mandante}")
                except Exception as e:
                    st.error(f"Erro ao cobrar salário: {e}")

            if col5.button(f"💸 Cobrar salário ({nome_visitante})", key=f"sal_v_{mandante}_{visitante}"):
                try:
                    elenco = supabase.table("elenco").select("valor").eq("id_time", visitante).execute().data
                    total = round(sum(j.get("valor", 0) * 0.01 for j in elenco if isinstance(j, dict)))
                    saldo = supabase.table("times").select("saldo").eq("id", visitante).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": int(saldo - total)}).eq("id", visitante).execute()
                    registrar_movimentacao(visitante, "saida", total, "Pagamento de salário")
                    supabase.table("pagamentos_realizados").insert({
                        "id": str(uuid.uuid4()), "temporada": num_temporada, "divisao": num_divisao,
                        "rodada": rodada["numero"], "mandante": mandante, "visitante": visitante, "tipo": "salario_visitante",
                        "data": str(datetime.utcnow())
                    }).execute()
                    st.success(f"Salário cobrado de {nome_visitante}")
                except Exception as e:
                    st.error(f"Erro ao cobrar salário: {e}")

            col6, col7 = st.columns([3, 3])
            if col6.button("🏆 Premiação Resultado", key=f"res_{mandante}_{visitante}"):
                try:
                    if gm is None or gv is None:
                        st.warning("Resultado incompleto.")
                        continue
                    val = premios[num_divisao]
                    if gm > gv:
                        vencedores = [(mandante, val["vitoria"]), (visitante, val["derrota"])]
                    elif gv > gm:
                        vencedores = [(visitante, val["vitoria"]), (mandante, val["derrota"])]
                    else:
                        vencedores = [(mandante, val["empate"]), (visitante, val["empate"])]
                    for t, valor in vencedores:
                        saldo = supabase.table("times").select("saldo").eq("id", t).execute().data[0]["saldo"]
                        supabase.table("times").update({"saldo": int(saldo + valor)}).eq("id", t).execute()
                        registrar_movimentacao(t, "entrada", valor, "Premiação por resultado")
                    supabase.table("pagamentos_realizados").insert({
                        "id": str(uuid.uuid4()), "temporada": num_temporada, "divisao": num_divisao,
                        "rodada": rodada["numero"], "mandante": mandante, "visitante": visitante, "tipo": "premiacao",
                        "data": str(datetime.utcnow())
                    }).execute()
                    st.success("Premiação paga.")
                except Exception as e:
                    st.error(f"Erro na premiação: {e}")

            if col7.button("⚽ Bônus de Gols", key=f"gol_{mandante}_{visitante}"):
                try:
                    if gm is None or gv is None:
                        st.warning("Resultado incompleto.")
                        continue
                    val = premios[num_divisao]
                    dados = [(mandante, gm, gv), (visitante, gv, gm)]
                    for t, g_feito, g_sofrido in dados:
                        valor = (g_feito * val["gol_feito"]) - (g_sofrido * val["gol_sofrido"])
                        saldo = supabase.table("times").select("saldo").eq("id", t).execute().data[0]["saldo"]
                        novo = saldo + valor if valor >= 0 else saldo - abs(valor)
                        supabase.table("times").update({"saldo": int(novo)}).eq("id", t).execute()
                        registrar_movimentacao(t, "entrada" if valor >= 0 else "saida", abs(valor), "Bônus de gols")
                    supabase.table("pagamentos_realizados").insert({
                        "id": str(uuid.uuid4()), "temporada": num_temporada, "divisao": num_divisao,
                        "rodada": rodada["numero"], "mandante": mandante, "visitante": visitante, "tipo": "bonus",
                        "data": str(datetime.utcnow())
                    }).execute()
                    st.success("Bônus de gols processado.")
                except Exception as e:
                    st.error(f"Erro bônus gols: {e}")
