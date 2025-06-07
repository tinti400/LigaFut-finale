# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from dateutil.parser import parse

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔢 Buscar saldo
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
except Exception as e:
    st.error(f"Erro ao carregar saldo: {e}")
    saldo = 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🏷️ Time: {nome_time}")
with col2:
    st.markdown(f"### 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

st.markdown("---")
st.subheader("📥 Compras (Entradas)")

try:
    movimentacoes = supabase.table("movimentacoes").select("*") \
        .eq("id_time", id_time).order("data", desc=True).limit(100).execute().data

    total_entrada = 0
    total_saida = 0
    compras = []
    vendas = []

    if movimentacoes:
        for m in movimentacoes:
            data = parse(m["data"]).strftime("%d/%m %H:%M")
            jogador = m.get("jogador", "Desconhecido")
            valor = m.get("valor", 0)
            origem = m.get("origem", "")
            destino = m.get("destino", "")
            categoria = m.get("categoria", "")
            tipo = m.get("tipo", "")

            detalhe = ""
            if origem:
                detalhe = f"do **{origem}**"
            elif destino:
                detalhe = f"para **{destino}**"

            texto = f"🟢 **{jogador}** {detalhe} por **R$ {abs(valor):,.0f}** em {data}".replace(",", ".")
            if tipo.lower() == "compra":
                compras.append(texto)
                total_entrada += valor
            elif tipo.lower() == "venda":
                texto = texto.replace("🟢", "🔴")
                vendas.append(texto)
                total_saida += valor

        for linha in compras:
            st.markdown(linha)

        st.markdown("---")
        st.subheader("💸 Vendas (Saídas)")
        for linha in vendas:
            st.markdown(linha)
    else:
        st.info("Nenhuma movimentação registrada ainda.")

    # 📊 Resumo
    st.markdown("---")
    st.subheader("📊 Resumo Financeiro")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"💰 Entradas: R$ {total_entrada:,.0f}".replace(",", "."))
    with col2:
        st.error(f"💸 Saídas: R$ {total_saida:,.0f}".replace(",", "."))
    with col3:
        resultado = total_entrada - total_saida
        cor = "success" if resultado >= 0 else "error"
        texto = f"📈 Lucro: R$ {resultado:,.0f}" if resultado >= 0 else f"📉 Prejuízo: R$ {abs(resultado):,.0f}"
        getattr(st, cor)(texto.replace(",", "."))

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")



