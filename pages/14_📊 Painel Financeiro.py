# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📊 Painel Financeiro", layout="wide")
st.markdown("<h1 style='text-align:center;'>📊 Painel Financeiro da LigaFut</h1><hr>", unsafe_allow_html=True)

# ✅ Buscar movimentações
res = supabase.table("movimentacoes").select("*").order("created_at", desc=True).limit(500).execute()
movs = res.data if res.data else []

if not movs:
    st.info("Nenhuma movimentação registrada ainda.")
    st.stop()

# 🔁 Converter para DataFrame
df = pd.DataFrame(movs)
df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
df["valor"] = df["valor"].astype(float).apply(lambda x: f'R${x:,.0f}'.replace(",", ".").replace(".", ",", 1))

# ✅ Renomear colunas para exibição
df = df.rename(columns={
    "created_at": "📅 Data",
    "tipo": "📁 Tipo",
    "valor": "💰 Valor",
    "jogador": "👤 Jogador",
    "origem": "🏳️ Origem",
    "destino": "🏁 Destino"
})

# 🔍 Filtros de busca
col1, col2 = st.columns(2)

lista_times = sorted(set(df["🏳️ Origem"].dropna().tolist() + df["🏁 Destino"].dropna().tolist()))
tipos = sorted(df["📁 Tipo"].dropna().unique())

with col1:
    filtro_time = st.selectbox("🎯 Filtrar por Time", ["Todos"] + lista_times)

with col2:
    filtro_tipo = st.selectbox("📂 Filtrar por Tipo de Movimento", ["Todos"] + tipos)

# 📉 Aplicar filtros
df_filtrado = df.copy()

if filtro_time != "Todos":
    df_filtrado = df_filtrado[(df_filtrado["🏳️ Origem"] == filtro_time) | (df_filtrado["🏁 Destino"] == filtro_time)]

if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["📁 Tipo"] == filtro_tipo]

# 📋 Exibir tabela final
st.markdown(f"<h4 style='margin-top:30px;'>🔽 Total de {len(df_filtrado)} movimentações encontradas</h4>", unsafe_allow_html=True)
st.dataframe(df_filtrado[["📅 Data", "📁 Tipo", "💰 Valor", "👤 Jogador", "🏳️ Origem", "🏁 Destino"]], use_container_width=True)
