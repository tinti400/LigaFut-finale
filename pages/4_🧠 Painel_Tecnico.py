# painel_movimentacoes_time.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📊 Painel do Time", layout="wide")
st.title("📊 Painel do Time - LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "")

# 🎯 Buscar saldo e escudo do time
try:
    time_res = supabase.table("times").select("saldo, logo").eq("id", id_time).single().execute()
    saldo = time_res.data.get("saldo", 0)
    logo = time_res.data.get("logo", None)
except:
    saldo = 0
    logo = None

# 🎨 Cabeçalho do time
col_logo, col_info = st.columns([1, 6])
with col_logo:
    if logo:
        st.image(logo, width=90)
with col_info:
    st.markdown(f"## 🛡️ {nome_time}")
    st.markdown(f"💰 **Saldo atual:** R$ {saldo:,.0f}".replace(",", "."))

st.markdown("---")

# 🔍 Buscar movimentações
try:
    mov = supabase.table("movimentacoes_financeiras")\
        .select("*")\
        .eq("id_time", id_time)\
        .order("data", desc=True)\
        .limit(50)\
        .execute().data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    st.stop()

# 🧠 Separar compras e vendas por palavras-chave
compras = [m for m in mov if "compra" in m["descricao"].lower() or "contratação" in m["descricao"].lower()]
vendas = [m for m in mov if "venda" in m["descricao"].lower()]

# 📋 Exibir os dois painéis
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 Últimas Compras")
    if not compras:
        st.info("Nenhuma compra registrada.")
    else:
        for c in compras[:10]:
            data = datetime.fromisoformat(c["data"]).strftime("%d/%m/%Y %H:%M")
            jogador = c["descricao"].replace("Compra de ", "").replace("Contratação de ", "")
            st.markdown(f"""
            <div style='padding:8px 12px; border-radius:10px; background-color:#e6f7e6; margin-bottom:6px'>
                <b>🧑 {jogador}</b><br>
                💸 <b>R$ {abs(c['valor']):,.0f}</b><br>
                🕓 <small>{data}</small>
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.subheader("🔴 Últimas Vendas")
    if not vendas:
        st.info("Nenhuma venda registrada.")
    else:
        for v in vendas[:10]:
            data = datetime.fromisoformat(v["data"]).strftime("%d/%m/%Y %H:%M")
            jogador = v["descricao"].replace("Venda de ", "")
            st.markdown(f"""
            <div style='padding:8px 12px; border-radius:10px; background-color:#ffecec; margin-bottom:6px'>
                <b>🧑 {jogador}</b><br>
                💰 <b>R$ {v['valor']:,.0f}</b><br>
                🕓 <small>{data}</small>
            </div>
            """, unsafe_allow_html=True)
