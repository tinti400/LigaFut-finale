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

# Capacidade por nível
capacidade_por_nivel = {
    1: 25000,
    2: 47500,
    3: 67500,
    4: 87500,
    5: 110000
}

# Setores e proporção
setores = {
    "geral": 0.40,
    "norte": 0.20,
    "sul": 0.20,
    "central": 0.15,
    "camarote": 0.05
}

# Preço padrão por setor
precos_padrao = {
    "geral": 20.0,
    "norte": 40.0,
    "sul": 40.0,
    "central": 60.0,
    "camarote": 100.0
}

# Busca posição na tabela
def buscar_posicao_time(id_time):
    try:
        res = supabase.table("classificacao").select("id_time").order("pontos", desc=True).execute()
        lista_ids = [t["id_time"] for t in res.data]
        return lista_ids.index(id_time) + 1 if id_time in lista_ids else 20
    except:
        return 20

# Busca últimos jogos
def buscar_resultados_recentes(id_time, limite=5):
    try:
        res = supabase.table("resultados").select("*").or_(f"mandante.eq.{id_time},visitante.eq.{id_time}").order("data_jogo", desc=True).limit(limite).execute()
        vitorias, derrotas = 0, 0
        for r in res.data:
            if r["mandante"] == id_time and r["gols_mandante"] > r["gols_visitante"]:
                vitorias += 1
            elif r["visitante"] == id_time and r["gols_visitante"] > r["gols_mandante"]:
                vitorias += 1
            else:
                derrotas += 1
        return vitorias, derrotas
    except:
        return 0, 0

# Calcula público estimado
def calcular_publico_setor(lugares, preco, desempenho, posicao, vitorias, derrotas):
    fator_base = 0.8 + desempenho * 0.007 + (20 - posicao) * 0.005
    fator_base += vitorias * 0.01 - derrotas * 0.005
    if preco <= 20:
        fator_preco = 1.0
    elif preco <= 50:
        fator_preco = 0.8
    elif preco <= 100:
        fator_preco = 0.6
    elif preco <= 200:
        fator_preco = 0.4
    elif preco <= 500:
        fator_preco = 0.2
    else:
        fator_preco = 0.01
    return int(min(lugares, lugares * fator_base * fator_preco))

# 🏟️ Dados do estádio
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

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

# Verifica e corrige capacidade do nível
nivel = estadio.get("nivel", 1)
capacidade_esperada = capacidade_por_nivel[nivel]
if estadio.get("capacidade", 0) != capacidade_esperada:
    estadio["capacidade"] = capacidade_esperada
    supabase.table("estadios").update({"capacidade": capacidade_esperada}).eq("id_time", id_time).execute()

# 🧠 Dados de desempenho
res_d = supabase.table("classificacao").select("vitorias").eq("id_time", id_time).execute()
desempenho = res_d.data[0]["vitorias"] if res_d.data else 0
posicao = buscar_posicao_time(id_time)
vitorias_recentes, derrotas_recentes = buscar_resultados_recentes(id_time)

# 🎯 Interface
st.markdown(f"## 🏟️ {estadio['nome']}")
novo_nome = st.text_input("✏️ Renomear Estádio", value=estadio["nome"])
if novo_nome and novo_nome != estadio["nome"]:
    supabase.table("estadios").update({"nome": novo_nome}).eq("id_time", id_time).execute()
    st.success("✅ Nome atualizado!")
    st.experimental_rerun()

st.markdown(f"- **Nível atual:** {nivel}\n- **Capacidade:** {capacidade_esperada:,} torcedores")

# 💸 Preços por setor
st.markdown("### 🎛 Preços por Setor")
publico_total = 0
renda_total = 0

for setor, proporcao in setores.items():
    col1, col2, col3 = st.columns([3, 2, 2])
    lugares = int(capacidade_esperada * proporcao)
    preco_atual = float(estadio.get(f"preco_{setor}", precos_padrao[setor]))
    novo_preco = col1.number_input(f"Preço - {setor.upper()}", min_value=1.0, max_value=2000.0, value=preco_atual, step=1.0, key=f"preco_{setor}")
    if novo_preco != preco_atual:
        supabase.table("estadios").update({f"preco_{setor}": novo_preco}).eq("id_time", id_time).execute()
        st.experimental_rerun()

    publico = calcular_publico_setor(lugares, novo_preco, desempenho, posicao, vitorias_recentes, derrotas_recentes)
    renda = publico * novo_preco
    col2.markdown(f"👥 Público estimado: **{publico:,}**")
    col3.markdown(f"💰 Renda estimada: **R${renda:,.2f}**")
    publico_total += publico
    renda_total += renda

st.markdown(f"### 📊 Público total estimado: **{publico_total:,}**")
st.markdown(f"### 💸 Renda total estimada: **R${renda_total:,.2f}**")

# 🧱 Evolução do estádio
if nivel < 5:
    custo = 250_000_000 + (nivel) * 120_000_000
    res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

    st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
    st.markdown(f"💸 **Custo:** R${custo:,.2f}")

    if saldo < custo:
        st.error("💰 Saldo insuficiente.")
    else:
        if st.button(f"📈 Evoluir Estádio para Nível {nivel + 1}"):
            nova_capacidade = capacidade_por_nivel[nivel + 1]
            supabase.table("estadios").update({
                "nivel": nivel + 1,
                "capacidade": nova_capacidade
            }).eq("id_time", id_time).execute()

            novo_saldo = saldo - custo
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
            st.success("🏗️ Estádio evoluído com sucesso!")
            st.experimental_rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")
