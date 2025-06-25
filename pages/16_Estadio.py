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

def calcular_publico_setor(lugares, preco, desempenho):
    fator_base = 0.9 + desempenho * 0.01
    fator_preco = max(0.3, 1 - (preco - 20) * 0.02)
    return int(min(lugares, lugares * fator_base * fator_preco))

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
        "em_melhorias": False,
        **{f"preco_{k}": v for k, v in precos_padrao.items()}
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo
else:
    nivel_atual = estadio.get("nivel", 1)
    capacidade_correta = capacidade_por_nivel.get(nivel_atual, 25000)
    if estadio.get("capacidade", 0) != capacidade_correta:
        estadio["capacidade"] = capacidade_correta
        supabase.table("estadios").update({"capacidade": capacidade_correta}).eq("id_time", id_time).execute()

# 🔄 Buscar desempenho do time
res_d = supabase.table("classificacao").select("vitorias").eq("id_time", id_time).execute()
desempenho = res_d.data[0]["vitorias"] if res_d.data else 0

# 📊 Dados do estádio
nome = estadio["nome"]
nivel = estadio["nivel"]
capacidade = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)

st.markdown(f"## 🏟️ {nome}")
st.markdown(f"- **Nível atual:** {nivel}\n- **Capacidade:** {capacidade:,} torcedores")

# 🎫 Edição de preços por setor
st.markdown("### 🎫 Preços por Setor")
precos_setores = {}
publico_total = 0
renda_total = 0

for setor, proporcao in setores.items():
    col1, col2, col3 = st.columns([3, 2, 2])
    lugares = int(capacidade * proporcao)
    preco_atual = float(estadio.get(f"preco_{setor}", precos_padrao[setor]))
    novo_preco = col1.number_input(f"Preço - {setor.upper()}", min_value=1.0, max_value=2000.0, value=preco_atual, step=1.0, key=f"preco_{setor}")
    if novo_preco != preco_atual:
        supabase.table("estadios").update({f"preco_{setor}": novo_preco}).eq("id_time", id_time).execute()
        st.rerun()

    publico = calcular_publico_setor(lugares, novo_preco, desempenho)
    renda = publico * novo_preco
    col2.markdown(f"👥 Público estimado: **{publico:,}**")
    col3.markdown(f"💰 Renda estimada: **R${renda:,.2f}**")

    publico_total += publico
    renda_total += renda

st.markdown(f"### 📊 Público total estimado: **{publico_total:,}**")
st.markdown(f"### 💸 Renda total estimada: **R${renda_total:,.2f}**")

# 🏗️ Melhorar estádio
if nivel < 5:
    custo = 250_000_000 + (nivel) * 120_000_000
    if em_melhorias:
        st.info("⏳ O estádio já está em obras. Aguarde a finalização antes de nova melhoria.")
    else:
        st.markdown(f"### 🔧 Melhorar para Nível {nivel + 1}")
        st.markdown(f"💸 **Custo:** R${custo:,.2f}")
        res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo = res_saldo.data[0].get("saldo", 0) if res_saldo.data else 0

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
            renda_estimativa = 0
            for setor, proporcao in setores.items():
                preco = float(est.get(f"preco_{setor}", precos_padrao[setor]))
                lugares = int(capacidade * proporcao)
                publico = calcular_publico_setor(lugares, preco, desempenho)
                renda_estimativa += publico * preco

            dados.append({
                "Time": nome,
                "Nível": nivel,
                "Capacidade": capacidade,
                "Renda Estimada": f"R${renda_estimativa:,.2f}"
            })
        df = pd.DataFrame(dados).sort_values(by="Capacidade", ascending=False)
        st.dataframe(df, height=600)
    except Exception as e:
        st.error(f"Erro ao carregar ranking: {e}")

