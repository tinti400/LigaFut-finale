# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from utils import verificar_sessao

st.set_page_config(page_title="💰 Gastos com Salários", layout="wide")
st.title("💰 Gastos com Salários dos Times")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_sessao()

# 📥 Carrega movimentações de pagamento de salários
res_mov = supabase.table("movimentacoes") \
    .select("id_time, valor") \
    .ilike("descricao", "%salário%") \
    .execute()

dados_mov = res_mov.data
if not dados_mov:
    st.info("Nenhum pagamento de salário registrado ainda.")
    st.stop()

# 💰 Soma os gastos por time
gastos_por_time = {}
for mov in dados_mov:
    id_time = mov["id_time"]
    valor = abs(float(mov["valor"]))  # transforma em valor positivo
    gastos_por_time[id_time] = gastos_por_time.get(id_time, 0) + valor

# 📥 Busca nomes e logos dos times
res_times = supabase.table("times").select("id", "nome", "logo").execute()
times_dict = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res_times.data}

# 🧾 Monta DataFrame para exibição
df_gastos = pd.DataFrame([
    {
        "Time": times_dict.get(tid, {}).get("nome", "Desconhecido"),
        "Gasto Total (R$)": gastos_por_time[tid],
        "Escudo": times_dict.get(tid, {}).get("logo", "")
    }
    for tid in gastos_por_time
])

df_gastos = df_gastos.sort_values(by="Gasto Total (R$)", ascending=False)

# 🖼️ Exibir escudos junto ao nome
def formatar_linha(row):
    return f'<img src="{row["Escudo"]}" width="25"> {row["Time"]}'

df_gastos["Time"] = df_gastos.apply(formatar_linha, axis=1)
df_gastos["Gasto Total (R$)"] = df_gastos["Gasto Total (R$)"].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))

# 📊 Exibir como tabela formatada
st.markdown("### 📋 Tabela de Gastos com Salários")
st.markdown(df_gastos[["Time", "Gasto Total (R$)"]].to_html(escape=False, index=False), unsafe_allow_html=True)
