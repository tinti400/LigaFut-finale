# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel de Times - LigaFut", layout="wide")
st.title("📋 Painel de Times")

# 🔍 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo").execute()
times = res_times.data

# ✅ Garante que vamos montar apenas listas simples
nomes = []
saldos = []
qtds = []

for time in times:
    id_time = time.get("id")
    nome = str(time.get("nome") or "Sem nome")
    saldo = int(time.get("saldo") or 0)

    # Buscar jogadores no elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data) if elenco.data else 0

    nomes.append(nome)
    saldos.append(saldo)
    qtds.append(qtd_jogadores)

# Criar DataFrame a partir de listas simples
df = pd.DataFrame({
    "Time": nomes,
    "Saldo": saldos,
    "Jogadores": qtds
})

# Ordenar e exibir
df = df.sort_values("Time")
st.dataframe(df, use_container_width=True)



