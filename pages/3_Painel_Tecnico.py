# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from utils import verificar_login, formatar_valor
from datetime import datetime

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
    res = supabase.table("movimentacoes").select("*").order("data", desc=True).limit(1000).execute()
    movimentacoes = res.data or []

    entradas = []
    saidas = []

    for m in movimentacoes:
        origem = m.get("origem", "") or ""
        destino = m.get("destino", "") or ""

        origem_norm = origem.strip().lower()
        destino_norm = destino.strip().lower()
        nome_time_norm = nome_time.strip().lower()

        if nome_time_norm in destino_norm:
            entradas.append(m)
        elif nome_time_norm in origem_norm:
            saidas.append(m)

    st.markdown("### 🟢 Entradas")
    if entradas:
        df_entradas = pd.DataFrame(entradas)
        df_entradas = df_entradas[["jogador", "valor", "tipo", "categoria", "origem", "data"]]
        df_entradas["valor"] = df_entradas["valor"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
        df_entradas["data"] = pd.to_datetime(df_entradas["data"]).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_entradas)
    else:
        st.info("Nenhuma entrada encontrada.")

    st.markdown("### 🔴 Saídas")
    if saidas:
        df_saidas = pd.DataFrame(saidas)
        df_saidas = df_saidas[["jogador", "valor", "tipo", "categoria", "destino", "data"]]
        df_saidas["valor"] = df_saidas["valor"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
        df_saidas["data"] = pd.to_datetime(df_saidas["data"]).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_saidas)
    else:
        st.info("Nenhuma saída encontrada.")

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")


