# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Histórico de Punições - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("📜 Histórico de Punições")

# Carregar punições
res = supabase.table("punicoes").select("*").order("data", desc=True).execute()
punicoes = res.data if res.data else []

# Organizar dados
dados_formatados = []
for p in punicoes:
    try:
        tipo = p.get("tipo") or ""
        tipo_formatado = tipo.capitalize() if isinstance(tipo, str) else "Desconhecido"

        valor = "-"
        if tipo == "financeira":
            valor = f"R$ {int(p.get('valor', 0)):,}".replace(",", ".")
        elif tipo == "pontuacao":
            valor = f"-{int(p.get('pontos', 0))} pts"

        dados_formatados.append({
            "🏷️ Time": p.get("nome_time", "Desconhecido"),
            "📅 Data": datetime.fromisoformat(p["data"]).strftime("%d/%m/%Y %H:%M") if p.get("data") else "",
            "🚫 Tipo": tipo_formatado,
            "✏️ Motivo": p.get("motivo", "-"),
            "🧮 Valor/Pontos": valor
        })
    except Exception as e:
        st.error(f"Erro ao processar punição: {e}")

df = pd.DataFrame(dados_formatados)

# 📋 Exibir em tabela
if not df.empty:
    st.dataframe(df)
else:
    st.warning("Nenhuma punição registrada até o momento.")

