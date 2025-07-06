# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📋 Relatório - Evento de Roubo", layout="wide")
st.title("📋 Relatório Final - Evento de Roubo")

# ✅ Verifica login
if "usuario_id" not in st.session_state or "nome_time" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🔄 Busca as transferências realizadas no evento
try:
    resposta = supabase.table("bids").select("*").eq("tipo", "roubo").order("data", desc=True).execute()
    dados = resposta.data
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    st.stop()

if not dados:
    st.info("Nenhuma movimentação registrada no Evento de Roubo.")
    st.stop()

# 📊 Monta o DataFrame para exibição
df = pd.DataFrame([{
    "Jogador": d["nome_jogador"],
    "Posição": d.get("posicao", ""),
    "Overall": d.get("overall", ""),
    "Valor Pago (50%)": f'R${d["valor"]:,.2f}',
    "Time que Roubou": d["time_destino"],
    "Time que Perdeu": d["time_origem"],
    "Data/Hora": pd.to_datetime(d["data"]).strftime("%d/%m %H:%M")
} for d in dados])

# 📁 Exibição bonita
st.markdown("### 🔄 Jogadores Roubados")
st.dataframe(df, use_container_width=True)

# 📥 Botão para baixar em Excel
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar Relatório em CSV",
    data=csv,
    file_name="relatorio_evento_roubo.csv",
    mime="text/csv"
)
