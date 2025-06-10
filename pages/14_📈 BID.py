# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="BID da LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.markdown("<h1 style='text-align: center;'>📊 BID da LigaFut</h1><hr>", unsafe_allow_html=True)

# 🔍 Filtros
filtro_time = st.selectbox("Filtrar por time", ["Todos"] + [t["nome"] for t in supabase.table("times").select("nome").execute().data])
filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "mercado", "leilao", "proposta"])
filtro_categoria = st.selectbox("Filtrar por categoria", ["Todos", "compra", "venda"])

# 🔁 Página atual (futuramente para paginação)
pagina = st.number_input("Página", min_value=1, value=1)

# 📥 Buscar movimentações com tratamento
try:
    query = supabase.table("movimentacoes").select("*")

    if filtro_time != "Todos":
        times = supabase.table("times").select("id").eq("nome", filtro_time).execute().data
        if times:
            id_time = times[0]["id"]
            query = query.or_(f"id_time.eq.{id_time},origem.eq.{filtro_time},destino.eq.{filtro_time}")

    if filtro_tipo != "Todos":
        query = query.eq("tipo", filtro_tipo.lower())

    if filtro_categoria != "Todos":
        query = query.eq("categoria", filtro_categoria.lower())

    # Usa created_at se data não existe
    query = query.order("created_at", desc=True)

    res = query.execute()
    movimentacoes = res.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    movimentacoes = []

# 📋 Exibe movimentações
if not movimentacoes:
    st.info("Nenhuma movimentação encontrada.")
else:
    for mov in movimentacoes:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"📌 **{mov['tipo'].capitalize()}** | {mov['categoria'].capitalize()} de **{mov['jogador']}**")
            if mov.get("origem") or mov.get("destino"):
                origem = mov.get("origem", "—")
                destino = mov.get("destino", "—")
                st.markdown(f"➡️ {origem} → {destino}")
        with col2:
            valor = mov.get("valor", 0)
            st.markdown(f"💰 R$ {valor:,.0f}".replace(",", "."))
            data = mov.get("created_at", "—")
            if data and data != "—":
                try:
                    dt = datetime.fromisoformat(data.replace("Z", "+00:00"))
                    st.markdown(f"🕒 {dt.strftime('%d/%m %H:%M')}")
                except:
                    st.markdown("🕒 —")
        st.markdown("---")



