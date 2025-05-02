# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(page_title="Leiloar Jogador - LigaFut", layout="wide")

# Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"<h2 style='text-align: center;'>Leiloar Jogador do {nome_time}</h2><hr>", unsafe_allow_html=True)

# Busca elenco do time
try:
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    st.stop()

if not elenco:
    st.info("Seu elenco está vazio.")
    st.stop()

# Formulário de leilão
with st.form("form_leiloar"):
    jogador_escolhido = st.selectbox(
        "Escolha o jogador para leiloar:",
        options=elenco,
        format_func=lambda x: f"{x.get('nome', 'Desconhecido')} ({x.get('posicao', 'Sem posição')})"
    )

    valor_base = jogador_escolhido.get("valor", 100000)
    valor_base = max(valor_base, 100000)
    valor_minimo = st.number_input(
        "Lance mínimo inicial (R$)",
        min_value=100000,
        value=valor_base,
        step=50000
    )

    duracao = st.slider("Duração do leilão (minutos)", min_value=1, max_value=10, value=2)
    botao_leiloar = st.form_submit_button("Iniciar Leilão")

# Inicia leilão
if botao_leiloar and jogador_escolhido:
    try:
        fim = datetime.utcnow() + timedelta(minutes=duracao)

        dados_leilao = {
            "id": "leilao_sistema",
            "jogador": {
                "nome": jogador_escolhido.get("nome", ""),
                "posicao": jogador_escolhido.get("posicao", "Sem posição"),
                "overall": jogador_escolhido.get("overall", 0),
                "valor": valor_minimo
            },
            "valor_atual": valor_minimo,
            "valor_inicial": valor_minimo,
            "time_vencedor": "",
            "id_time_atual": id_time,
            "ativo": True,
            "fim": fim.isoformat()
        }

        supabase.table("configuracoes").upsert(dados_leilao).execute()

        supabase.table("elenco").delete().eq("id_time", id_time).eq("nome", jogador_escolhido["nome"]).execute()

        st.success("Jogador enviado para o leilão com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao iniciar leilão: {e}")
