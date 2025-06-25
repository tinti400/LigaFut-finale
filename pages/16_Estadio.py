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

def custo_melhoria(nivel):
    return 250_000_000 + (nivel - 1) * 120_000_000

def calcular_publico(capacidade_setor, preco):
    demanda_base = capacidade_setor * 1.1
    fator_preco = max(0.3, 1 - (preco - 20) * 0.03)
    return int(min(capacidade_setor, demanda_base * fator_preco))

# 🔄 Buscar ou criar estádio
res = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res.data[0] if res.data else None

if not estadio:
    estadio_novo = {
        "id_time": id_time,
        "nome": f"Estádio {nome_time}",
        "nivel": 1,
        "capacidade": capacidade_por_nivel[1],
        "em_melhorias": False,
        "preco_geral": 20.0,
        "preco_norte": 20.0,
        "preco_sul": 20.0,
        "preco_central": 20.0,
        "preco_camarote": 20.0
    }
    supabase.table("estadios").insert(estadio_novo).execute()
    estadio = estadio_novo
else:
    nivel_atual = estadio.get("nivel", 1)
    capacidade_correta = capacidade_por_nivel.get(nivel_atual, 25000)
    if estadio.get("capacidade", 0) != capacidade_correta:
        estadio["capacidade"] = capacidade_correta
        supabase.table("estadios").update({"capacidade": capacidade_correta}).eq("id_time", id_time).execute()

# Dados atuais
nivel = estadio["nivel"]
capacidade_total = estadio["capacidade"]
em_melhorias = estadio.get("em_melhorias", False)

precos = {
    setor: float(estadio.get(f"preco_{setor}", 20.0))
    for setor in setores
}

st.markdown(f"## 🏟️ Estádio {nome_time}")
st.markdown(f"- **Nível atual:** {nivel}")
st.markdown(f"- **Capacidade total:** {capacidade_total:,} torcedores")

# 🎫 Edição de preços
st.markdown("### 🎫 Preço por Setor")
with st.form("form_precos"):
    novos_precos = {}
    for setor, proporcao in setores.items():
        label = setor.capitalize()
        valor = st.number_input(f"{label}", min_value=1.0, max_value=2000.0, step=1.0, value=precos[setor], key=f"preco_{setor}")
        novos_precos[setor] = valor

    if st.form_submit_button("💾 Atualizar Preços"):
        campos = {f"preco_{k}": v for k, v in novos_precos.items()}
        supabase.table("estadios").update(campos).eq("id_time", id_time).execute()
        st.success("✅ Preços atualizados com sucesso!")
        st.rerun()

# 📊 Cálculo por setor
st.markdown("### 📈 Estimativa de Público e Renda por Setor")
dados = []
renda_total = 0
for setor, proporcao in setores.items():
    capacidade = int(capacidade_total * proporcao)
    preco = precos[setor]
    publico = calcular_publico(capacidade, preco)
    renda = publico * preco
    renda_total += renda
    dados.append({
        "Setor": setor.capitalize(),
        "Capacidade": capacidade,
        "Preço": f"R${preco:.2f}",
        "Público Estimado": publico,
        "Renda Estimada": f"R${renda:,.2f}"
    })

df = pd.DataFrame(dados)
st.dataframe(df, use_container_width=True)

st.markdown(f"### 💰 Renda Total Estimada: R${renda_total:,.2f}")

# 📈 Melhorar estádio
if nivel < 5:
    custo = custo_melhoria(nivel + 1)
    st.markdown(f"---\n### 🏗️ Melhorar Estádio para Nível {nivel + 1}")
    st.markdown(f"💸 **Custo:** R${custo:,.2f}")

    if em_melhorias:
        st.info("⏳ O estádio já está em obras.")
    else:
        res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

        if saldo < custo:
            st.error("💰 Saldo insuficiente para realizar a melhoria.")
        else:
            if st.button(f"📈 Confirmar Melhoria"):
                nova_capacidade = capacidade_por_nivel[nivel + 1]
                supabase.table("estadios").update({
                    "nivel": nivel + 1,
                    "capacidade": nova_capacidade,
                    "em_melhorias": True
                }).eq("id_time", id_time).execute()

                novo_saldo = saldo - custo
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
                registrar_movimentacao(id_time, "saida", custo, f"Melhoria do estádio para nível {nivel + 1}")
                st.success("🏗️ Estádio em obras!")
                st.rerun()
else:
    st.success("🌟 Estádio já está no nível máximo!")

# 👑 Admin: Ranking
res_admin = supabase.table("admins").select("*").eq("email", email_usuario).execute()
if res_admin.data:
    st.markdown("---")
    st.markdown("## 👑 Ranking de Estádios (Admin)")

    res_est = supabase.table("estadios").select("*").execute()
    res_times = supabase.table("times").select("id, nome").execute()
    nomes_times = {t["id"]: t["nome"] for t in res_times.data}

    dados = []
    for est in res_est.data:
        id_t = est["id_time"]
        nome = nomes_times.get(id_t, "Desconhecido")
        nivel = est.get("nivel", 1)
        capacidade = est.get("capacidade", 0)
        total_renda = 0
        for setor in setores:
            preco = float(est.get(f"preco_{setor}", 20.0))
            capacidade_setor = int(capacidade * setores[setor])
            publico = calcular_publico(capacidade_setor, preco)
            total_renda += publico * preco

        dados.append({
            "Time": nome,
            "Nível": nivel,
            "Capacidade": capacidade,
            "Renda Estimada": f"R${total_renda:,.2f}"
        })

    df = pd.DataFrame(dados).sort_values(by="Capacidade", ascending=False)
    st.dataframe(df, height=600)

