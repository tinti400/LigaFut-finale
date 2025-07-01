# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import verificar_sessao

st.set_page_config(page_title="📊 Movimentações Financeiras", layout="wide")
st.title("📊 Extrato Financeiro")

# 🔐 Conexão Supabase
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

# 💰 Calcular caixa anterior e atual
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

# 🎯 Calcular totais
df["descricao_lower"] = df["descricao"].str.lower()

total_salario = df[df["descricao_lower"].str.contains("pagamento de salário")]["valor"].astype(float).sum()
total_bonus = df[df["descricao_lower"].str.contains("bônus de gols")]["valor"].astype(float).sum()
total_premiacao = df[df["descricao_lower"].str.contains("premiação por resultado")]["valor"].astype(float).sum()
total_compras_registro = df[df["descricao_lower"].str.contains("compra de")]["valor"].astype(float).sum()
total_vendas_registro = df[df["descricao_lower"].str.contains("venda de")]["valor"].astype(float).sum()

# 🔍 Buscar lances no BID (leilão)
res_bid = supabase.table("bid").select("valor_final, vencedor_id, origem_id").or_(
    f"vencedor_id.eq.{id_time},origem_id.eq.{id_time}"
).execute()

lances = res_bid.data or []
total_compras_leilao = 0
total_vendas_leilao = 0

for lance in lances:
    valor = float(lance.get("valor_final", 0))
    if lance.get("vencedor_id") == id_time:
        total_compras_leilao += valor
    elif lance.get("origem_id") == id_time:
        total_vendas_leilao += valor

# 🎯 Totais finais
total_compras = total_compras_registro + total_compras_leilao
total_vendas = total_vendas_registro + total_vendas_leilao
total_geral = total_bonus + total_premiacao + total_vendas - total_salario - total_compras

# 🎨 Função de formatação
def formatar_valor(v, negativo=False):
    try:
        v = float(v)
        return f"{'-' if negativo else ''}R${abs(v):,.0f}".replace(",", ".")
    except:
        return "-"

# 🧾 Bloco de Totais
st.markdown(f"""
<div style='background-color:#f9f9f9;padding:20px;border-radius:10px;margin-bottom:15px'>
<h4>💰 <strong>Resumo Financeiro</strong></h4>
<ul style='font-size:17px'>
<li>🛒 Compras de Jogadores (Total): <strong style='color:red'>{formatar_valor(total_compras, negativo=True)}</strong></li>
<ul style='margin-left:20px'>
<li>↳ Registro: {formatar_valor(total_compras_registro, negativo=True)}</li>
<li>↳ Leilão (BID): {formatar_valor(total_compras_leilao, negativo=True)}</li>
</ul>
<li>📤 Vendas de Jogadores (Total): <strong style='color:green'>{formatar_valor(total_vendas)}</strong></li>
<ul style='margin-left:20px'>
<li>↳ Registro: {formatar_valor(total_vendas_registro)}</li>
<li>↳ Leilão (BID): {formatar_valor(total_vendas_leilao)}</li>
</ul>
<li>🥅 Bônus por Gol: <strong style='color:green'>{formatar_valor(total_bonus)}</strong></li>
<li>🏆 Premiação por Resultado: <strong style='color:green'>{formatar_valor(total_premiacao)}</strong></li>
<li>💼 Pagamento de Salário: <strong style='color:red'>{formatar_valor(total_salario, negativo=True)}</strong></li>
</ul>
<p style='font-size:20px;margin-top:10px'><strong>📊 Total Geral: <span style='color:{"green" if total_geral >= 0 else "red"}'>{formatar_valor(total_geral, negativo=(total_geral < 0))}</span></strong></p>
<p style='font-size:16px;margin-top:10px'>📦 <strong>Saldo Atual do Time:</strong> {formatar_valor(saldo_atual)}</p>
</div>
""", unsafe_allow_html=True)

# 🧾 Exibir extrato
df["💰 Caixa Atual"] = df["caixa_atual"].apply(formatar_valor)
df["📦 Caixa Anterior"] = df["caixa_anterior"].apply(formatar_valor)
df["💸 Valor"] = df["valor"].apply(formatar_valor)
df["📅 Data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")
df["📌 Tipo"] = df["tipo"].astype(str).str.capitalize()
df["📝 Descrição"] = df["descricao"].astype(str)

colunas = ["📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"]
df_exibir = df[colunas].copy().fillna("").astype(str)

st.subheader(f"📁 Extrato do time {nome_time}")
try:
    st.dataframe(df_exibir, use_container_width=True)
except Exception:
    st.warning("⚠️ Erro ao exibir com `st.dataframe`. Exibindo com `st.table()`.")
    st.table(df_exibir)
