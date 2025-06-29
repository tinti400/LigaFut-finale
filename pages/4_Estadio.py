# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
                if r["gols_mandante"] > r["gols_visitante"]:
                    vitorias += 1
                elif r["gols_mandante"] < r["gols_visitante"]:
                    derrotas += 1
            elif r["visitante"] == id_time:
                if r["gols_visitante"] > r["gols_mandante"]:
                    vitorias += 1
                elif r["gols_visitante"] < r["gols_mandante"]:
                    derrotas += 1
        return vitorias, derrotas
    except:
        return 0, 0

def calcular_publico_setor(lugares, preco, desempenho, posicao, vitorias_recentes, derrotas_recentes):
    fator_base = 0.8 + desempenho * 0.007 + (20 - posicao) * 0.005
    fator_base += vitorias_recentes * 0.01 - derrotas_recentes * 0.005

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
    try:
        supabase.table("estadios").insert(estadio_novo).execute()
        res_novo = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
        estadio = res_novo.data[0] if res_novo.data else estadio_novo
    except Exception as e:
        st.error(f"Erro ao criar estádio: {e}")
        st.stop()
else:
    nivel_atual = estadio.get("nivel", 1)
    capacidade_correta = capacidade_por_nivel.get(nivel_atual, 25000)
    if estadio.get("capacidade", 0) != capacidade_correta:
        estadio["capacidade"] = capacidade_correta
        supabase.table("estadios").update({"capacidade": capacidade_correta}).eq("id_time", id_time).execute()

data_inicio = estadio.get("data_inicio_melhoria")
if estadio.get("em_melhorias") and data_inicio:
    try:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        if datetime.now() >= inicio + timedelta(days=3):
            supabase.table("estadios").update({"em_melhorias": False, "data_inicio_melhoria": None}).eq("id_time", id_time).execute()
            estadio["em_melhorias"] = False
    except:
        pass

res_d = supabase.table("classificacao").select("vitorias").eq("id_time", id_time).execute()
desempenho = res_d.data[0]["vitorias"] if res_d.data else 0
posicao = buscar_posicao_time(id_time)
vitorias_recentes, derrotas_recentes = buscar_resultados_recentes(id_time)

nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)

st.markdown(f"## 🏟️ {nome}")
novo_nome = st.text_input("✏️ Renomear Estádio", value=nome)
if novo_nome and novo_nome != nome:
    supabase.table("estadios").update({"nome": novo_nome}).eq("id_time", id_time).execute()
    st.success("✅ Nome atualizado!")
    st.experimental_rerun()

st.markdown(f"- **Nível atual:** {nivel}\n- **Capacidade:** {capacidade:,} torcedores")

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

    publico = calcular_publico_setor(lugares, novo_preco, desempenho, posicao, vitorias_recentes, derrotas_recentes)
    renda = publico * novo_preco
    col2.markdown(f"👥 Público estimado: **{publico:,}**")
    col3.markdown(f"💰 Renda estimada: **R${renda:,.2f}**")
    publico_total += publico
    renda_total += renda

st.markdown(f"### 📊 Público total estimado: **{publico_total:,}**")
st.markdown(f"### 💸 Renda total estimada: **R${renda_total:,.2f}**")

if nivel < 5:
    custo = 250_000_000 + (nivel) * 120_000_000
    if em_melhorias:
        st.info("⌛ O estádio já está em obras. Conclusão prevista para 3 dias.")
    else:
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
                    "capacidade": nova_capacidade,
                    "em_melhorias": True,
                    "data_inicio_melhoria": datetime.now().strftime("%Y-%m-%d")
                }).eq("id_time", id_time).execute()
                novo_saldo = saldo - custo
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
                registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
                st.success("🏗️ Estádio em obras! Conclusão em 3 dias.")
                st.experimental_rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")
