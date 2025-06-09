# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🎯 Configuração
st.set_page_config(page_title="Painel de Times - LigaFut", layout="wide")
st.title("📋 Painel de Times")

# 🔍 Buscar dados
res = supabase.table("times").select("id, nome, saldo").execute()
times = res.data

linhas = []

for time in times:
    id_time = time.get("id")
    nome = time.get("nome", "Desconhecido")
    saldo = time.get("saldo", 0)

    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd = len(elenco.data) if elenco.data else 0

    # Formatar saldo
    saldo_fmt = f"R$ {saldo:,.0f}".replace(",", ".")

    # Definir cor de fundo
    if qtd < 18:
        cor = "#ffcccc"  # vermelho claro
    elif qtd > 26:
        cor = "#fff5cc"  # amarelo claro
    else:
        cor = "#ffffff"  # normal

    linhas.append({
        "Time": nome,
        "Saldo": saldo_fmt,
        "Jogadores": qtd,
        "Cor": cor
    })

# 🔠 Filtro por nome
filtro = st.text_input("🔍 Filtrar por nome do time:")
if filtro:
    linhas = [linha for linha in linhas if filtro.lower() in linha["Time"].lower()]

# 🔁 Ordenar por nome
linhas = sorted(linhas, key=lambda x: x["Time"])

# 📥 Botão de download CSV
df_csv = pd.DataFrame([{"Time": l["Time"], "Saldo": l["Saldo"], "Jogadores": l["Jogadores"]} for l in linhas])
csv = df_csv.to_csv(index=False).encode("utf-8")
st.download_button("📥 Baixar tabela como CSV", data=csv, file_name="times_ligafut.csv", mime="text/csv")

# 📊 Gerar HTML manual da tabela com destaque
html = """
<table style='width:100%; border-collapse:collapse; font-family:sans-serif; font-size:16px;'>
    <thead>
        <tr style='background-color:#111; color:white;'>
            <th style='text-align:left; padding:10px;'>🛡️ Time</th>
            <th style='text-align:left; padding:10px;'>💰 Saldo</th>
            <th style='text-align:left; padding:10px;'>👥 Jogadores</th>
        </tr>
    </thead>
    <tbody>
"""

for linha in linhas:
    html += f"""
    <tr style='background-color:{linha["Cor"]};'>
        <td style='padding:10px;'><b>{linha["Time"]}</b></td>
        <td style='padding:10px;'>{linha["Saldo"]}</td>
        <td style='padding:10px;'>{linha["Jogadores"]}</td>
    </tr>
    """

html += "</tbody></table>"

# 🖼️ Exibir tabela estilizada
st.markdown(html, unsafe_allow_html=True)



