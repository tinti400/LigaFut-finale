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

nomes = []
saldos = []
qtds = []

for time in times:
    id_time = time.get("id")
    nome = str(time.get("nome") or "Sem nome")
    saldo = int(time.get("saldo") or 0)

    # Buscar jogadores do elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data) if elenco.data else 0

    nomes.append(nome)
    saldos.append(saldo)
    qtds.append(qtd_jogadores)

try:
    # Criar DataFrame
    df = pd.DataFrame({
        "Time": nomes,
        "Saldo": saldos,
        "Jogadores": qtds
    })

    # 💰 Formatando o saldo como R$
    df["Saldo"] = df["Saldo"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))

    # 🔠 Filtro por nome do time
    filtro = st.text_input("🔍 Filtrar por nome do time:")
    if filtro:
        df = df[df["Time"].str.contains(filtro, case=False)]

    # 🔢 Ordenar por nome
    df = df.sort_values("Time")

    # 📥 Botão para download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar tabela como CSV", data=csv, file_name="times_ligafut.csv", mime="text/csv")

    # ✅ Exibição final em modo visual
    st.table(df)

except Exception as e:
    st.error(f"Erro ao montar a tabela: {e}")


