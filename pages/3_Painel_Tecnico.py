# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from utils import verificar_login, formatar_valor

# ⚙️ Configuração da página
st.set_page_config(page_title="Painel do Técnico", page_icon="📋", layout="wide")
st.markdown("## 📋 Painel do Técnico")

# 🔒 Verifica login
verificar_login()

# 🔗 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados da sessão
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu Time")
nome_normalizado = nome_time.strip().lower()

st.markdown(f"### 👤 Técnico do {nome_time}")

# 🔄 Buscar movimentações
try:
    res = supabase.table("movimentacoes").select("*").order("id", desc=True).limit(1000).execute()
    movimentacoes = res.data or []

    entradas, saidas = [], []

    for m in movimentacoes:
        origem = (m.get("origem") or "").strip().lower()
        destino = (m.get("destino") or "").strip().lower()
        if nome_normalizado in destino:
            entradas.append(m)
        elif nome_normalizado in origem:
            saidas.append(m)

    def exibir_tabela(titulo, dados, tipo_movimentacao):
        if not dados:
            st.info(f"Nenhuma movimentação de {titulo.lower()} registrada.")
            return

        st.markdown(f"### {titulo}")

        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 3])
        col1.markdown("**👤 Jogador**")
        col2.markdown("**💰 Valor**")
        col3.markdown("**📦 Tipo**")
        col4.markdown("**📁 Categoria**")
        col5.markdown("**🏷️ " + ("Origem" if tipo_movimentacao == "entrada" else "Destino") + "**")

        for m in dados:
            jogador = m.get("jogador", "Desconhecido")
            valor = formatar_valor(m.get("valor", 0))
            tipo = m.get("tipo", "-").capitalize()
            categoria = m.get("categoria", "-").capitalize()
            ref = m.get("origem") if tipo_movimentacao == "entrada" else m.get("destino")

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 3])
            col1.markdown(jogador)
            col2.markdown(valor)
            col3.markdown(tipo)
            col4.markdown(categoria)
            col5.markdown(ref or "-")

        st.markdown("---")

    exibir_tabela("🟢 Entradas", entradas, "entrada")
    exibir_tabela("🔴 Saídas", saidas, "saida")

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")


