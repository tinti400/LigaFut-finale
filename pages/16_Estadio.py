# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao
import pandas as pd

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
    custos = {
        1: 5_000_000,
        2: 10_000_000,
        3: 20_000_000,
        4: 30_000_000
    }
    return custos.get(nivel_atual, None)

# 🔄 Buscar ou criar estádio
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

if not estadio:
    estadio_novo = {
        "id_time": id_time,
        "nome": f"Estádio {nome_time}",
        "nivel": 1,
        "capacidade": 10000,
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
                nova_capacidade = capacidade + 10000
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

# 📊 Ranking de Estádios
st.markdown("---")
st.subheader("📊 Ranking dos Estádios")

res_todos = supabase.table("estadios").select("id_time, nome, nivel, capacidade, preco_ingresso").execute().data
dados = []
for est in res_todos:
    idt = est["id_time"]
    preco = float(est.get("preco_ingresso", 20.0))
    nivel = est.get("nivel", 1)
    capacidade = est.get("capacidade", 10000)
    publico = calcular_publico(capacidade, preco, nivel)
    renda = publico * preco

    # Nome do time
    nome_time_res = supabase.table("times").select("nome").eq("id", idt).execute()
    nome_time_est = nome_time_res.data[0]["nome"] if nome_time_res.data else "Desconhecido"

    dados.append({
        "Time": nome_time_est,
        "Estádio": est.get("nome", "Estádio"),
        "Nível": nivel,
        "Capacidade": capacidade,
        "Preço Ingresso (R$)": preco,
        "Público Médio": publico,
        "Renda Média (R$)": renda
    })

df_estadios = pd.DataFrame(dados).sort_values(by="Renda Média (R$)", ascending=False).reset_index(drop=True)
st.dataframe(df_estadios, use_container_width=True)

