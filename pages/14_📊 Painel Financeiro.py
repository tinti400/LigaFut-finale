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
res = supabase.table("movimentacoes").select("*").order("data", desc=True).limit(500).execute()
movs = res.data if res.data else []

if not movs:
    st.info("Nenhuma movimentação registrada ainda.")
    st.stop()

# 🔁 Converter para DataFrame
df = pd.DataFrame(movs)

# 🛠️ Depuração: mostrar colunas reais da base
st.subheader("🧪 Colunas encontradas na base de dados:")
st.write(df.columns.tolist())

# ⏱️ Ajustar data e valor
if "data" in df.columns:
    df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y %H:%M")

if "valor" in df.columns:
    df["valor"] = df["valor"].astype(float).apply(lambda x: f'R${x:,.0f}'.replace(",", ".").replace(".", ",", 1))

# 🏷️ Renomear colunas com ícones, se existirem
colunas_renomear = {
    "data": "📅 Data",
    "tipo": "📁 Tipo",
    "valor": "💰 Valor",
    "jogador": "👤 Jogador",
    "origem": "🏳️ Origem",
    "destino": "🏁 Destino"
}

colunas_existentes_renomear = {k: v for k, v in colunas_renomear.items() if k in df.columns}
df = df.rename(columns=colunas_existentes_renomear)

# 🔍 Filtros
col1, col2 = st.columns(2)

lista_times = sorted(set(df.get("🏳️ Origem", pd.Series()).dropna().tolist() + df.get("🏁 Destino", pd.Series()).dropna().tolist()))
tipos = sorted(df.get("📁 Tipo", pd.Series()).dropna().unique())

with col1:
    filtro_time = st.selectbox("🎯 Filtrar por Time", ["Todos"] + lista_times)

with col2:
    filtro_tipo = st.selectbox("📂 Filtrar por Tipo de Movimento", ["Todos"] + tipos)

# 🎯 Aplicar filtros
df_filtrado = df.copy()

if filtro_time != "Todos":
    df_filtrado = df_filtrado[(df_filtrado["🏳️ Origem"] == filtro_time) | (df_filtrado["🏁 Destino"] == filtro_time)]

if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["📁 Tipo"] == filtro_tipo]

# 📋 Exibir resultado final com segurança
st.markdown(f"<h4 style='margin-top:30px;'>🔽 Total de {len(df_filtrado)} movimentações encontradas</h4>", unsafe_allow_html=True)

colunas_exibicao = ["📅 Data", "📁 Tipo", "💰 Valor", "👤 Jogador", "🏳️ Origem", "🏁 Destino"]
colunas_existentes = [col for col in colunas_exibicao if col in df_filtrado.columns]

if colunas_existentes:
    st.dataframe(df_filtrado[colunas_existentes], use_container_width=True)
else:
    st.warning("⚠️ Nenhuma coluna disponível para exibição.")


