# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="📄 Relatório - Evento de Roubo", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("📄 Relatório do Evento de Roubo")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📦 Buscar movimentações com categoria "roubo"
try:
    res = supabase.table("movimentacoes").select("*").eq("categoria", "roubo").order("data", desc=True).execute()
    dados = res.data
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    dados = []

if dados:
    df = pd.DataFrame(dados)

    # 🔁 Converte e organiza colunas
    df["data"] = pd.to_datetime(df["data"])
    df["valor"] = df["valor"].astype(float)
    df["valor_formatado"] = df["valor"].map(lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    colunas = ["data", "descricao", "valor_formatado", "origem", "destino"]
    df_exibicao = df[colunas].rename(columns={
        "data": "Data",
        "descricao": "Descrição",
        "valor_formatado": "Valor",
        "origem": "Time que Roubou",
        "destino": "Time Roubado"
    })

    # 📊 Exibe tabela
    st.markdown("### 📊 Transferências realizadas por roubo")
    st.dataframe(df_exibicao, use_container_width=True)

    # 📥 Download Excel
    excel = df_exibicao.to_excel(index=False, engine="openpyxl")
    st.download_button("📥 Baixar Excel", data=excel, file_name="relatorio_roubo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("Nenhum registro de roubo encontrado no BID.")
