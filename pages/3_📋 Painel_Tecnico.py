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
st.subheader("📊 Histórico de Movimentações")

# 🔍 Buscar todas as movimentações do time
try:
    movimentacoes = supabase.table("movimentacoes").select("*") \
        .eq("id_time", id_time).order("data", desc=True).limit(30).execute().data

    if movimentacoes:
        for m in movimentacoes:
            data = parse(m["data"]).strftime("%d/%m %H:%M")
            categoria = m.get("categoria", "Movimentação")
            jogador = m.get("jogador", "Desconhecido")
            valor = m.get("valor", 0)

            if categoria == "Compra":
                origem = m.get("origem", "Mercado")
                st.markdown(f"✅ **{jogador}** comprado por **R$ {valor:,.0f}** em {data} (_{origem}_)".replace(",", "."))

            elif categoria == "Venda":
                destino = m.get("destino", "Mercado")
                st.markdown(f"📤 **{jogador}** vendido por **R$ {valor:,.0f}** em {data} (_{destino}_)".replace(",", "."))

            else:
                st.markdown(f"🔁 **{jogador}** - {categoria} - **R$ {valor:,.0f}** em {data}".replace(",", "."))
    else:
        st.info("Nenhuma movimentação registrada ainda.")
except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")
