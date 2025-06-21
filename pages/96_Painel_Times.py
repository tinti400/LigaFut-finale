# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🎯 Configuração da página
st.set_page_config(page_title="Painel de Times - LigaFut", layout="wide")
st.title("📋 Painel de Times")

# 🔍 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo").execute()
times = res_times.data

linhas = []

for time in times:
    id_time = time.get("id")
    nome = time.get("nome", "Desconhecido")
    saldo = time.get("saldo", 0)

    # Buscar jogadores no elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data) if elenco.data else 0

    # Formatar saldo
    saldo_fmt = f"R$ {saldo:,.0f}".replace(",", ".")

    linhas.append({
        "Time": nome,
        "Saldo": saldo_fmt,
        "Jogadores": qtd_jogadores
    })

# 🔠 Filtros
col1, col2 = st.columns([2, 1])
with col1:
    filtro_nome = st.text_input("🔍 Filtrar por nome do time:")
with col2:
    filtro_min_jogadores = st.number_input("🔢 Mínimo de jogadores", min_value=0, value=0, step=1)

# Aplicar filtros
if filtro_nome:
    linhas = [l for l in linhas if filtro_nome.lower() in l["Time"].lower()]
if filtro_min_jogadores > 0:
    linhas = [l for l in linhas if l["Jogadores"] >= filtro_min_jogadores]

# Ordenar
linhas = sorted(linhas, key=lambda x: x["Time"])

# 📥 Exportar CSV
df_csv = pd.DataFrame(linhas)
csv = df_csv.to_csv(index=False).encode("utf-8")
st.download_button("📥 Baixar tabela como CSV", data=csv, file_name="times_ligafut.csv", mime="text/csv")

# ✅ Exibir tabela final estilo exibição limpa
st.table(df_csv)



