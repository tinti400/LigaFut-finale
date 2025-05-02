import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="💰 Finanças", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔐 Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("💰 Finanças do Clube")
st.markdown(f"### 📊 Time: **{nome_time}**")

# 📥 Carrega movimentações do time
try:
    movimentacoes_ref = supabase.table("times").select("*").eq("id", id_time).execute()
    movimentacoes = movimentacoes_ref.data[0].get("movimentacoes", [])
except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")
    st.stop()

# ✅ Preenche jogador com "N/A" se não existir
for mov in movimentacoes:
    if "jogador" not in mov:
        mov["jogador"] = "N/A"

# 📊 Monta DataFrame
df = pd.DataFrame(movimentacoes)

if not df.empty and all(col in df.columns for col in ["tipo", "jogador", "valor"]):
    # Garante que valor seja numérico
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["valor_formatado"] = df["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".") if pd.notnull(x) else "N/A")

    # Trata a data corretamente
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Reorganiza e renomeia colunas
    colunas = ["data", "tipo", "jogador", "valor_formatado"]
    if "descricao" in df.columns:
        colunas.append("descricao")
    df = df[colunas]
    df = df.rename(columns={
        "data": "Data",
        "tipo": "Tipo",
        "jogador": "Jogador",
        "valor_formatado": "Valor",
        "descricao": "Descrição"
    })

    st.dataframe(df, use_container_width=True)
else:
    st.info("⚠️ Nenhuma movimentação financeira registrada ou dados incompletos.")
