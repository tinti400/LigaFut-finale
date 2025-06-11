# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Histórico de Punições - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("📜 Histórico de Punições")

# 📥 Buscar punições registradas
res = supabase.table("punicoes").select("*").order("data", desc=True).execute()
punicoes = res.data

if not punicoes:
    st.info("✅ Nenhuma punição registrada até o momento.")
    st.stop()

# 🔄 Carregar nomes dos times para exibir no lugar dos IDs
res_times = supabase.table("times").select("id", "nome").execute()
dict_times = {t["id"]: t["nome"] for t in res_times.data}

# 🧾 Montar DataFrame com dados organizados
dados = []
for p in punicoes:
    dados.append({
        "🧿 Time": dict_times.get(p["id_time"], "Desconhecido"),
        "🚫 Tipo": p.get("tipo", "").capitalize(),
        "📋 Motivo": p.get("motivo", "Não informado"),
        "📅 Data": datetime.fromisoformat(p["data"]).strftime("%d/%m/%Y %H:%M"),
        "⏳ Duração (dias)": p.get("duracao", "Indefinida")
    })

df = pd.DataFrame(dados)

# 📊 Exibir em formato de tabela
st.dataframe(df, use_container_width=True)
