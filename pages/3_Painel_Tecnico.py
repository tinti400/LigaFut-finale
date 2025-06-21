# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_login
import pandas as pd

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_login()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 💰 Buscar saldo
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)
st.markdown(f"### 🏷️ Time: {nome_time} &nbsp;&nbsp;&nbsp;&nbsp; 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

# 📂 Tipo de movimentação
aba = st.radio("Selecione a visualização", ["📥 Entradas", "💸 Saídas", "📊 Resumo"])

# 🔄 Carrega todas as movimentações registradas
movs = supabase.table("movimentacoes").select("*").order("data", desc=True).execute().data

# 🔍 Processamento
entradas, saidas = [], []
total_entrada = total_saida = 0

for m in movs:
    jogador = m.get("jogador", "Desconhecido")
    valor = m.get("valor", 0)
    tipo = m.get("tipo", "")
    categoria = m.get("categoria", "")
    data = m.get("data", "")[:16].replace("T", " ")
    origem = m.get("origem", "")
    destino = m.get("destino", "")

    entrada = destino and destino.strip().lower() == nome_time.strip().lower()
    saida = origem and origem.strip().lower() == nome_time.strip().lower()

    registro = {
        "Jogador": jogador,
        "Valor (R$)": f"R$ {abs(valor):,.0f}".replace(",", "."),
        "Tipo": tipo.capitalize(),
        "Categoria": categoria.capitalize(),
        "Origem": origem or "-",
        "Destino": destino or "-",
        "Data": data or "-"
    }

    if entrada:
        entradas.append(registro)
        total_entrada += valor
    elif saida:
        saidas.append(registro)
        total_saida += valor

# 📊 Exibição
if aba == "📥 Entradas":
    st.markdown("### 📥 Jogadores que chegaram")
    df = pd.DataFrame(entradas)
    st.dataframe(df, use_container_width=True)

elif aba == "💸 Saídas":
    st.markdown("### 💸 Jogadores que saíram")
    df = pd.DataFrame(saidas)
    st.dataframe(df, use_container_width=True)

else:
    st.markdown("### 📊 Resumo Financeiro")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total em Entradas", f"R$ {total_entrada:,.0f}".replace(",", "."))
    col2.metric("💸 Total em Saídas", f"R$ {total_saida:,.0f}".replace(",", "."))
    lucro_prejuizo = total_entrada - total_saida
    if lucro_prejuizo >= 0:
        col3.success(f"📈 Lucro: R$ {lucro_prejuizo:,.0f}".replace(",", "."))
    else:
        col3.error(f"📉 Prejuízo: R$ {abs(lucro_prejuizo):,.0f}".replace(",", "."))


