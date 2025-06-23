# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import verificar_sessao

st.set_page_config(page_title="📊 Movimentações Financeiras", layout="wide")
st.title("📊 Histórico de Movimentações Financeiras")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verifica login
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu Time")

# 🔄 Buscar movimentações
res = supabase.table("movimentacoes_financeiras")\
    .select("*")\
    .eq("id_time", id_time)\
    .order("data", desc=True)\
    .execute()

if not res.data:
    st.info("Nenhuma movimentação encontrada.")
    st.stop()

# 📊 Converter para DataFrame
df = pd.DataFrame(res.data)
df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y %H:%M")
df["valor"] = df["valor"].apply(lambda x: f"R${x:,.0f}".replace(",", "."))
df["caixa_anterior"] = df["caixa_anterior"].apply(lambda x: f"R${x:,.0f}".replace(",", "."))
df["caixa_atual"] = df["caixa_atual"].apply(lambda x: f"R${x:,.0f}".replace(",", "."))

# 🔀 Reorganizar colunas
df = df[["data", "tipo", "descricao", "valor", "caixa_anterior", "caixa_atual"]]
df = df.rename(columns={
    "data": "📅 Data",
    "tipo": "📌 Tipo",
    "descricao": "📝 Descrição",
    "valor": "💸 Valor",
    "caixa_anterior": "📦 Caixa Anterior",
    "caixa_atual": "💰 Caixa Atual"
})

# 🎨 Estilo da tabela
st.markdown(f"### 💼 Movimentações do time **{nome_time}**")
st.dataframe(df, use_container_width=True)
