# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from utils import verificar_login

# 🛠️ Configuração da página
st.set_page_config(page_title="Painel do Técnico", page_icon="📋", layout="wide")
st.markdown("## 📋 Painel do Técnico")

# 🔐 Verificar login
verificar_login()

# 🔌 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados da sessão
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu Time")

st.markdown(f"### 👤 Técnico do {nome_time}")

# 🔎 Buscar movimentações com base no nome do time (entrada e saída)
try:
    res = supabase.table("movimentacoes").select("*").order("id", desc=True).limit(1000).execute()
    movimentacoes = res.data or []

    entradas = []
    saidas = []

    for m in movimentacoes:
        origem = (m.get("origem") or "").strip().lower()
        destino = (m.get("destino") or "").strip().lower()
        nome_normalizado = nome_time.strip().lower()

        if nome_normalizado in destino:
            entradas.append(m)
        elif nome_normalizado in origem:
            saidas.append(m)

    # 🟢 ENTRADAS
    st.markdown("### 🟢 Entradas")
    if entradas:
        df_entradas = pd.DataFrame(entradas)
        df_entradas = df_entradas[["jogador", "valor", "tipo", "categoria", "origem"]]
        df_entradas["valor"] = df_entradas["valor"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
        st.dataframe(df_entradas)
    else:
        st.info("Nenhuma entrada registrada.")

    # 🔴 SAÍDAS
    st.markdown("### 🔴 Saídas")
    if saidas:
        df_saidas = pd.DataFrame(saidas)
        df_saidas = df_saidas[["jogador", "valor", "tipo", "categoria", "destino"]]
        df_saidas["valor"] = df_saidas["valor"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
        st.dataframe(df_saidas)
    else:
        st.info("Nenhuma saída registrada.")

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")


