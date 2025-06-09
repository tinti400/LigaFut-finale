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

if times:
    for time in times:
        id_time = time.get("id")
        nome = time.get("nome") or "Sem nome"
        saldo = time.get("saldo") or 0

        # Buscar jogadores no elenco
        elenco_res = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
        qtd_jogadores = len(elenco_res.data) if elenco_res.data else 0

        dados.append({
            "Time": nome,
            "Saldo": saldo,
            "Jogadores": qtd_jogadores
        })

    # Criar DataFrame
    df = pd.DataFrame(dados)

    # Exibir somente se tiver dados
    if not df.empty:
        df = df.sort_values("Time")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para exibir.")
else:
    st.warning("Nenhum time encontrado no banco de dados.")



