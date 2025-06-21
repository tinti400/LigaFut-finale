# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import pagar_salario, pagar_premiacao

st.set_page_config(page_title="✏️ Editar Resultados", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verifica login
if "usuario" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📌 Dados da sessão
usuario = st.session_state["usuario"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔄 Seleção de temporada e divisão
temporada = st.selectbox("📅 Temporada", [1, 2, 3], index=0)
divisao = st.selectbox("🏆 Divisão", [1, 2, 3], index=0)

# 📥 Carregar rodadas
try:
    nome_tabela = f"rodadas_temporada_{temporada}_divisao_{divisao}"
    rodadas = supabase.table(nome_tabela).select("*").order("numero").execute().data
except Exception as e:
    st.error(f"Erro ao carregar rodadas: {e}")
    st.stop()

# ⬇️ Escolha da rodada
numeros_rodadas = [r["numero"] for r in rodadas]
rodada_selecionada = st.selectbox("Escolha a rodada", numeros_rodadas)

# 🔎 Pega os jogos da rodada
jogos = []
for rodada in rodadas:
    if rodada["numero"] == rodada_selecionada:
        jogos = rodada["jogos"]
        break

st.markdown("## 📝 Editar Resultados da Rodada")

# 🎯 Campos para editar resultados
for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f"**{jogo['mandante']} x {jogo['visitante']}**")
    with col2:
        gols_mandante = st.number_input("Gols Mandante", min_value=0, value=jogo.get("gols_mandante", 0), key=f"gm_{idx}")
    with col3:
        gols_visitante = st.number_input("Gols Visitante", min_value=0, value=jogo.get("gols_visitante", 0), key=f"gv_{idx}")
    with col4:
        st.markdown("")

    jogo["gols_mandante"] = gols_mandante
    jogo["gols_visitante"] = gols_visitante

# 💾 Botão para salvar e processar
if st.button("💾 Salvar Resultados e Atualizar Financeiro"):
    try:
        # Atualiza os resultados no banco
        supabase.table(nome_tabela).update({"jogos": jogos}).eq("numero", rodada_selecionada).execute()

        # Busca todos os times da divisão
        times_res = supabase.table("times").select("id, nome").execute()
        mapa_times = {t["nome"]: t["id"] for t in times_res.data}

        # Processa cada jogo
        for jogo in jogos:
            id_m = mapa_times.get(jogo["mandante"])
            id_v = mapa_times.get(jogo["visitante"])
            gols_m = jogo.get("gols_mandante", 0)
            gols_v = jogo.get("gols_visitante", 0)

            # Pagar salários
            if id_m:
                pagar_salario(id_m)
            if id_v:
                pagar_salario(id_v)

            # Premiação por resultado
            if id_m and id_v:
                pagar_premiacao(id_m, id_v, gols_m, gols_v, int(divisao))

        st.success("✅ Resultados salvos e premiações processadas com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar resultados: {e}")


