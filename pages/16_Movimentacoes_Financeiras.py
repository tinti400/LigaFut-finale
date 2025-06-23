# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import verificar_sessao

st.set_page_config(page_title="📊 Movimentações Financeiras", layout="wide")
st.title("📊 Extrato Financeiro")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verifica login
verificar_sessao()
email_usuario = st.session_state.get("usuario", "")
usuario_id = st.session_state["usuario_id"]

# 👑 Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
is_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔽 Se admin, seleciona time
if is_admin:
    res_times = supabase.table("times").select("id, nome").order("nome", desc=False).execute()
    times = res_times.data or []
    if not times:
        st.warning("Nenhum time encontrado.")
        st.stop()

    nome_para_id = {t["nome"]: t["id"] for t in times}
    nome_selecionado = st.selectbox("👑 Selecione um time para visualizar o extrato:", list(nome_para_id.keys()))
    id_time = nome_para_id[nome_selecionado]
    nome_time = nome_selecionado
else:
    id_time = st.session_state["id_time"]
    nome_time = st.session_state.get("nome_time", "Seu Time")

# 📥 Buscar saldo atual
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).single().execute()
saldo_atual = res_saldo.data.get("saldo", 0)

# 📥 Buscar movimentações
res_mov = supabase.table("movimentacoes_financeiras")\
    .select("*")\
    .eq("id_time", id_time)\
    .order("data", desc=True)\
    .execute()

movs = res_mov.data
if not movs:
    st.info("Nenhuma movimentação encontrada.")
    st.stop()

# 📊 Criar DataFrame
df = pd.DataFrame(movs)
df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data"])
df = df.sort_values("data", ascending=False)

# 🛡️ Garante colunas básicas
if "valor" not in df.columns:
    df["valor"] = 0
if "tipo" not in df.columns:
    df["tipo"] = "saida"
if "descricao" not in df.columns:
    df["descricao"] = "Sem descrição"

# 🔁 Calcular caixa anterior e atual
saldos_atuais = []
saldos_anteriores = []
saldo = saldo_atual

for _, row in df.iterrows():
    valor = float(row.get("valor", 0))
    tipo = row.get("tipo", "saida")
    if tipo == "entrada":
        saldo_anterior = saldo - valor
    else:
        saldo_anterior = saldo + valor

    saldos_anteriores.append(saldo_anterior)
    saldos_atuais.append(saldo)
    saldo = saldo_anterior

df["caixa_atual"] = saldos_atuais
df["caixa_anterior"] = saldos_anteriores

# 🎨 Formatação
def formatar_valor(v):
    try:
        return f"R${float(v):,.0f}".replace(",", ".")
    except:
        return "-"

df["💰 Caixa Atual"] = df["caixa_atual"].apply(formatar_valor)
df["📦 Caixa Anterior"] = df["caixa_anterior"].apply(formatar_valor)
df["💸 Valor"] = df["valor"].apply(formatar_valor)
df["📅 Data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")
df["📌 Tipo"] = df["tipo"].astype(str).str.capitalize()
df["📝 Descrição"] = df["descricao"].astype(str)

# Seleção final de colunas
colunas = ["📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"]
df_exibir = df[colunas].copy()

# Força todas as colunas como string
for col in df_exibir.columns:
    df_exibir[col] = df_exibir[col].astype(str)

# 🔍 Debug (opcional - pode remover depois)
st.subheader("🔍 Debug do DataFrame")
st.write("Colunas:", df_exibir.columns.tolist())
st.text("Tipos de dados:")
st.text(df_exibir.dtypes.to_string())
st.write("Amostra dos dados:")
st.write(df_exibir.head())

# 📋 Exibir
st.subheader(f"💼 Extrato do time **{nome_time}**")
st.dataframe(df_exibir, use_container_width=True)


