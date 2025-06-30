# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from utils import verificar_sessao

st.set_page_config(page_title="💰 Gastos com Salários", layout="wide")
st.title("💰 Gastos com Salários dos Times")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()

# 📥 Buscar movimentações de salários
res_mov = supabase.table("movimentacoes")\
    .select("*")\
    .ilike("descricao", "%Pagamento de salários%")\
    .execute()

movimentacoes = res_mov.data if res_mov.data else []

# 💼 Agrupar gastos por time
gastos_por_time = {}
for mov in movimentacoes:
    id_time = mov.get("id_time")
    valor = abs(mov.get("valor", 0))
    if id_time:
        gastos_por_time[id_time] = gastos_por_time.get(id_time, 0) + valor

# 📥 Buscar nomes e escudos dos times
res_times = supabase.table("times").select("id", "nome", "escudo_url").execute()
times_data = {t["id"]: {"nome": t["nome"], "escudo": t.get("escudo_url", "")} for t in res_times.data}

# 🧾 Montar DataFrame
dados = []
for id_time, valor in gastos_por_time.items():
    time_info = times_data.get(id_time, {"nome": "Desconhecido", "escudo": ""})
    nome = time_info["nome"]
    escudo = time_info["escudo"]
    dado_formatado = {
        "Time": f"<img src='{escudo}' width='20'> {nome}",
        "Gasto com Salários": f"R$ {valor:,.0f}".replace(",", ".")
    }
    dados.append(dado_formatado)

df = pd.DataFrame(dados)
df = df.sort_values(by="Gasto com Salários", ascending=False)

# 📊 Exibir tabela com HTML ativado
st.markdown("### 📊 Ranking de Gastos com Salários")
st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
