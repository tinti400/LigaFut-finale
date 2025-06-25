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

# ⚠️ Verifica se 'nome_time' está na sessão
if "nome_time" not in st.session_state:
    st.warning("Você precisa estar logado com um time válido para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

# 📐 Regras atualizadas
capacidade_por_nivel = {
    1: 25000,
    2: 47500,
    3: 67500,
    4: 87500,
    5: 110000
}

def custo_melhoria(nivel):
    return 250_000_000 + (nivel - 1) * 120_000_000

def calcular_publico(capacidade, preco_medio, nivel):
    demanda_base = capacidade * (0.9 + nivel * 0.02)
    fator_preco = max(0.3, 1 - (preco_medio - 20) * 0.03)
    return int(min(capacidade, demanda_base * fator_preco))

# 🔄 Buscar ou criar estádio
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

# 🆕 Criar novo estádio se não existir
if not estadio:
    estadio_novo = {
        "id_time": id_time,
        "nome": f"Estádio {nome_time}",
        "nivel": 1,
        "capacidade": capacidade_por_nivel[1],
        "preco_geral": 20.0,
        "preco_sul": 25.0,
        "preco_norte": 25.0,
        "preco_central": 40.0,
        "preco_camarote": 100.0,
        "em_melhorias": False
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo
else:
    nivel_atual = estadio.get("nivel", 1)
    capacidade_correta = capacidade_por_nivel.get(nivel_atual, 25000)
    if estadio.get("capacidade", 0) != capacidade_correta:
        estadio["capacidade"] = capacidade_correta
        supabase.table("estadios").update({"capacidade": capacidade_correta}).eq("id_time", id_time).execute()

# 📊 Dados do estádio
nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)

preco_geral = float(estadio.get("preco_geral", 20.0))
preco_sul = float(estadio.get("preco_sul", 25.0))
preco_norte = float(estadio.get("preco_norte", 25.0))
preco_central = float(estadio.get("preco_central", 40.0))
preco_camarote = float(estadio.get("preco_camarote", 100.0))

# 🧮 Percentuais por setor
percentuais = {
    "geral": 0.4,
    "sul": 0.15,
    "norte": 0.15,
    "central": 0.2,
    "camarote": 0.1
}

preco_medio = (preco_geral * percentuais["geral"] +
               preco_sul * percentuais["sul"] +
               preco_norte * percentuais["norte"] +
               preco_central * percentuais["central"] +
               preco_camarote * percentuais["camarote"])

publico_total = calcular_publico(capacidade, preco_medio, nivel)
setores = {
    "Geral": (int(publico_total * percentuais["geral"]), preco_geral),
    "Arquibancada Sul": (int(publico_total * percentuais["sul"]), preco_sul),
    "Arquibancada Norte": (int(publico_total * percentuais["norte"]), preco_norte),
    "Arquibancada Central": (int(publico_total * percentuais["central"]), preco_central),
    "Camarote": (int(publico_total * percentuais["camarote"]), preco_camarote)
}

renda_total = sum(qtd * preco for qtd, preco in setores.values())

st.markdown(f"## 🏟️ {nome}")
st.markdown(f"**Capacidade Total:** {capacidade:,} torcedores\n\n**Público Estimado:** {publico_total:,} torcedores\n\n**Renda Estimada:** R${renda_total:,.2f}")

st.markdown("### 📊 Setores do Estádio")
for setor, (qtd, preco) in setores.items():
    st.markdown(f"- **{setor}**: {qtd:,} torcedores x R${preco:.2f} = R${qtd * preco:,.2f}")

st.markdown("### ✏️ Definir Preços por Setor (entre R$1 e R$2.000)")
col1, col2 = st.columns(2)
with col1:
    novo_geral = st.number_input("🎫 Geral", value=preco_geral, min_value=1.0, max_value=2000.0)
    novo_sul = st.number_input("🎫 Arquibancada Sul", value=preco_sul, min_value=1.0, max_value=2000.0)
    novo_norte = st.number_input("🎫 Arquibancada Norte", value=preco_norte, min_value=1.0, max_value=2000.0)
with col2:
    novo_central = st.number_input("🎫 Arquibancada Central", value=preco_central, min_value=1.0, max_value=2000.0)
    novo_camarote = st.number_input("🎫 Camarote", value=preco_camarote, min_value=1.0, max_value=2000.0)

if st.button("💾 Salvar preços dos setores"):
    supabase.table("estadios").update({
        "preco_geral": novo_geral,
        "preco_sul": novo_sul,
        "preco_norte": novo_norte,
        "preco_central": novo_central,
        "preco_camarote": novo_camarote
    }).eq("id_time", id_time).execute()
    st.success("✅ Preços atualizados com sucesso!")
    st.rerun()

# 🏗️ Melhorar estádio
if nivel < 5:
    custo = custo_melhoria(nivel + 1)
    if em_melhorias:
        st.info("⏳ O estádio já está em obras. Aguarde a finalização antes de nova melhoria.")
    else:
        st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
        st.markdown(f"💸 **Custo:** R${custo:,.2f}")

        res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo = res_saldo.data[0]["saldo"]

        if saldo < custo:
            st.error("💰 Saldo insuficiente para realizar a melhoria.")
        else:
            if st.button(f"📈 Melhorar Estádio para Nível {nivel + 1}"):
                nova_capacidade = capacidade_por_nivel[nivel + 1]
                supabase.table("estadios").update({
                    "nivel": nivel + 1,
                    "capacidade": nova_capacidade,
                    "em_melhorias": True
                }).eq("id_time", id_time).execute()

                novo_saldo = saldo - custo
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
                registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
                st.success("🏗️ Estádio em obras! A melhoria será concluída em breve.")
                st.rerun()
else:
    st.success("🌟 Estádio já está no nível máximo (5). Parabéns!")

# 👑 Painel de Administrador
res_admin = supabase.table("admins").select("*").eq("email", email_usuario).execute()
if res_admin.data:
    st.markdown("---")
    st.markdown("## 👑 Ranking de Estádios (Admin)")

    try:
        res_est = supabase.table("estadios").select("*").execute()
        res_times = supabase.table("times").select("id, nome").execute()
        nomes_times = {t["id"]: t["nome"] for t in res_times.data}

        dados = []
        for est in res_est.data:
            id_t = est["id_time"]
            nome = nomes_times.get(id_t, "Desconhecido")
            nivel = est.get("nivel", 1)
            capacidade = est.get("capacidade", 0)
            preco_medio_est = (float(est.get("preco_geral", 20.0)) * percentuais["geral"] +
                               float(est.get("preco_sul", 25.0)) * percentuais["sul"] +
                               float(est.get("preco_norte", 25.0)) * percentuais["norte"] +
                               float(est.get("preco_central", 40.0)) * percentuais["central"] +
                               float(est.get("preco_camarote", 100.0)) * percentuais["camarote"])

            publico = calcular_publico(capacidade, preco_medio_est, nivel)
            renda = publico * preco_medio_est

            dados.append({
                "Time": nome,
                "Nível": nivel,
                "Capacidade": capacidade,
                "Público": publico,
                "Renda Estimada": f"R${renda:,.2f}"
            })

        df = pd.DataFrame(dados).sort_values(by="Capacidade", ascending=False)
        st.dataframe(df, height=600)
    except Exception as e:
        st.error(f"Erro ao carregar ranking: {e}")
