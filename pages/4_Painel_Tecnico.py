import streamlit as st
import pandas as pd
from supabase import create_client
from utils import verificar_login, formatar_valor

st.set_page_config(page_title="📋 Últimas Movimentações", layout="wide")
verificar_login()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]

# 🔄 Buscar últimas 8 movimentações do time, ordenadas pela data mais recente
try:
    res = supabase.table("movimentacoes").select("*").eq("id_time", id_time).order("data", desc=True).limit(8).execute()
    movimentacoes = res.data if res.data else []
except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")
    movimentacoes = []

# Exibir visual igual ao painel de elenco
st.markdown("### 💼 Últimas Movimentações")
if movimentacoes:
    for mov in movimentacoes:
        tipo = "🟢 Entrada" if mov["categoria"] == "compra" else "🔴 Saída"
        col1, col2, col3, col4, col5 = st.columns([1.5, 2.5, 1.2, 2, 1.5])
        with col1:
            st.markdown(f"**{mov.get('posição', '—')}**")
        with col2:
            st.markdown(f"{mov['jogador']}")
        with col3:
            st.markdown(f"{mov.get('overall', '—')}")
        with col4:
            st.markdown(formatar_valor(mov["valor"]))
        with col5:
            st.markdown(tipo)
        st.markdown("---")
else:
    st.info("Nenhuma movimentação encontrada.")




