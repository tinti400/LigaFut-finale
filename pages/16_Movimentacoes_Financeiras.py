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

# 🎯 Normaliza descrições
df["descricao_lower"] = df["descricao"].str.lower()

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

# 🎯 Calcular totais detalhados
total_salario = df[df["descricao_lower"].str.contains("pagamento de salário")]["valor"].astype(float).sum()
total_bonus = df[df["descricao_lower"].str.contains("bônus de gols")]["valor"].astype(float).sum()
total_premiacao = df[df["descricao_lower"].str.contains("premiação por resultado")]["valor"].astype(float).sum()
total_compras = df[df["descricao_lower"].str.contains("compra de jogador")]["valor"].astype(float).sum()
total_vendas = df[df["descricao_lower"].str.contains("venda de jogador")]["valor"].astype(float).sum()
total_leilao = df[df["descricao_lower"].str.contains("leilão|leilao")]["valor"].astype(float).sum()

# 🧾 Cálculo total geral
total_geral = total_bonus + total_premiacao + total_vendas - total_salario - total_compras - total_leilao

# 🎨 Formatação de valores
def formatar_valor(v, negativo=False):
    try:
        v = float(v)
        if negativo:
            return f"-R${abs(v):,.0f}".replace(",", ".")
        else:
            return f"R${v:,.0f}".replace(",", ".")
    except:
        return "-"

# ➕ Exibir resumo no topo
st.markdown(f"""
<div style='background-color:#eef9f1;padding:20px;border-radius:10px;margin-bottom:15px;border: 1px solid #CCC'>
<ul style='font-size:17px;list-style:none;padding-left:10px'>
<li>🛒 Compras de Jogadores: <strong style='color:red'>{formatar_valor(total_compras, negativo=True)}</strong></li>
<li>📤 Vendas de Jogadores: <strong style='color:green'>{formatar_valor(total_vendas)}</strong></li>
<li>🥅 Bônus por Gol: <strong style='color:green'>{formatar_valor(total_bonus)}</strong></li>
<li>🏆 Premiação por Resultado: <strong style='color:green'>{formatar_valor(total_premiacao)}</strong></li>
<li>💼 Pagamento de Salário: <strong style='color:red'>{formatar_valor(total_salario, negativo=True)}</strong></li>
<li>🔨 Gastos com Leilões: <strong style='color:red'>{formatar_valor(total_leilao, negativo=True)}</strong></li>
</ul>
<p style='font-size:20px;margin-top:10px'><strong>💰 Total Geral: <span style='color:{"green" if total_geral >= 0 else "red"}'>{formatar_valor(total_geral, negativo=(total_geral < 0))}</span></strong></p>
<p style='font-size:16px;margin-top:10px'>📦 <strong>Saldo Atual do Time:</strong> {formatar_valor(saldo_atual)}</p>
</div>
""", unsafe_allow_html=True)

# 🧾 Tabela final formatada
df["💰 Caixa Atual"] = df["caixa_atual"].apply(formatar_valor)
df["📦 Caixa Anterior"] = df["caixa_anterior"].apply(formatar_valor)
df["💸 Valor"] = df.apply(lambda row: formatar_valor(row["valor"], negativo=("compra de jogador" in row["descricao_lower"] or "pagamento de salário" in row["descricao_lower"] or "leilão" in row["descricao_lower"])), axis=1)
df["📅 Data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")
df["📌 Tipo"] = df["tipo"].astype(str).str.capitalize()
df["📝 Descrição"] = df["descricao"].astype(str)

colunas = ["📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"]
df_exibir = df[colunas].copy()
df_exibir = df_exibir.fillna("").astype(str)

# 🧾 Exibir extrato
st.subheader(f"📁 Extrato do time {nome_time}")
try:
    st.dataframe(df_exibir, use_container_width=True)
except Exception:
    st.warning("⚠️ Erro ao exibir com `st.dataframe`. Exibindo com `st.table()`.")
    st.table(df_exibir)
