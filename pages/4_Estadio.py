# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="🏟️ Estádio - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()

if "nome_time" not in st.session_state:
    st.warning("Você precisa estar logado com um time válido para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

capacidade_por_nivel = {
    1: 25000,
    2: 47500,
    3: 67500,
    4: 87500,
    5: 110000
}

setores = {
    "geral": 0.40,
    "norte": 0.20,
    "sul": 0.20,
    "central": 0.15,
    "camarote": 0.05
}

precos_padrao = {
    "geral": 20.0,
    "norte": 40.0,
    "sul": 40.0,
    "central": 60.0,
    "camarote": 100.0
}

def calcular_publico_setor(lugares, preco):
    if preco <= 20:
        fator = 1.0
    elif preco <= 50:
        fator = 0.8
    elif preco <= 100:
        fator = 0.6
    elif preco <= 200:
        fator = 0.4
    elif preco <= 500:
        fator = 0.2
    else:
        fator = 0.01
    return int(min(lugares, lugares * fator))

# 🔎 Verifica se o estádio já existe
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

# 🏗️ Cria o estádio se não existir
if not estadio:
    estadio_novo = {
        "id_time": id_time,
        "nome": f"Estádio {nome_time}",
        "nivel": 1,
        "capacidade": capacidade_por_nivel[1],
        "em_melhorias": False,
        **{f"preco_{k}": v for k, v in precos_padrao.items()}
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo
    st.success("✅ Estádio criado com sucesso!")
    st.experimental_rerun()

# 🔄 Garante capacidade correta
nivel = estadio.get("nivel", 1)
capacidade = capacidade_por_nivel.get(nivel, 25000)
if estadio.get("capacidade", 0) != capacidade:
    supabase.table("estadios").update({"capacidade": capacidade}).eq("id_time", id_time).execute()

# 🖊️ Renomear estádio
st.markdown(f"## 🏟️ {estadio['nome']}")
novo_nome = st.text_input("✏️ Renomear Estádio", value=estadio["nome"])
if novo_nome and novo_nome != estadio["nome"]:
    supabase.table("estadios").update({"nome": novo_nome}).eq("id_time", id_time).execute()
    st.success("✅ Nome atualizado!")
    st.experimental_rerun()

st.markdown(f"- **Nível atual:** {nivel}")
st.markdown(f"- **Capacidade:** {capacidade:,} torcedores")

# 💸 Preços por setor e público estimado
st.markdown("### 🎛 Preços por Setor")
publico_total = 0
renda_total = 0

for setor, proporcao in setores.items():
    col1, col2, col3 = st.columns([3, 2, 2])
    lugares = int(capacidade * proporcao)
    preco_atual = float(estadio.get(f"preco_{setor}", precos_padrao[setor]))
    novo_preco = col1.number_input(f"Preço - {setor.upper()}", min_value=1.0, max_value=2000.0, value=preco_atual, step=1.0, key=f"preco_{setor}")
    
    if novo_preco != preco_atual:
        supabase.table("estadios").update({f"preco_{setor}": novo_preco}).eq("id_time", id_time).execute()
        st.experimental_rerun()
    
    publico = calcular_publico_setor(lugares, novo_preco)
    renda = publico * novo_preco
    col2.markdown(f"👥 Público estimado: **{publico:,}**")
    col3.markdown(f"💰 Renda estimada: **R${renda:,.2f}**")
    publico_total += publico
    renda_total += renda

st.markdown(f"### 📊 Público total estimado: **{publico_total:,}**")
st.markdown(f"### 💸 Renda total estimada: **R${renda_total:,.2f}**")

# ⬆️ Melhorar estádio
if nivel < 5:
    custo = 250_000_000 + (nivel * 120_000_000)
    st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
    st.markdown(f"💰 **Custo:** R${custo:,.2f}")
    
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0

    if saldo < custo:
        st.error("💸 Saldo insuficiente.")
    else:
        if st.button(f"📈 Melhorar Estádio para Nível {nivel + 1}"):
            nova_capacidade = capacidade_por_nivel[nivel + 1]
            supabase.table("estadios").update({
                "nivel": nivel + 1,
                "capacidade": nova_capacidade,
                "em_melhorias": False,
                "data_inicio_melhoria": None
            }).eq("id_time", id_time).execute()
            novo_saldo = saldo - custo
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
            st.success("✅ Estádio melhorado com sucesso!")
            st.experimental_rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")
