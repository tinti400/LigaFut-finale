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

if "nome_time" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado com um time válido para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

# 📊 Parâmetros do estádio
capacidade_por_nivel = {
    1: 25000,
    2: 47500,
    3: 67500,
    4: 87500,
    5: 110000
}

setores = {
    "geral": 0.40,
    "arquibancada": 0.30,
    "cadeira": 0.20,
    "camarote": 0.10
}

# 💸 Custo para melhoria
custo_base = 250_000_000
custo_por_nivel = 120_000_000
preco_medio_ingresso = 80

# 🎯 Carrega dados do estádio
res = supabase.table("estadios").select("*").eq("id_time", str(id_time)).execute()
dados_estadio = res.data[0] if res.data else None

if not dados_estadio:
    # Cria estádio se não existir
    supabase.table("estadios").insert({
        "id_time": str(id_time),
        "nivel": 1,
        "capacidade": capacidade_por_nivel[1]
    }).execute()
    dados_estadio = {
        "nivel": 1,
        "capacidade": capacidade_por_nivel[1]
    }

nivel = dados_estadio.get("nivel", 1)
capacidade_atual = dados_estadio.get("capacidade", capacidade_por_nivel[1])
capacidade_correta = capacidade_por_nivel.get(nivel, 25000)

# 🔄 Corrige capacidade caso esteja divergente
if capacidade_atual != capacidade_correta:
    supabase.table("estadios").update({
        "capacidade": capacidade_correta
    }).eq("id_time", str(id_time)).execute()
    capacidade_atual = capacidade_correta

# 🖼️ Exibição do estádio
st.subheader(f"🏟️ Estádio do {nome_time}")
st.metric("Nível atual", nivel)
st.metric("Capacidade atual", f"{capacidade_atual:,}".replace(",", "."))

# 📈 Projeção por setor
st.markdown("### 💺 Setores do Estádio")
df_setores = pd.DataFrame(columns=["Setor", "Capacidade", "Proporção"])
for setor, proporcao in setores.items():
    capacidade = int(capacidade_atual * proporcao)
    df_setores.loc[len(df_setores)] = [setor.capitalize(), f"{capacidade:,}".replace(",", "."), f"{int(proporcao * 100)}%"]
st.dataframe(df_setores, use_container_width=True)

# 💰 Receita estimada por jogo
renda_por_jogo = capacidade_atual * preco_medio_ingresso
st.metric("💰 Receita estimada por jogo", f"R$ {renda_por_jogo:,.0f}".replace(",", "."))

# 📊 Buscar jogos em casa
try:
    res_rodadas = supabase.table("rodadas").select("jogos").execute()
    todas_rodadas = res_rodadas.data
except Exception as e:
    st.error(f"Erro ao buscar rodadas: {e}")
    todas_rodadas = []

jogos_em_casa = 0
for rodada in todas_rodadas:
    jogos = rodada.get("jogos", [])
    for jogo in jogos:
        if jogo.get("mandante") == id_time:
            jogos_em_casa += 1

receita_total = jogos_em_casa * renda_por_jogo

col1, col2 = st.columns(2)
with col1:
    st.metric("📆 Jogos em casa", jogos_em_casa)
with col2:
    st.metric("💸 Receita acumulada estimada", f"R$ {receita_total:,.0f}".replace(",", "."))

# 📤 Melhorar Estádio
if nivel < 5:
    novo_nivel = nivel + 1
    nova_capacidade = capacidade_por_nivel[novo_nivel]
    custo = custo_base + (nivel - 1) * custo_por_nivel

    st.markdown("---")
    st.subheader("🔧 Melhorar Estádio")
    st.markdown(f"Melhore seu estádio para o **nível {novo_nivel}** com capacidade de **{nova_capacidade:,}** lugares.")
    st.markdown(f"💸 Custo: **R$ {custo:,.0f}**".replace(",", "."))

    # Verifica saldo do time
    saldo_res = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
    saldo_atual = saldo_res.data[0]["saldo"] if saldo_res.data else 0
    st.metric("💼 Saldo atual", f"R$ {saldo_atual:,.0f}".replace(",", "."))

    if saldo_atual < custo:
        st.error("❌ Saldo insuficiente para realizar a melhoria.")
    else:
        if st.button("✅ Confirmar melhoria do estádio"):
            # Atualiza estádio
            supabase.table("estadios").update({
                "nivel": novo_nivel,
                "capacidade": nova_capacidade
            }).eq("id_time", str(id_time)).execute()

            # Atualiza saldo do time
            novo_saldo = saldo_atual - custo
            supabase.table("times").update({
                "saldo": novo_saldo
            }).eq("id", str(id_time)).execute()

            # Registra movimentação
            registrar_movimentacao(
                id_time=id_time,
                valor=-custo,
                tipo="gasto",
                categoria="estadio",
                descricao=f"Melhoria do estádio para nível {novo_nivel}"
            )

            st.success("✅ Estádio melhorado com sucesso!")
            st.rerun()
else:
    st.success("🏟️ Seu estádio já está no nível máximo.")
