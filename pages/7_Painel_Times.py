# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel de Times - LigaFut", layout="wide")

# 🎯 Título centralizado
st.markdown("<h1 style='text-align:center;'>📊 Painel Geral dos Times</h1><hr>", unsafe_allow_html=True)

# 🚫 Evita HTML exibido como texto
st.markdown("""
    <style>
    pre, code, .element-container:has(.stMarkdown) + .element-container pre {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🔍 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo").execute()
times = res_times.data

linhas_html = []

# 🔄 Loop por time
for time in times:
    id_time = time["id"]
    nome = time.get("nome", "Desconhecido")
    saldo = time.get("saldo", 0)

    # 📥 Buscar elenco
    elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
    qtd_jogadores = len(elenco.data)

    # 🎨 Destaques visuais
    if qtd_jogadores < 18:
        cor = "#ffcccc"
    elif qtd_jogadores > 26:
        cor = "#fff5cc"
    else:
        cor = "#ffffff"

    # 🔠 Linha HTML
    linha = f"""
    <tr style="background-color:{cor};">
        <td style='padding:8px;'><b>{nome}</b></td>
        <td style='padding:8px;'>R$ {saldo:,.0f}</td>
        <td style='padding:8px;'>{qtd_jogadores}</td>
    </tr>
    """
    linhas_html.append(linha)

# 🧱 Tabela formatada
tabela_html = f"""
<table style='width:100%; border-collapse:collapse; font-family:sans-serif;'>
    <thead>
        <tr style='background-color:#111; color:white;'>
            <th style='text-align:left; padding:8px;'>🛡️ Time</th>
            <th style='text-align:left; padding:8px;'>💰 Saldo</th>
            <th style='text-align:left; padding:8px;'>👥 Qtd. Jogadores</th>
        </tr>
    </thead>
    <tbody>
        {''.join(linhas_html)}
    </tbody>
</table>
"""

# ✅ Exibir tabela bonitinha
st.markdown(tabela_html, unsafe_allow_html=True)

