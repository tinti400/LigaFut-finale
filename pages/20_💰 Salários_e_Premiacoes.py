# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao
from datetime import datetime

st.set_page_config(page_title="💰 Salários e Premiações", layout="wide")
st.title("💰 Painel de Salários e Premiações")

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

# 📅 Seleção de divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

st.markdown("---")

# 💵 Pagar salários com base no campo 'salario'
if st.button("💸 Pagar Salários da Rodada (campo salário do elenco)"):
    try:
        res_times = supabase.table("times").select("id").execute()
        for time in res_times.data:
            id_time = time["id"]
            res_elenco = supabase.table("elenco").select("salario").eq("id_time", id_time).execute()
            total_salario = sum(j.get("salario", 0) for j in res_elenco.data)

            if total_salario > 0:
                saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                novo_saldo = saldo_atual - total_salario
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
                registrar_movimentacao(id_time, "saida", total_salario, "Pagamento de salários da rodada")

        st.success("✅ Salários pagos com sucesso.")
    except Exception as e:
        st.error(f"Erro ao pagar salários: {e}")

# 🏆 Premiação por resultado (ajustada por divisão)
if st.button("🏅 Premiar Times por Resultados da Rodada"):
    try:
        res_rodadas = (
            supabase.table("rodadas")
            .select("*")
            .eq("temporada", numero_temporada)
            .eq("divisao", numero_divisao)
            .order("numero")
            .execute()
        )
        rodadas = res_rodadas.data if res_rodadas.data else []

        # 🪙 Definir valores por divisão
        if numero_divisao == 1:
            premio_vitoria = 12_000_000
            premio_empate = 8_000_000
            premio_derrota = 5_000_000
        elif numero_divisao == 2:
            premio_vitoria = 9_000_000
            premio_empate = 6_000_000
            premio_derrota = 3_000_000
        else:
            premio_vitoria = 6_000_000
            premio_empate = 4_000_000
            premio_derrota = 2_000_000

        premiacoes = {}

        for rodada in rodadas:
            for jogo in rodada["jogos"]:
                gm = jogo.get("gols_mandante")
                gv = jogo.get("gols_visitante")
                mandante = jogo["mandante"]
                visitante = jogo["visitante"]

                if gm is None or gv is None:
                    continue

                if gm > gv:
                    premiacoes[mandante] = premiacoes.get(mandante, 0) + premio_vitoria
                    premiacoes[visitante] = premiacoes.get(visitante, 0) + premio_derrota
                elif gv > gm:
                    premiacoes[visitante] = premiacoes.get(visitante, 0) + premio_vitoria
                    premiacoes[mandante] = premiacoes.get(mandante, 0) + premio_derrota
                else:
                    premiacoes[mandante] = premiacoes.get(mandante, 0) + premio_empate
                    premiacoes[visitante] = premiacoes.get(visitante, 0) + premio_empate

        for id_time, valor in premiacoes.items():
            saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            registrar_movimentacao(id_time, "entrada", valor, "Premiação por resultados da rodada")

        st.success("✅ Premiações aplicadas com sucesso.")
    except Exception as e:
        st.error(f"Erro ao premiar resultados: {e}")

# ⚽ Premiação por gols marcados e sofridos
if st.button("⚽ Premiar por Gols Marcados e Sofridos"):
    try:
        res_rodadas = (
            supabase.table("rodadas")
            .select("*")
            .eq("temporada", numero_temporada)
            .eq("divisao", numero_divisao)
            .order("numero")
            .execute()
        )
        rodadas = res_rodadas.data if res_rodadas.data else []

        # 💰 Valores por divisão
        if numero_divisao == 1:
            valor_gol_feito = 400_000
            valor_gol_sofrido = 80_000
        elif numero_divisao == 2:
            valor_gol_feito = 300_000
            valor_gol_sofrido = 60_000
        else:
            valor_gol_feito = 200_000
            valor_gol_sofrido = 40_000

        premiacoes = {}

        for rodada in rodadas:
            for jogo in rodada["jogos"]:
                gm = jogo.get("gols_mandante")
                gv = jogo.get("gols_visitante")
                mandante = jogo["mandante"]
                visitante = jogo["visitante"]

                if gm is None or gv is None:
                    continue

                # Mandante
                valor_mandante = (gm * valor_gol_feito) - (gv * valor_gol_sofrido)
                premiacoes[mandante] = premiacoes.get(mandante, 0) + valor_mandante

                # Visitante
                valor_visitante = (gv * valor_gol_feito) - (gm * valor_gol_sofrido)
                premiacoes[visitante] = premiacoes.get(visitante, 0) + valor_visitante

        for id_time, valor in premiacoes.items():
            saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            registrar_movimentacao(id_time, "entrada" if valor >= 0 else "saida", abs(valor), "Premiação por gols feitos e sofridos")

        st.success("✅ Premiação por gols aplicada com sucesso.")
    except Exception as e:
        st.error(f"Erro ao premiar por gols: {e}")
