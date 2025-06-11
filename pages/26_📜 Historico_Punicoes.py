# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📜 Histórico de Punições", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("📜 Histórico de Punições")

# 🚨 Carregar punições
res = supabase.table("punicoes").select("*").order("data", desc=True).execute()
punicoes = res.data

if not punicoes:
    st.warning("Nenhuma punição registrada.")
    st.stop()

# 📊 Formatando os dados
linhas = []
for p in punicoes:
    linhas.append({
        "📅 Data": datetime.fromisoformat(p["data"]).strftime("%d/%m/%Y %H:%M"),
        "🏷️ Time": p.get("nome_time", "Desconhecido"),
        "🚫 Tipo": str(p.get("tipo", "")).capitalize(),
        "💬 Motivo": p.get("motivo", "-"),
        "🧮 Valor/Pontos": f"-{int(p['valor']) if p['tipo'] == 'financeira' else int(p['pontos'])}"
    })

df = pd.DataFrame(linhas)

# 📋 Exibir em tabela
st.dataframe(df, use_container_width=True)
