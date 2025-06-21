# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="💰 Painel de Salários", page_icon="💰", layout="centered")
st.markdown("## 💰 Total de Salários Pagos")
st.markdown("Veja abaixo quanto cada time já pagou de salários na temporada.")

# 🔄 Buscar movimentações de salários
try:
    res = supabase.table("movimentacoes").select("*").eq("descricao", "Pagamento de salários").execute()
    movimentacoes = res.data
    if not movimentacoes:
        st.info("Ainda não houve pagamento de salários registrado.")
        st.stop()

    # Organizar em DataFrame
    df = pd.DataFrame(movimentacoes)
    df["valor"] = df["valor"].astype(float)
    df["valor"] = df["valor"].abs()  # Mostrar valor positivo
    df_grouped = df.groupby("id_time")["valor"].sum().reset_index()
except Exception as e:
    st.error(f"Erro ao carregar dados de salários: {e}")
    st.stop()

# 🔎 Buscar nomes dos times
try:
    res_times = supabase.table("times").select("id", "nome", "logo").execute()
    times = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res_times.data}
except Exception as e:
    st.error(f"Erro ao buscar nomes dos times: {e}")
    st.stop()

# 📊 Montar exibição
dados = []
for _, row in df_grouped.iterrows():
    time_id = row["id_time"]
    if time_id in times:
        nome = times[time_id]["nome"]
        logo = times[time_id]["logo"]
        valor = row["valor"]
        dados.append((logo, nome, valor))

# 🔢 Ordenar e exibir
dados = sorted(dados, key=lambda x: x[2], reverse=True)
for logo, nome, valor in dados:
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(logo or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=40)
    with col2:
        st.markdown(f"**{nome}** — `R$ {valor:,.0f}`".replace(",", "."))

st.markdown("---")
st.caption("💡 Os salários são descontados automaticamente após cada jogo confirmado.")
