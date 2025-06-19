# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Resultado dos Amistosos", layout="wide")
st.title("🎯 Inserir Resultados dos Amistosos")

# ✅ Verifica se é admin
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email = st.session_state["usuario"]
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email).execute()
if not res_admin.data or not res_admin.data[0].get("administrador", False):
    st.error("Apenas administradores podem acessar esta página.")
    st.stop()

# 🔄 Buscar times
res_times = supabase.table("times").select("id, nome, saldo").execute()
todos_times = res_times.data or []
mapa_times = {t["id"]: t for t in todos_times}

# 🔄 Buscar amistosos aceitos e pendentes de resultado
res_amistosos = supabase.table("amistosos").select("*").eq("status", "aceito").execute()
amistosos = res_amistosos.data or []

if not amistosos:
    st.info("Nenhum amistoso pendente de resultado.")
    st.stop()

for amistoso in amistosos:
    id = amistoso["id"]
    valor = amistoso["valor_aposta"]
    time_a_id = amistoso["time_convidante"]
    time_b_id = amistoso["time_convidado"]

    time_a = mapa_times.get(time_a_id, {"nome": "Desconhecido", "saldo": 0})
    time_b = mapa_times.get(time_b_id, {"nome": "Desconhecido", "saldo": 0})

    st.markdown(f"""
        ### ⚽️ {time_a['nome']} vs {time_b['nome']}  
        💰 Aposta total: R${valor * 2:.2f} milhões  
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(f"✅ {time_a['nome']} venceu", key=f"a_{id}"):
            # Transferência do valor total para o time A
            novo_saldo = time_a["saldo"] + valor * 2
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", time_a_id).execute()
            registrar_movimentacao(supabase, time_a_id, valor * 2, "Vitória amistoso")
            supabase.table("amistosos").update({"status": "concluido", "resultado": "vitoria_convidante"}).eq("id", id).execute()
            st.success(f"{time_a['nome']} venceu e recebeu R${valor * 2:.2f} milhões!")
            st.experimental_rerun()

    with col2:
        if st.button(f"✅ {time_b['nome']} venceu", key=f"b_{id}"):
            novo_saldo = time_b["saldo"] + valor * 2
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", time_b_id).execute()
            registrar_movimentacao(supabase, time_b_id, valor * 2, "Vitória amistoso")
            supabase.table("amistosos").update({"status": "concluido", "resultado": "vitoria_convidado"}).eq("id", id).execute()
            st.success(f"{time_b['nome']} venceu e recebeu R${valor * 2:.2f} milhões!")
            st.experimental_rerun()

    with col3:
        if st.button("🤝 Empate", key=f"empate_{id}"):
            novo_saldo_a = time_a["saldo"] + valor
            novo_saldo_b = time_b["saldo"] + valor
            supabase.table("times").update({"saldo": novo_saldo_a}).eq("id", time_a_id).execute()
            supabase.table("times").update({"saldo": novo_saldo_b}).eq("id", time_b_id).execute()
            registrar_movimentacao(supabase, time_a_id, valor, "Empate amistoso")
            registrar_movimentacao(supabase, time_b_id, valor, "Empate amistoso")
            supabase.table("amistosos").update({"status": "concluido", "resultado": "empate"}).eq("id", id).execute()
            st.info("Empate! Cada time recebeu de volta sua aposta.")
            st.experimental_rerun()
