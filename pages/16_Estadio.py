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

def calcular_desempenho(supabase, id_time):
    try:
        res = supabase.table("resultados").select("*").eq("id_time", id_time).order("rodada", desc=True).limit(5).execute()
        jogos = res.data
        pontuacao = 0
        for jogo in jogos:
            if jogo.get("resultado") == "vitoria":
                pontuacao += 3
            elif jogo.get("resultado") == "empate":
                pontuacao += 1
        return pontuacao
    except:
        return 7

def calcular_publico(capacidade, preco_ingresso, nivel, desempenho):
    demanda_base = capacidade * (0.9 + nivel * 0.02)
    fator_desempenho = 0.8 + (desempenho / 15) * 0.4
    fator_preco = max(0.3, 1 - (preco_ingresso - 20) * 0.03)
    return int(min(capacidade, demanda_base * fator_preco * fator_desempenho))

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
        "preco_ingresso": 20.0,
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
preco_ingresso = float(estadio.get("preco_ingresso", 20.0))
em_melhorias = estadio.get("em_melhorias", False)

desempenho = calcular_desempenho(supabase, id_time)
publico_estimado = calcular_publico(capacidade, preco_ingresso, nivel, desempenho)
renda = publico_estimado * preco_ingresso

st.markdown(f"## 🏟️ {nome}")
st.markdown(f"""
- **Nível atual:** {nivel}
- **Capacidade:** {capacidade:,} torcedores
- **Preço do ingresso:** R${preco_ingresso:.2f}
- **Público médio estimado:** {publico_estimado:,} torcedores
- **Renda por jogo (como mandante):** R${renda:,.2f}
""")

# 💰 Atualizar preço do ingresso
novo_preco = st.number_input("🎫 Definir novo preço médio do ingresso (R$)", value=preco_ingresso, min_value=1.0, max_value=2000.0, step=1.0)
if novo_preco != preco_ingresso:
    if st.button("💾 Atualizar Preço do Ingresso"):
        supabase.table("estadios").update({"preco_ingresso": novo_preco}).eq("id_time", id_time).execute()
        st.success("✅ Preço atualizado com sucesso!")
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
        saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

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
            preco = float(est.get("preco_ingresso", 20.0))
            desempenho = calcular_desempenho(supabase, id_t)
            publico = calcular_publico(capacidade, preco, nivel, desempenho)
            renda = publico * preco

            dados.append({
                "Time": nome,
                "Nível": nivel,
                "Capacidade": capacidade,
                "Ingresso": f"R${preco:.2f}",
                "Público": publico,
                "Renda Estimada": f"R${renda:,.2f}"
            })

        df = pd.DataFrame(dados).sort_values(by="Capacidade", ascending=False)
        st.dataframe(df, height=600)
    except Exception as e:
        st.error(f"Erro ao carregar ranking: {e}")

