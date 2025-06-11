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

st.markdown("<h1 style='text-align:center; color:#C0392B;'>📜 Histórico de Punições</h1>", unsafe_allow_html=True)
st.markdown("---")

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
            valor = f"<span style='color:#E74C3C;'>- R$ {int(p.get('valor', 0)):,}</span>".replace(",", ".")
        elif tipo == "pontuacao":
            valor = f"<span style='color:#F39C12;'>- {int(p.get('pontos', 0))} pts</span>"

        dados_formatados.append({
            "🏷️ Time": p.get("nome_time", "Desconhecido"),
            "📅 Data": datetime.fromisoformat(p["data"]).strftime("%d/%m/%Y %H:%M") if p.get("data") else "",
            "🚫 Tipo": tipo_formatado,
            "✏️ Motivo": p.get("motivo", "-"),
            "💥 Penalidade": valor
        })
    except Exception as e:
        st.error(f"Erro ao processar punição: {e}")

# Exibir
if dados_formatados:
    df = pd.DataFrame(dados_formatados)

    # Estilização visual
    st.markdown("""
        <style>
            .stDataFrame tbody td {
                text-align: center;
                font-size: 16px;
            }
            .stDataFrame thead th {
                background-color: #F5B7B1;
                color: black;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

    st.write("🔽 Punições aplicadas recentemente:")
    st.dataframe(df.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.info("✅ Nenhuma punição registrada até o momento.")



