# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from utils import verificar_login, formatar_valor

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verifica login
verificar_login()
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 💰 Busca saldo
saldo = 0
res = supabase.table("times").select("saldo").eq("id", id_time).execute()
if res.data:
    saldo = res.data[0].get("saldo", 0)

st.markdown("<h2 style='text-align: center;'>📊 Painel do Técnico</h2><hr>", unsafe_allow_html=True)
st.markdown(f"### 🏷️ Time: {nome_time} &nbsp;&nbsp;&nbsp;&nbsp; 💰 Saldo: {formatar_valor(saldo)}")

# 📌 Seletor de aba
aba = st.radio("📂 Selecione o tipo de movimentação", ["📥 Entradas", "💸 Saídas", "📊 Resumo"])

# 🔄 Carregar movimentações
try:
    dados = supabase.table("movimentacoes").select("*").order("data", desc=True).execute().data
    entradas, saidas = [], []

    for m in dados:
        jogador = m.get("jogador", "Desconhecido")
        valor = m.get("valor", 0)
        tipo = m.get("tipo", "").capitalize()
        categoria = m.get("categoria", "-")
        origem = m.get("origem", "-")
        destino = m.get("destino", "-")
        data = m.get("data", "-")

        envolvido = nome_time.lower() in (str(origem).lower() + str(destino).lower())
        if not envolvido:
            continue

        registro = {
            "Jogador": jogador,
            "Valor (R$)": formatar_valor(valor),
            "Tipo": tipo,
            "Categoria": categoria,
            "Origem": origem,
            "Destino": destino,
            "Data": data
        }

        if destino.lower() == nome_time.lower():
            entradas.append(registro)
        elif origem.lower() == nome_time.lower():
            saidas.append(registro)

    if aba == "📥 Entradas":
        st.markdown("### ✅ Jogadores recebidos")
        df = pd.DataFrame(entradas) if entradas else pd.DataFrame(columns=["Jogador", "Valor (R$)", "Tipo", "Categoria", "Origem", "Destino", "Data"])
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma entrada registrada.")

    elif aba == "💸 Saídas":
        st.markdown("### ❌ Jogadores vendidos")
        df = pd.DataFrame(saidas) if saidas else pd.DataFrame(columns=["Jogador", "Valor (R$)", "Tipo", "Categoria", "Origem", "Destino", "Data"])
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma saída registrada.")

    elif aba == "📊 Resumo":
        total_entrada = sum(float(m.get("valor", 0)) for m in entradas)
        total_saida = sum(float(m.get("valor", 0)) for m in saidas)
        saldo_final = total_entrada - total_saida

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Entradas", formatar_valor(total_entrada))
        col2.metric("💸 Total Saídas", formatar_valor(total_saida))
        col3.metric("📈 Saldo Líquido", formatar_valor(saldo_final))

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")

