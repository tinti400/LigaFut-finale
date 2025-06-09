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

dados = []

for time in times:
    id_time = time.get("id")
    nome = time.get("nome") or "Sem nome"
    saldo = time.get("saldo") or 0

    # Buscar jogadores no elenco
    elenco_res = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco_res.data)

    dados.append({
        "Time": nome,
        "Saldo": saldo,
        "Jogadores": qtd_jogadores
    })

# Garantir que o DataFrame foi criado corretamente
df = pd.DataFrame(dados)

# Ordenar por nome do time, se a coluna existir
if "Time" in df.columns:
    df = df.sort_values("Time")

# Exibir tabela estilo Excel
st.dataframe(df, use_container_width=True)


