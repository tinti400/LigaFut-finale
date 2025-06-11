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

import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

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
        tipo = p.get("tipo", "").capitalize()
        motivo = p.get("motivo", "-")
        data = p.get("data", "")[:10]
        valor = p.get("valor") or 0
        pontos = p.get("pontos") or 0
        time_id = p.get("id_time")

        # Buscar nome do time
        res_time = supabase.table("times").select("nome").eq("id", time_id).limit(1).execute()
        nome_time = res_time.data[0]["nome"] if res_time.data else "Desconhecido"

        penalidade = f"R$ -{int(valor):,}".replace(",", ".") if tipo.lower() == "financeira" else f"-{pontos} pts"

        tabela.append({
            "🛡️ Time": nome_time,
            "📅 Data": data,
            "📌 Motivo": motivo,
            "🚫 Tipo": tipo,
            "💸 Penalidade": penalidade
        })
    except Exception as e:
        st.error(f"Erro ao processar punição: {e}")

# 💡 Mostrar tabela estilizada
if tabela:
    df = pd.DataFrame(tabela)
    st.markdown(
        f"""
        <div style='overflow-x: auto; border-radius: 10px; border: 1px solid #CCC; padding: 10px; background-color: #f9f9f9'>
            {df.to_html(index=False, escape=False)}
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("Nenhuma punição registrada até o momento.")
