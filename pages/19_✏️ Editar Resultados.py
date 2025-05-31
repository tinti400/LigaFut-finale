# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerenciar Rodadas", page_icon="🏕️", layout="centered")
st.title("🏕️ Gerenciar Rodadas da Divisão")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if len(admin_ref.data) == 0:
    st.error("🔒 Acesso restrito: somente administradores.")
    st.stop()

# 🔹 Filtro de divisão
divisao = st.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 🗓️ Obter times da divisão
def obter_times(divisao):
    res_times = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute()
    return [u["time_id"] for u in res_times.data if u.get("time_id")]

# 📖 Obter nomes dos times
def obter_nomes_times():
    res_nomes = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res_nomes.data}

# 🔍 Buscar rodadas existentes
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

# 🔍 Rodadas
rodadas_existentes = buscar_rodadas()
times_map = obter_nomes_times()

if rodadas_existentes:
    st.subheader("🗓️ Editar Resultados")
    lista_numeros = [r["numero"] for r in rodadas_existentes]
    rodada_escolhida = st.selectbox("Selecione a rodada para editar", lista_numeros)
    rodada = next(r for r in rodadas_existentes if r["numero"] == rodada_escolhida)

    for idx, jogo in enumerate(rodada["jogos"]):
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        nome_m = times_map.get(mandante, "FOLGA" if mandante == "FOLGA" else "?")
        nome_v = times_map.get(visitante, "FOLGA" if visitante == "FOLGA" else "?")

        col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 3])
        with col1:
            st.markdown(f"**{nome_m}**")
        with col2:
            gm = st.number_input(f"Gols {nome_m}", min_value=0,
                                 value=jogo.get("gols_mandante") if jogo.get("gols_mandante") is not None else 0,
                                 key=f"gm_{idx}", format="%d")
        with col3:
            st.markdown("**X**")
        with col4:
            gv = st.number_input(f"Gols {nome_v}", min_value=0,
                                 value=jogo.get("gols_visitante") if jogo.get("gols_visitante") is not None else 0,
                                 key=f"gv_{idx}", format="%d")
        with col5:
            st.markdown(f"**{nome_v}**")

        if "FOLGA" in [mandante, visitante]:
            st.info("🚫 Este time folgou nesta rodada.")
        else:
            if st.button("💾 Salvar Resultado", key=f"salvar_{idx}"):
                rodada["jogos"][idx]["gols_mandante"] = gm
                rodada["jogos"][idx]["gols_visitante"] = gv

                try:
                    supabase.table(nome_tabela_rodadas).update({
                        "jogos": rodada["jogos"]
                    }).eq("numero", rodada_escolhida).execute()
                    st.success(f"Resultado salvo: {nome_m} {gm} x {gv} {nome_v}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

