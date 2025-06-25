# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="🏟️ Estádio - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🧠 Funções auxiliares
def calcular_publico(capacidade, preco_ingresso, nivel):
    demanda_base = capacidade * (0.9 + nivel * 0.02)
    fator_preco = max(0.3, 1 - (preco_ingresso - 20) * 0.03)
    publico = int(min(capacidade, demanda_base * fator_preco))
    return publico

def custo_melhoria(nivel_atual):
    base = 250_000_000
    incremento = 120_000_000
    return base + (nivel_atual - 1) * incremento

def capacidade_por_nivel(nivel):
    capacidades = {
        1: 25000,
        2: 40000,
        3: 60000,
        4: 85000,
        5: 110000
    }
    return capacidades.get(nivel, 25000)

# 🔄 Buscar ou criar estádio
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

if not estadio:
    estadio_novo = {
        "id_time": id_time,
        "nome": f"Estádio {nome_time}",
        "nivel": 1,
        "capacidade": capacidade_por_nivel(1),
        "preco_ingresso": 20.0,
        "em_melhorias": False
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo

# 🔢 Dados do estádio
nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)
preco_ingresso = float(estadio.get("preco_ingresso", 20.0))
publico_estimado = calcular_publico(capacidade, preco_ingresso, nivel)
renda = publico_estimado * preco_ingresso

# 🎨 Exibição
st.markdown(f"## 🏟️ {nome}")
st.markdown(f"""
- **Nível atual:** {nivel}
- **Capacidade:** {capacidade:,} torcedores
- **Preço do ingresso:** R${preco_ingresso:.2f}
- **Público médio estimado:** {publico_estimado:,} torcedores
- **Renda por jogo (como mandante):** R${renda:,.2f}
""")

# 💵 Atualizar preço do ingresso
novo_preco = st.number_input("🎫 Definir novo preço médio do ingresso (R$)", value=preco_ingresso, min_value=5.0, max_value=100.0, step=1.0)
if novo_preco != preco_ingresso:
    if st.button("💾 Atualizar Preço do Ingresso"):
        supabase.table("estadios").update({"preco_ingresso": novo_preco}).eq("id_time", id_time).execute()
        st.success("✅ Preço atualizado com sucesso!")
        st.experimental_rerun()

# 🏗️ Melhorar estádio
if nivel < 5:
    custo = custo_melhoria(nivel)
    if em_melhorias:
        st.info("⏳ O estádio já está em obras. Aguarde a finalização antes de nova melhoria.")
    else:
        st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
        st.markdown(f"💸 **Custo:** R${custo:,.2f}")

        # Buscar saldo
        res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo = res_saldo.data[0]["saldo"]

        if saldo < custo:
            st.error("💰 Saldo insuficiente para realizar a melhoria.")
        else:
            if st.button(f"📈 Melhorar Estádio para Nível {nivel + 1}"):
                nova_capacidade = capacidade_por_nivel(nivel + 1)
                supabase.table("estadios").update({
                    "nivel": nivel + 1,
                    "capacidade": nova_capacidade,
                    "em_melhorias": True
                }).eq("id_time", id_time).execute()

                novo_saldo = saldo - custo
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
                st.success("🏗️ Estádio em obras! A melhoria será concluída em breve.")
                st.experimental_rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")

