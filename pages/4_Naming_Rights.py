# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao
import uuid

st.set_page_config(page_title="📢 Naming Rights - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()

if "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🏟️ Busca o nível atual do estádio
res_estadio = supabase.table("estadios").select("nivel").eq("id_time", id_time).execute()
nivel = res_estadio.data[0]["nivel"] if res_estadio.data else 1

# 💵 Calcula o valor da evolução para o próximo nível
custo_base = 250_000_000 + nivel * 120_000_000

# 🧠 Verifica se já existe naming ativo
res_naming = supabase.table("naming_rights").select("*").eq("id_time", id_time).eq("ativo", True).execute()
ja_tem_naming = len(res_naming.data) > 0

if ja_tem_naming:
    st.success("✅ Seu time já possui um contrato de naming rights ativo.")
    st.stop()

st.title("📢 Ofertas de Naming Rights")
st.markdown(f"💡 Todas as propostas têm valor de **R${custo_base:,.0f}**, suficiente para cobrir a evolução do estádio para o nível {nivel + 1}.")

# 📋 Lista de propostas
propostas = [
    {"nome": "NeoBank", "beneficio_extra": "estacionamento"},
    {"nome": "TechMaster", "beneficio_extra": "area_vip"},
    {"nome": "PowerCell", "beneficio_extra": "desconto_ingressos"},
    {"nome": "VittaCard", "beneficio_extra": "loja_exclusiva"},
]

# 💰 Saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

for proposta in propostas:
    st.markdown("---")
    col1, col2 = st.columns([6, 2])
    col1.markdown(f"### 🏷️ {proposta['nome']}")
    col1.markdown(f"- 💰 Valor: **R${custo_base:,.0f}**")
    col1.markdown(f"- 🎁 Benefício Extra: **{proposta['beneficio_extra'].replace('_', ' ').capitalize()}**")

    if col2.button(f"💼 Aceitar {proposta['nome']}", key=proposta["nome"]):
        if saldo < custo_base:
            st.error("❌ Saldo insuficiente para aceitar esta proposta.")
        else:
            # Insere contrato
            novo_naming = {
                "id": str(uuid.uuid4()),
                "id_time": id_time,
                "empresa": proposta["nome"],
                "valor": custo_base,
                "beneficio_extra": proposta["beneficio_extra"],
                "ativo": True,
                "percentual_evolucao": 100,
                "evolucao_utilizada": False
            }
            supabase.table("naming_rights").insert(novo_naming).execute()

            # Atualiza saldo e registra movimentação
            novo_saldo = saldo + custo_base
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            registrar_movimentacao(id_time, "entrada", custo_base, f"Contrato naming rights com {proposta['nome']}", categoria="naming")

            st.success("✅ Proposta aceita com sucesso!")
            st.rerun()
