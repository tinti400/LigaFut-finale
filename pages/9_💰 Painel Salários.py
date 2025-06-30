# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from utils import verificar_sessao

st.set_page_config(page_title="💰 Painel Salários", layout="wide")
st.title("💰 Total de Salários Pagos")
st.markdown("Veja abaixo quanto cada time já pagou de salários na temporada.")
st.markdown("---")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()

# 🔍 Busca movimentações com descrição contendo qualquer variação de 'salario'
res_mov = supabase.table("movimentacoes").select("id_time, valor, descricao").execute()
movimentacoes = res_mov.data if res_mov.data else []

# 📦 Filtra apenas os registros de salários (por descrição)
salarios = [
    mov for mov in movimentacoes
    if any(p in mov.get("descricao", "").lower() for p in ["salario", "salários", "salário", "salarios"])
]

# 💰 Soma por time
df = pd.DataFrame(salarios)
if df.empty:
    st.info("Nenhum salário registrado até o momento.")
    st.stop()

df["valor"] = df["valor"].astype(float).abs()
df_grouped = df.groupby("id_time")["valor"].sum().reset_index()

# 📌 Puxa nomes e logos dos times
res_times = supabase.table("times").select("id, nome, logo").execute()
times_data = res_times.data if res_times.data else []

mapa_times = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in times_data}
df_grouped["nome_time"] = df_grouped["id_time"].map(lambda x: mapa_times.get(x, {}).get("nome", "Desconhecido"))
df_grouped["logo"] = df_grouped["id_time"].map(lambda x: mapa_times.get(x, {}).get("logo", ""))

# 💳 Formatação
df_grouped = df_grouped.sort_values("valor", ascending=False)
df_grouped["valor_formatado"] = df_grouped["valor"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))

# 🖼️ Exibe com logos
for _, row in df_grouped.iterrows():
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if row["logo"]:
            st.image(row["logo"], width=40)
    with col2:
        st.markdown(f"**{row['nome_time']}** — <span style='color:green'>{row['valor_formatado']}</span>", unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 Os salários são descontados automaticamente após cada jogo confirmado.")
