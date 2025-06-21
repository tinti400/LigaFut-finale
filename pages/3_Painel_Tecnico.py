# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Painel do Técnico", layout="wide")
st.markdown("<h1 style='text-align: center;'>📊 Painel do Técnico</h1>", unsafe_allow_html=True)

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "")

# 🎯 Filtro
opcao_filtro = st.radio("Filtrar:", ["Entradas", "Saídas", "Resumo"], horizontal=True)

# 🔄 Buscar movimentações
res_mov = supabase.table("movimentacoes").select("*").order("data", desc=True).execute()
movs = res_mov.data

# 🔍 Normalizar nomes
nome_time_norm = nome_time.strip().lower()

def formatar_valor(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")

def exibir_mov(m):
    jogador = m.get("jogador")
    valor = m.get("valor", 0)
    tipo = m.get("tipo", "-")
    categoria = m.get("categoria", "-")
    origem = m.get("origem", "-")
    destino = m.get("destino", "-")
    data = m.get("data", "")
    if data:
        data = datetime.fromisoformat(data).strftime("%d/%m/%Y %H:%M")

    html = f"""
    <div style='border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:10px'>
        <div><b>🧍 Jogador:</b> {jogador}</div>
        <div><b>🗓️ Data:</b> {data}</div>
        <div><b>📦 Tipo:</b> {tipo} — <b>📁 Categoria:</b> {categoria}</div>
        <div><b>🔄 Origem:</b> {origem} → <b>🏁 Destino:</b> {destino}</div>
        <div><b>💰 Valor:</b> <span style='color:green'>{formatar_valor(valor)}</span></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# 🔍 Filtrar por time
movs_filtradas = []
for m in movs:
    origem_norm = m.get("origem", "").strip().lower()
    destino_norm = m.get("destino", "").strip().lower()

    if origem_norm != nome_time_norm and destino_norm != nome_time_norm:
        continue

    if opcao_filtro == "Entradas" and destino_norm == nome_time_norm:
        movs_filtradas.append(m)
    elif opcao_filtro == "Saídas" and origem_norm == nome_time_norm:
        movs_filtradas.append(m)
    elif opcao_filtro == "Resumo":
        movs_filtradas.append(m)

# 💡 Exibir time e saldo
res_time = supabase.table("times").select("saldo").eq("id", id_time).single().execute()
saldo_time = res_time.data.get("saldo", 0)
st.markdown(f"""
<div style='padding:10px 0 20px 0;'>
    <h3>📍 <b>Time:</b> {nome_time} &nbsp;&nbsp;&nbsp; 💰 <b>Saldo:</b> R$ {saldo_time:,.3f}</h3>
</div>
""", unsafe_allow_html=True)

# 📋 Exibir resultados
if not movs_filtradas:
    st.info("Nenhuma movimentação encontrada.")
else:
    for mov in movs_filtradas:
        exibir_mov(mov)

