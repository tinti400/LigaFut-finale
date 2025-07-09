# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao
import matplotlib.pyplot as plt

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

# 📌 Níveis de capacidade
capacidade_por_nivel = {
    1: 25000,
    2: 47500,
    3: 67500,
    4: 87500,
    5: 110000
}

# 🧠 Verifica naming rights com benefícios extras
res_naming = supabase.table("naming_rights").select("*").eq("id_time", id_time).eq("ativo", True).execute()
beneficio_extra = res_naming.data[0].get("beneficio_extra", "") if res_naming.data else ""

# 📌 Setores e proporções
setores = {
    "geral": 0.40,
    "norte": 0.20,
    "sul": 0.20,
    "central": 0.15,
    "camarote": 0.05
}
if beneficio_extra == "area_vip":
    setores["vip"] = 0.02

# Preços padrão
precos_padrao = {
    "geral": 20.0,
    "norte": 40.0,
    "sul": 40.0,
    "central": 60.0,
    "camarote": 100.0,
    "vip": 1500.0
}

# Limites de preço por nível
limites_precos = {
    1: {"geral": 100.0, "norte": 150.0, "sul": 150.0, "central": 200.0, "camarote": 1000.0, "vip": 5000.0},
    2: {"geral": 150.0, "norte": 200.0, "sul": 200.0, "central": 300.0, "camarote": 1500.0, "vip": 5000.0},
    3: {"geral": 200.0, "norte": 250.0, "sul": 250.0, "central": 400.0, "camarote": 2000.0, "vip": 5000.0},
    4: {"geral": 250.0, "norte": 300.0, "sul": 300.0, "central": 500.0, "camarote": 2500.0, "vip": 5000.0},
    5: {"geral": 300.0, "norte": 350.0, "sul": 350.0, "central": 600.0, "camarote": 3000.0, "vip": 5000.0},
}

# 🔍 Funções auxiliares
def buscar_posicao_time(id_time):
    try:
        res = supabase.table("classificacao").select("id_time").order("pontos", desc=True).execute()
        lista_ids = [t["id_time"] for t in res.data]
        return lista_ids.index(id_time) + 1 if id_time in lista_ids else 20
    except:
        return 20

def buscar_resultados_recentes(id_time, limite=5):
    try:
        res = supabase.table("resultados").select("*").or_(f"mandante.eq.{id_time},visitante.eq.{id_time}").order("data_jogo", desc=True).limit(limite).execute()
        vitorias, derrotas = 0, 0
        for r in res.data:
            if r["mandante"] == id_time:
                if r["gols_mandante"] > r["gols_visitante"]: vitorias += 1
                elif r["gols_mandante"] < r["gols_visitante"]: derrotas += 1
            elif r["visitante"] == id_time:
                if r["gols_visitante"] > r["gols_mandante"]: vitorias += 1
                elif r["gols_visitante"] < r["gols_mandante"]: derrotas += 1
        return vitorias, derrotas
    except:
        return 0, 0

def calcular_publico_setor(lugares, preco, desempenho, posicao, vitorias, derrotas):
    fator_base = 0.8 + desempenho * 0.007 + (20 - posicao) * 0.005 + vitorias * 0.01 - derrotas * 0.005
    if preco <= 20: fator_preco = 1.0
    elif preco <= 50: fator_preco = 0.85
    elif preco <= 100: fator_preco = 0.65
    elif preco <= 200: fator_preco = 0.4
    elif preco <= 500: fator_preco = 0.2
    else: fator_preco = 0.05
    publico_estimado = int(min(lugares, lugares * fator_base * fator_preco))
    renda = publico_estimado * preco
    return publico_estimado, renda

# 🎯 Buscar dados do estádio
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
    estadio = supabase.table("estadios").select("*").eq("id_time", id_time).execute().data[0]
else:
    nivel_atual = estadio.get("nivel", 1)
    capacidade_correta = capacidade_por_nivel.get(nivel_atual, 25000)
    if estadio.get("capacidade", 0) != capacidade_correta:
        estadio["capacidade"] = capacidade_correta
        supabase.table("estadios").update({"capacidade": capacidade_correta}).eq("id_time", id_time).execute()

# Dados auxiliares
res_d = supabase.table("classificacao").select("vitorias").eq("id_time", id_time).execute()
desempenho = res_d.data[0]["vitorias"] if res_d.data else 0
posicao = buscar_posicao_time(id_time)
vitorias_recentes, derrotas_recentes = buscar_resultados_recentes(id_time)

nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]

# UI
st.markdown(f"## 🏟️ {nome}")
novo_nome = st.text_input("✏️ Renomear Estádio", value=nome)
if novo_nome and novo_nome != nome:
    supabase.table("estadios").update({"nome": novo_nome}).eq("id_time", id_time).execute()
    st.success("✅ Nome atualizado!")
    st.experimental_rerun()

st.markdown(f"- **Nível atual:** {nivel}\n- **Capacidade:** {capacidade:,} torcedores")

# 💸 Preços por setor
st.markdown("### 🎛 Preços por Setor")
publico_total = 0
renda_total = 0

for setor, proporcao in setores.items():
    col1, col2, col3 = st.columns([3, 2, 2])
    lugares = int(capacidade * proporcao)
    preco_atual = float(estadio.get(f"preco_{setor}", precos_padrao[setor]))
    limite_setor = limites_precos[nivel].get(setor, 5000.0)

    novo_preco = col1.number_input(
        f"Preço - {setor.upper()}",
        min_value=1.0,
        max_value=limite_setor,
        value=min(preco_atual, limite_setor),
        step=1.0,
        key=f"preco_{setor}"
    )

    if novo_preco >= limite_setor * 0.9:
        col1.warning(f"⚠️ Valor próximo ao limite de R${limite_setor:,.2f}")

    if novo_preco != preco_atual:
        supabase.table("estadios").update({f"preco_{setor}": novo_preco}).eq("id_time", id_time).execute()
        st.experimental_rerun()

    publico, renda = calcular_publico_setor(lugares, novo_preco, desempenho, posicao, vitorias_recentes, derrotas_recentes)
    col2.markdown(f"👥 Público estimado: **{publico:,}**")
    col3.markdown(f"💰 Renda estimada: **R${renda:,.2f}**")
    publico_total += publico
    renda_total += renda

# 🚗 Renda de Estacionamento
renda_estacionamento = 0
if beneficio_extra == "estacionamento":
    veiculos = publico_total // 3
    renda_estacionamento = veiculos * 10
    st.markdown(f"🚗 Estacionamento estimado: **{veiculos:,} veículos**")
    st.markdown(f"💵 Renda de estacionamento: **R${renda_estacionamento:,.2f}**")
    renda_total += renda_estacionamento

st.markdown(f"### 📊 Público total estimado: **{publico_total:,}**")
st.markdown(f"### 💸 Renda total estimada (com estacionamento): **R${renda_total:,.2f}**")

# 🔧 Melhorias
if nivel < 5:
    custo = 250_000_000 + (nivel) * 120_000_000
    st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
    st.markdown(f"💸 **Custo:** R${custo:,.2f}")
    res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = res_saldo.data[0].get("saldo", 0) if res_saldo.data else 0

    if saldo < custo:
        st.error("💰 Saldo insuficiente.")
    else:
        if st.button(f"📈 Melhorar Estádio para Nível {nivel + 1}"):
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

