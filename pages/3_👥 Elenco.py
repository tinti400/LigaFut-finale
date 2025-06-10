# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🧾 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔒 Verifica se o mercado está aberto
status_res = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = status_res.data[0]["mercado_aberto"] if status_res.data else False

# 📋 Exibir elenco
st.title(f"📋 Elenco - {nome_time}")

res = supabase.table("elenco").select("*").eq("time_id", id_time).execute()
elenco = res.data

if not elenco:
    st.info("Nenhum jogador cadastrado no elenco.")
    st.stop()

for jogador in elenco:
    col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 2, 2, 2, 2])
    with col1:
        st.markdown(f"**{jogador['posição']}**")
    with col2:
        st.markdown(f"{jogador['nome']}")
    with col3:
        st.markdown(f"⭐ {jogador['overall']}")
    with col4:
        st.markdown(f"💰 R$ {jogador['valor']:,}".replace(",", "."))
    with col5:
        if mercado_aberto:
            if st.button("💸 Vender", key=jogador["id"]):
                # 1. Remover do elenco
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                # 2. Adicionar ao mercado com valor cheio
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posição": jogador["posição"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"]
                }).execute()

                # 3. Registrar movimentação (venda, valor total, crédito de 70% no utils)
                registrar_movimentacao(
                    id_time=id_time,
                    jogador=jogador["nome"],
                    tipo="mercado",
                    categoria="venda",
                    valor=jogador["valor"]
                )

                st.success(f"{jogador['nome']} foi vendido ao mercado!")
                st.rerun()
        else:
            with col5:
                st.markdown("🚫 Mercado Fechado")


