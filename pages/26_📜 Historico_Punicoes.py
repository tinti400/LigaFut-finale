import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="📜 Histórico de Punições", layout="wide")
st.title("📜 Histórico de Punições Aplicadas")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔍 Carregar punições
res = supabase.table("punicoes").select("*").order("data", desc=True).execute()
punicoes = res.data or []

# 🔄 Processar dados
tabela = []
for p in punicoes:
    try:
        tipo = p.get("tipo", "")
        motivo = p.get("motivo", "-")
        data = p.get("data", "")[:10]
        valor = p.get("valor")
        pontos = p.get("pontos")
        time_id = p.get("id_time")

        # Buscar nome do time
        res_time = supabase.table("times").select("nome").eq("id", time_id).limit(1).execute()
        nome_time = res_time.data[0]["nome"] if res_time.data else "Desconhecido"

        penalidade = f"-R$ {int(valor):,}".replace(",", ".") if tipo == "financeira" else f"-{int(pontos)} pts"

        tabela.append({
            "Time": nome_time,
            "Data": data,
            "Motivo": motivo,
            "Tipo": tipo.capitalize(),
            "Penalidade": penalidade
        })
    except Exception as e:
        st.error(f"Erro ao processar punição: {e}")

# 📊 Mostrar tabela
if tabela:
    df = pd.DataFrame(tabela)
    st.dataframe(df)
else:
    st.info("Nenhuma punição registrada até o momento.")

