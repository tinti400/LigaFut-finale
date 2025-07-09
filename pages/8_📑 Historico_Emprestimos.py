# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime

st.set_page_config(page_title="📑 Empréstimos - LigaFut", layout="centered")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📑 Histórico de Empréstimos")
st.markdown(f"🔎 Clube: **{nome_time}**")

# 🔍 Busca todos os empréstimos do time
res = supabase.table("emprestimos").select("*").eq("id_time", id_time).order("data_inicio", desc=True).execute()
emprestimos = res.data

if not emprestimos:
    st.info("📭 Nenhum empréstimo foi encontrado para seu clube.")
else:
    for emp in emprestimos:
        st.divider()
        status = "🟢 Ativo" if emp["status"] == "ativo" else "✅ Quitado"
        data_formatada = datetime.fromisoformat(emp["data_inicio"]).strftime('%d/%m/%Y %H:%M')

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"💵 **Valor Total:** R$ {emp['valor_total']:,}")
            st.write(f"📆 **Parcelas Totais:** {emp['parcelas_totais']}")
            st.write(f"🔁 **Parcelas Restantes:** {emp['parcelas_restantes']}")
        with col2:
            st.write(f"📊 **Valor por Parcela:** R$ {emp['valor_parcela']:,}")
            st.write(f"📈 **Juros:** {int(emp['juros'] * 100)}%")
            st.write(f"📅 **Data de Início:** {data_formatada}")

        st.success(f"**Status:** {status}" if emp["status"] == "ativo" else f"**Status:** ✅ Quitado")

st.divider()
st.markdown("🔙 Volte ao menu lateral para acessar outras áreas da LigaFut.")
