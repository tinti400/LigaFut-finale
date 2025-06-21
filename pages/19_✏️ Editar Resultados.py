# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao_simples, pagar_salario_e_premiacao_resultado
import streamlit.components.v1 as components

st.set_page_config(page_title="✏️ Editar Resultados", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

st.title("✏️ Editar Resultados da Rodada")

temporada = st.selectbox("Temporada", [1, 2, 3])
divisao = st.selectbox("Divisão", [1, 2, 3])

try:
    rodadas = (
        supabase.table(f"rodadas_temporada_{temporada}_divisao_{divisao}")
        .select("*")
        .order("numero")
        .execute()
        .data
    )
except Exception as e:
    st.error(f"Erro ao carregar rodadas: {e}")
    st.stop()

if not rodadas:
    st.info("Nenhuma rodada encontrada.")
    st.stop()

rodada_selecionada = st.selectbox(
    "Escolha a rodada", [f"Rodada {r['numero']}" for r in rodadas]
)

rodada_numero = int(rodada_selecionada.split(" ")[-1])
rodada = next((r for r in rodadas if r["numero"] == rodada_numero), None)

if not rodada:
    st.warning("Rodada não encontrada.")
    st.stop()

jogos = rodada["jogos"]

st.markdown("### 📝 Resultados")
for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        mandante = st.text_input(f"Mandante {idx}", jogo["mandante"], disabled=True)
    with col2:
        gols_mandante = st.number_input(
            f"Gols {jogo['mandante']}", min_value=0, value=jogo.get("gols_mandante", 0), key=f"gm_{idx}"
        )
    with col3:
        st.markdown("<h4 style='text-align:center;'>X</h4>", unsafe_allow_html=True)
    with col4:
        gols_visitante = st.number_input(
            f"Gols {jogo['visitante']}", min_value=0, value=jogo.get("gols_visitante", 0), key=f"gv_{idx}"
        )
    with col5:
        visitante = st.text_input(f"Visitante {idx}", jogo["visitante"], disabled=True)

if st.button("💾 Salvar Resultados e Aplicar Premiações"):
    for idx, jogo in enumerate(jogos):
        jogo["gols_mandante"] = st.session_state[f"gm_{idx}"]
        jogo["gols_visitante"] = st.session_state[f"gv_{idx}"]

        id_m = jogo["id_mandante"]
        id_v = jogo["id_visitante"]
        gols_m = jogo["gols_mandante"]
        gols_v = jogo["gols_visitante"]

        # Aplica salário + premiação + bônus
        try:
            pagar_salario_e_premiacao_resultado(id_m, id_v, gols_m, gols_v, divisao)
        except Exception as e:
            st.error(f"Erro ao aplicar movimentações: {e}")

    # Atualiza rodada com os novos gols
    try:
        supabase.table(f"rodadas_temporada_{temporada}_divisao_{divisao}")\
            .update({"jogos": jogos})\
            .eq("numero", rodada_numero)\
            .execute()
        st.success("✅ Resultados salvos e movimentações aplicadas com sucesso!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao salvar resultados: {e}")


