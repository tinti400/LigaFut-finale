# 98_painel_destino_jogadores.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime

st.set_page_config(page_title="📥 Jogadores Destino", layout="wide")
verificar_sessao()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔎 Info usuário
id_time = st.session_state.get("id_time")
if not id_time:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.markdown("## 📥 Jogadores para Adição ao Elenco")
st.markdown("---")

# 🎯 Filtros
todos_jogadores = supabase.table("jogadores_base").select("*").execute().data

nome_busca = st.text_input("🔍 Buscar por nome").strip().lower()
nacionalidades = sorted(list(set(j["nacionalidade"] for j in todos_jogadores if j.get("nacionalidade"))))
nacionalidade_selecionada = st.selectbox("🌎 Filtrar por nacionalidade", ["Todos"] + nacionalidades)
overall_min = st.slider("📊 Filtrar por overall mínimo", min_value=0, max_value=99, value=0)

# 🎯 Aplica filtros
jogadores_filtrados = []
for jogador in todos_jogadores:
    nome = jogador.get("nome", "").lower()
    nacionalidade = jogador.get("nacionalidade", "")
    overall = jogador.get("overall") or 0

    if nome_busca and nome_busca not in nome:
        continue
    if nacionalidade_selecionada != "Todos" and nacionalidade != nacionalidade_selecionada:
        continue
    if overall < overall_min:
        continue

    jogadores_filtrados.append(jogador)

# 🎲 Mostra jogadores filtrados
for jogador in jogadores_filtrados:
    st.markdown("---")
    col1, col2 = st.columns([1, 5])

    with col1:
        st.image(jogador.get("imagem_url", "https://via.placeholder.com/80x80.png"), width=80)

    with col2:
        st.markdown(f"**{jogador.get('nome')}**")
        st.markdown(f"**Posição:** {jogador.get('posicao')} &nbsp;&nbsp;|&nbsp;&nbsp; **Overall:** {jogador.get('overall', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; **Origem:** {jogador.get('origem', 'N/A')}")
        st.markdown(f"**Nacionalidade:** {jogador.get('nacionalidade', 'N/A')}")

        valor_input = st.number_input(f"💰 Valor (R$) para {jogador.get('nome')}", min_value=0, value=int(jogador.get("valor") or 0), step=500000, key=f"valor_{jogador['id']}")

        if st.button(f"✅ Adicionar ao meu elenco", key=f"add_{jogador['id']}"):
            try:
                salario = int(valor_input * 0.007)
                novo = {
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador.get("posicao"),
                    "overall": jogador.get("overall"),
                    "valor": valor_input,
                    "nacionalidade": jogador.get("nacionalidade"),
                    "origem": jogador.get("origem"),
                    "imagem_url": jogador.get("imagem_url"),
                    "foto": jogador.get("foto"),
                    "classificacao": "sem classificacao",
                    "jogos": 0,
                    "numero_camisa": None,
                    "salario": salario,
                    "link_sofifa": jogador.get("link_sofifa")
                }

                supabase.table("elenco").insert(novo).execute()
                st.success(f"✅ Jogador {jogador['nome']} adicionado ao elenco com sucesso!")

            except Exception as e:
                st.error("❌ Erro ao adicionar jogador ao elenco.")
                st.exception(e)
