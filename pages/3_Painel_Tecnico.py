# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import formatar_valor, verificar_login

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Painel do Técnico", page_icon="📊", layout="wide")
verificar_login()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown("## 📊 Painel do Técnico")
st.markdown(f"### 🏷️ Time: `{nome_time}`")

# 💰 Saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo_time = res_saldo.data[0]["saldo"] if res_saldo.data else 0
st.markdown(f"💰 **Saldo:** `{formatar_valor(saldo_time)}`")

# 🧾 Buscar movimentações relacionadas ao time
res_movs = supabase.table("movimentacoes").select("*").order("data", desc=True).execute()
movimentacoes = res_movs.data if res_movs.data else []

# 🔍 Filtro por tipo
filtro = st.radio("Filtrar:", ["Entradas", "Saídas", "Resumo"], horizontal=True)
filtradas = []
nome_time_norm = nome_time.strip().lower()

for m in movimentacoes:
    origem_norm = (m.get("origem") or "").strip().lower()
    destino_norm = (m.get("destino") or "").strip().lower()
    
    if filtro == "Entradas" and destino_norm == nome_time_norm:
        filtradas.append(m)
    elif filtro == "Saídas" and origem_norm == nome_time_norm:
        filtradas.append(m)
    elif filtro == "Resumo" and (origem_norm == nome_time_norm or destino_norm == nome_time_norm):
        filtradas.append(m)

# 🎯 Exibir movimentações
if not filtradas:
    st.info("Nenhuma movimentação encontrada.")
else:
    for mov in filtradas:
        jogador = mov.get("jogador", "Desconhecido")
        tipo = mov.get("tipo", "N/A")
        categoria = mov.get("categoria", "N/A")
        valor = formatar_valor(mov.get("valor", 0))
        destino = mov.get("destino", "N/A")
        origem = mov.get("origem", "N/A")
        data = mov.get("data")
        tipo_icon = "🟢" if destino.lower() == nome_time_norm else "🔴"

        data_str = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S.%f").strftime("%d/%m/%Y %H:%M") if data else "N/A"
        clube_ref = destino if destino.lower() == nome_time_norm else origem

        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin:10px 0;">
            <h5>{tipo_icon} <strong>{jogador}</strong></h5>
            <p>📁 <strong>Tipo:</strong> {tipo} — {categoria}</p>
            <p>🏷️ <strong>Clube:</strong> {clube_ref}</p>
            <p>💸 <strong>Valor:</strong> {valor}</p>
            <p>📅 <strong>Data:</strong> {data_str}</p>
        </div>
        """, unsafe_allow_html=True)

