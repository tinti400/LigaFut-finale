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
    res_times = supabase.table("times").select("id, nome, saldo").order("nome", desc=False).execute()
    times = res_times.data or []
    if not times:
        st.warning("Nenhum time encontrado.")
        st.stop()

    nome_para_dados = {t["nome"]: (t["id"], t["saldo"]) for t in times}
    nome_selecionado = st.selectbox("👑 Selecione um time para visualizar o extrato:", list(nome_para_dados.keys()))
    id_time, saldo_atual = nome_para_dados[nome_selecionado]
    nome_time = nome_selecionado
else:
    id_time = st.session_state["id_time"]
    nome_time = st.session_state.get("nome_time", "Seu Time")
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
df["valor"] = df.get("valor", 0)
df["tipo"] = df.get("tipo", "saida")
df["descricao"] = df.get("descricao", "Sem descrição")

# 💰 Calcular caixa anterior e atual (somente visual, saldo_atual não entra no cálculo)
saldos_atuais = []
saldos_anteriores = []
saldo_temp = 0

for _, row in df.iterrows():
    valor = float(row.get("valor", 0))
    tipo = row.get("tipo", "saida")
    if tipo == "entrada":
        saldo_anterior = saldo_temp
        saldo_temp += valor
    else:
        saldo_anterior = saldo_temp
        saldo_temp -= valor
    saldos_anteriores.append(saldo_anterior)
    saldos_atuais.append(saldo_temp)

df["caixa_anterior"] = saldos_anteriores
df["caixa_atual"] = saldos_atuais

# 🔍 Totais
df["descricao_lower"] = df["descricao"].str.lower()

total_salario = df[df["descricao_lower"].str.contains("pagamento de salário")]["valor"].astype(float).sum()
total_compras = df[df["descricao_lower"].str.contains("compra de jogador")]["valor"].astype(float).sum()
total_bonus = df[df["descricao_lower"].str.contains("bônus de gols")]["valor"].astype(float).sum()
total_premiacao = df[df["descricao_lower"].str.contains("premiação por resultado")]["valor"].astype(float).sum()
total_vendas = df[df["descricao_lower"].str.contains("venda de jogador")]["valor"].astype(float).sum()

# 🧾 Cálculo total geral
total_geral = total_bonus + total_premiacao + total_vendas - total_salario - total_compras

# 🎨 Função formatar valor
def formatar_valor(v, negativo=False):
    try:
        v = float(v)
        prefix = "-" if negativo or v < 0 else ""
        return f"{prefix}R${abs(v):,.0f}".replace(",", ".")
    except:
        return "-"

# 🔎 Monta colunas formatadas
df["💰 Caixa Atual"] = df["caixa_atual"].apply(formatar_valor)
df["📦 Caixa Anterior"] = df["caixa_anterior"].apply(formatar_valor)
df["💸 Valor"] = df["valor"].apply(formatar_valor)
df["📅 Data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")
df["📌 Tipo"] = df["tipo"].astype(str).str.capitalize()
df["📝 Descrição"] = df["descricao"].astype(str)

# 🧾 Exibir Resumo com destaque
st.markdown(f"""
<div style='background-color:#f0f9ff;padding:25px;border-radius:10px;margin-bottom:20px;border-left:5px solid #2c91e2'>
    <h2>📋 <strong>Resumo Financeiro - {nome_time}</strong></h2>
    <ul style='font-size:18px;margin-left:10px'>
        <li>💼 <strong>Salários Pagos:</strong> <span style='color:red'>{formatar_valor(total_salario, negativo=True)}</span></li>
        <li>🛒 <strong>Compras de Jogadores:</strong> <span style='color:red'>{formatar_valor(total_compras, negativo=True)}</span></li>
        <li>📤 <strong>Vendas de Jogadores:</strong> <span style='color:green'>{formatar_valor(total_vendas)}</span></li>
        <li>🥅 <strong>Bônus por Gol:</strong> <span style='color:green'>{formatar_valor(total_bonus)}</span></li>
        <li>🏆 <strong>Premiação por Resultado:</strong> <span style='color:green'>{formatar_valor(total_premiacao)}</span></li>
    </ul>
    <p style='font-size:20px;margin-top:10px'><strong>💰 Total Geral: <span style='color:{"green" if total_geral >= 0 else "red"}'>{formatar_valor(total_geral)}</span></strong></p>
    <p style='font-size:18px'>📦 <strong>Saldo Atual do Time:</strong> <span style='color:#000'>{formatar_valor(saldo_atual)}</span></p>
</div>
""", unsafe_allow_html=True)

# Exibir tabela
df_exibir = df[["📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"]].copy()
df_exibir = df_exibir.fillna("").astype(str)

st.subheader(f"📁 Extrato do time {nome_time}")

try:
    st.dataframe(df_exibir, use_container_width=True)
except Exception:
    st.warning("⚠️ Erro ao exibir com `st.dataframe`. Exibindo com `st.table()`.")
    st.table(df_exibir)
