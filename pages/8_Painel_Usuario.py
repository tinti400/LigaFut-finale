# -*- coding: utf-8 -*- 
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔢 Buscar saldo
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
except Exception as e:
    st.error(f"Erro ao carregar saldo: {e}")
    saldo = 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🏷️ Time: {nome_time}")
with col2:
    st.markdown(f"### 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

st.markdown("---")

# ⚡ Ações rápidas
st.markdown("### 🔍 Ações rápidas")
col1, col2 = st.columns(2)

# 👥 Exibe o elenco se ativado
if st.session_state.get("mostrar_elenco", False):
    st.markdown("### 👥 Seu Elenco")

    try:
        # Carrega elenco do time
        elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
        elenco = elenco_ref.data
    except Exception as e:
        st.error(f"Erro ao carregar elenco: {e}")
        elenco = []

    if not elenco:
        st.info("📭 Seu elenco está vazio.")
    else:
        # Exibe os jogadores do elenco
        for jogador in elenco:
            col1, col2, col3, col4, col5 = st.columns([2.5, 2.5, 1.5, 1.5, 2])
            with col1:
                st.markdown(f"**👤 Nome:** {jogador.get('nome', '')}")
            with col2:
                st.markdown(f"**📌 Posição:** {jogador.get('posicao', '')}")
            with col3:
                st.markdown(f"**⭐ Overall:** {jogador.get('overall', '')}")
            with col4:
                st.markdown(f"**💰 Valor:** R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
            with col5:
                # Botão de Vender com chave única
                if st.button(f"❌ Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):  # Usando ID do jogador para chave única
                    try:
                        valor_jogador = jogador.get("valor", 0)
                        valor_recebido = round(valor_jogador * 0.7)  # 70% do valor do jogador

                        # 1. Remove do elenco
                        supabase.table("elenco").delete().eq("id_time", id_time).eq("id", jogador["id"]).execute()

                        # 2. Adiciona no mercado com valor cheio
                        jogador_mercado = {
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"]
                        }
                        supabase.table("mercado_transferencias").insert(jogador_mercado).execute()

                        # 3. Atualiza saldo
                        novo_saldo = saldo + valor_recebido
                        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                        st.success(f"✅ {jogador['nome']} vendido! Você recebeu R$ {valor_recebido:,.0f}".replace(",", "."))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao vender jogador: {e}")

        st.markdown("---")

with col1:
    if st.button("👥 Ver Elenco", key="ver_elenco"):
        st.session_state["mostrar_elenco"] = not st.session_state.get("mostrar_elenco", False)

# 📜 Definir Formação Tática
st.markdown("### 📜 Definir Formação Tática")
formacao_tatica = st.text_input("Defina sua formação tática (ex: 4-4-2)")

if formacao_tatica:
    st.markdown(f"**Formação atual: {formacao_tatica}**")

# ⚽ Escalação dos jogadores
st.markdown("### ⚽ Escale seus jogadores")
col1, col2 = st.columns(2)

with col1:
    goleiros = [j for j in elenco if j["posicao"] == "GL"]
    if goleiros:
        goleiro_escalado = st.selectbox("Goleiro", options=[g["nome"] for g in goleiros], key="goleiro")
    else:
        st.warning("Nenhum goleiro disponível no elenco.")

with col2:
    defensores = [j for j in elenco if j["posicao"] in ["LD", "ZAG", "LE"]]
    if defensores:
        defesa_escalada = st.selectbox("Defensores", options=[d["nome"] for d in defensores], key="defesa")
    else:
        st.warning("Nenhum defensor disponível no elenco.")

# Salvar escalação
if st.button("💾 Salvar Escalação"):
    # Aqui você pode salvar a formação tática e escalação no banco de dados
    st.success(f"Formação tática {formacao_tatica} e escalação salva com sucesso!")