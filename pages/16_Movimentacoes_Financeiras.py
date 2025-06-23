# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import verificar_sessao

st.set_page_config(page_title="📊 Movimentações Financeiras", layout="wide")
st.title("📊 Extrato Financeiro do Time")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verifica login
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu Time")

# 📥 Buscar saldo atual
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).single().execute()
saldo_atual = res_saldo.data["saldo"]

# 📥 Buscar movimentações financeiras (ordem decrescente)
res_mov = supabase.table("movimentacoes_financeiras")\
    .select("*")\
    .eq("id_time", id_time)\
    .order("data", desc=True)\
    .execute()

movs = res_mov.data
if not movs:
    st.info("Nenhuma movimentação encontrada.")
    st.stop()

# 📊 Criar DataFrame e converter datas
df = pd.DataFrame(movs)
df["data"] = pd.to_datetime(df["data"])
df = df.sort_values("data", ascending=False)

# 🔄 Calcular saldo anterior e saldo atual linha a linha
saldos_atuais = []
saldos_anteriores = []
saldo = saldo_atual

for _, row in df.iterrows():
    valor = row["valor"]
    if row["tipo"] == "entrada":
        saldo_anterior = saldo - valor
    else:  # saída
        saldo_anterior = saldo + valor

    saldos_anteriores.append(saldo_anterior)
    saldos_atuais.append(saldo)

    saldo = saldo_anterior  # para a próxima linha

# 🧮 Adicionar colunas de saldo
df["caixa_atual"] = saldos_atuais
df["caixa_anterior"] = saldos_anteriores

# 🎨 Formatar valores
def formatar_valor(v):
    try:
        return f"R${v:,.0f}".replace(",", ".")
    except:
        return "-"

df["💰 Caixa Atual"] = df["caixa_atual"].apply(formatar_valor)
df["📦 Caixa Anterior"] = df["caixa_anterior"].apply(formatar_valor)
df["💸 Valor"] = df["valor"].apply(formatar_valor)
df["📅 Data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")
df["📌 Tipo"] = df["tipo"].str.capitalize()
df["📝 Descrição"] = df["descricao"]

# 🔽 Selecionar colunas finais
df_exibir = df[[
    "📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"
]]

# 📋 Exibir
st.markdown(f"### 💼 Extrato do time **{nome_time}**")
st.dataframe(df_exibir, use_container_width=True)
