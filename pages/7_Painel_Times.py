# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel de Times - LigaFut", layout="wide")

st.markdown("<h1 style='text-align:center;'>📊 Painel Geral dos Times</h1><hr>", unsafe_allow_html=True)

# 🔍 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo, logo_url").execute()
times = res_times.data

linhas = []

# 📥 Para cada time, contar jogadores no elenco
for time in times:
    id_time = time["id"]
    nome = time.get("nome", "Desconhecido")
    saldo = time.get("saldo", 0)
    logo_url = time.get("logo_url", "")

    # Buscar elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data)

    # Verificar situação do elenco
    if qtd_jogadores < 18:
        cor = "#ffcccc"  # vermelho claro
    elif qtd_jogadores > 26:
        cor = "#fff5cc"  # amarelo claro
    else:
        cor = "#ffffff"  # branco (normal)

    # Montar HTML com estilo de linha
    linha = f"""
    <tr style="background-color:{cor};">
        <td style='padding:8px; display:flex; align-items:center; gap:10px;'>
            <img src='{logo_url}' width='30'> <b>{nome}</b>
        </td>
        <td style='padding:8px;'>R$ {saldo:,.0f}</td>
        <td style='padding:8px;'>{qtd_jogadores}</td>
    </tr>
    """
    linhas.append(linha)

# Montar HTML da tabela
tabela_html = f"""
<table style='width:100%; border-collapse:collapse; font-family:sans-serif;'>
    <thead>
        <tr style='background-color:#222; color:white;'>
            <th style='text-align:left; padding:8px;'>🛡️ Time</th>
            <th style='text-align:left; padding:8px;'>💰 Saldo</th>
            <th style='text-align:left; padding:8px;'>👥 Qtd. Jogadores</th>
        </tr>
    </thead>
    <tbody>
        {''.join(linhas)}
    </tbody>
</table>
"""

st.markdown(tabela_html, unsafe_allow_html=True)
