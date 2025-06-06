# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(page_title="Leiloar Jogador - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Dados do time
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"<h2 style='text-align: center;'>📤 Leiloar Jogador do {nome_time}</h2><hr>", unsafe_allow_html=True)

# 🔍 Buscar elenco
try:
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    st.stop()

if not elenco:
    st.info("Seu elenco está vazio.")
    st.stop()

# 📄 Formulário
with st.form("form_leiloar"):
    jogador_escolhido = st.selectbox(
        "Escolha o jogador para leiloar:",
        options=elenco,
        format_func=lambda x: f"{x.get('nome', '')} ({x.get('posicao', '')})"
    )

    valor_base = jogador_escolhido.get("valor", 100000)
    valor_minimo = st.number_input("Valor Inicial do Leilão (R$)", min_value=100000, value=valor_base, step=50000)
    incremento = st.number_input("Incremento Mínimo (R$)", min_value=100000, value=3000000, step=50000)
    duracao = st.slider("Duração do Leilão (minutos)", 1, 10, value=2)
    botao = st.form_submit_button("Iniciar Leilão")

# 🚀 Iniciar leilão
if botao:
    try:
        agora = datetime.utcnow()
        fim = agora + timedelta(minutes=duracao)

        dados_leilao = {
            "nome_jogador": jogador_escolhido["nome"],
            "posicao_jogador": jogador_escolhido["posicao"],
            "overall_jogador": jogador_escolhido["overall"],
            "valor_inicial": valor_minimo,
            "valor_atual": valor_minimo,
            "incremento_minimo": incremento,
            "id_time_atual": id_time,
            "ultimo_lance": None,
            "inicio": None,
            "fim": None,
            "ativo": False,
            "finalizado": False,
            "time_vencedor": "",
            "id_time_vendedor": id_time,
            "nome_time_vendedor": nome_time
        }

        supabase.table("leiloes").insert(dados_leilao).execute()
        st.success("✅ Jogador adicionado à fila de leilões com sucesso!")
        st.experimental_rerun()

    except Exception as e:
        st.error(f"Erro ao iniciar o leilão: {e}")
