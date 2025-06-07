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
st.subheader("📥 Entradas no Caixa (Vendas)")

try:
    movimentacoes = supabase.table("movimentacoes").select("*") \
        .eq("id_time", id_time).order("data", desc=True).limit(100).execute().data

    entradas = []
    saidas = []
    total_entrada = 0
    total_saida = 0

    for m in movimentacoes:
        categoria = m.get("categoria", "")
        data = parse(m["data"]).strftime("%d/%m %H:%M")
        jogador = m.get("jogador", "Desconhecido")
        valor = m.get("valor", 0)
        origem = m.get("origem", "")
        destino = m.get("destino", "")

        # Entradas
        if categoria.lower() == "venda":
            total_entrada += valor
            if destino.lower() == "mercado":
                entradas.append(f"🟢 **{jogador}** vendido no **Mercado** por **R$ {valor:,.0f}** em {data}")
            elif destino.lower() == "leilao":
                entradas.append(f"🟢 **{jogador}** vendido via **Leilão** por **R$ {valor:,.0f}** em {data}")
            elif destino:
                entradas.append(f"🟢 **{jogador}** vendido para **{destino}** por **R$ {valor:,.0f}** em {data}")
            else:
                entradas.append(f"🟢 **{jogador}** vendido por **R$ {valor:,.0f}** em {data}")

        # Saídas
        elif categoria.lower() == "compra":
            total_saida += valor
            if origem.lower() == "mercado":
                saidas.append(f"🔴 **{jogador}** comprado no **Mercado** por **R$ {valor:,.0f}** em {data}")
            elif origem.lower() == "leilao":
                saidas.append(f"🔴 **{jogador}** comprado via **Leilão** por **R$ {valor:,.0f}** em {data}")
            elif origem:
                saidas.append(f"🔴 **{jogador}** comprado do **{origem}** por **R$ {valor:,.0f}** em {data}")
            else:
                saidas.append(f"🔴 **{jogador}** comprado por **R$ {valor:,.0f}** em {data}")

    # Mostrar entradas
    if entradas:
        for entrada in entradas:
            st.markdown(entrada.replace(",", "."))
    else:
        st.info("Nenhuma entrada registrada ainda.")

    st.markdown("---")
    st.subheader("📤 Saídas do Caixa (Compras)")

    # Mostrar saídas
    if saidas:
        for saida in saidas:
            st.markdown(saida.replace(",", "."))
    else:
        st.info("Nenhuma saída registrada ainda.")

    # Resumo financeiro
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
