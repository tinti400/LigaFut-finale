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
    tipo = str(p.get("tipo", "")).lower()
    valor_ou_pontos = "-"
    if tipo == "financeira":
        valor_ou_pontos = f"-{int(p.get('valor', 0))}"
    elif tipo == "pontuacao":
        valor_ou_pontos = f"-{int(p.get('pontos', 0))}"

    linhas.append({
        "📅 Data": datetime.fromisoformat(p.get("data", datetime.now().isoformat())).strftime("%d/%m/%Y %H:%M"),
        "🏷️ Time": p.get("nome_time", "Desconhecido"),
        "🚫 Tipo": tipo.capitalize(),
        "💬 Motivo": p.get("motivo", "-"),
        "🧮 Valor/Pontos": valor_ou_pontos
    })

df = pd.DataFrame(linhas)

# 📋 Exibir em tabela
st.dataframe(df, use_container_width=True)

