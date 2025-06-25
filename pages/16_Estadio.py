# -*- coding: utf-8 -*-
import streamlit as st
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
def calcular_renda(capacidade, nivel):
    return capacidade * 10 * nivel

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
        "em_melhorias": False
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo

# 🔢 Dados do estádio
nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)
renda = calcular_renda(capacidade, nivel)

# 🎨 Exibição
st.markdown(f"## 🏟️ {nome}")
st.markdown(f"""
- **Nível atual:** {nivel}
- **Capacidade:** {capacidade:,} torcedores
- **Renda por jogo (como mandante):** R${renda:,.2f}
""")

# 💡 Melhorar estádio
if nivel < 5:
    custo = custo_melhoria(nivel)
    if em_melhorias:
        st.info("⏳ O estádio já está em obras. Aguarde a finalização antes de nova melhoria.")
    else:
        st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
        st.markdown(f"💸 **Custo:** R${custo:,.2f}")

        # Buscar saldo do time
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

                # Debita o valor do time
                novo_saldo = saldo - custo
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                # Registra movimentação
                registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")

                st.success("🏗️ Estádio em obras! A melhoria será concluída em breve.")
                st.rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")

# ✅ Futuras melhorias: aplicar tempo real ou por rodada para finalizar a obra
