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
    id_time = time["id"]
    nome = time.get("nome", "Desconhecido")
    saldo = time.get("saldo", 0)

    # Buscar elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data)

    dados.append({
        "Nome do Time": nome,
        "Saldo": saldo,
        "Qtd. Jogadores": qtd_jogadores
    })

# Criar DataFrame estilo Excel
df = pd.DataFrame(dados)

# Exibir em formato planilha simples
st.dataframe(df.sort_values("Nome do Time"), use_container_width=True)


