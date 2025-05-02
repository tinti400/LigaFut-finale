import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 🔐 Conexão com Supabase
url = "https://hceqyuvryhtihhbvacyo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZXF5dXZyeWh0aWhoYnZhY3lvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTQ0NDgwNCwiZXhwIjoyMDYxMDIwODA0fQ.zzQs8YobpxZeFdWJhSyh34I_tzW_tUciEAsTat8setg"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Painel de Times", layout="wide")
st.title("📋 Painel de Times - LigaFut")

# 🔄 Buscar times
try:
    data = supabase.table("Times").select("*").execute()
    times = data.data

    if times:
        df = pd.DataFrame(times)
        df = df[["nome", "tecnico", "saldo"]]
        df["saldo"] = df["saldo"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum time cadastrado ainda.")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
