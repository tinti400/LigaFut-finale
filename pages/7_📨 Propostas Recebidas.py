# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao
import uuid

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# 🔄 Buscar propostas recebidas
res = supabase.table("propostas").select("*").eq("id_time_alvo", id_time).eq("status", "pendente").execute()
propostas = res.data or []

if not propostas:
    st.info("Você não tem propostas pendentes.")
    st.stop()

for prop in propostas:
    st.markdown("---")
    st.markdown(f"### 👤 Jogador: {prop['jogador_nome']}")
    st.markdown(f"📌 Posição: {prop['jogador_posicao']}")
    st.markdown(f"⭐ Overall: {prop['jogador_overall']}")
    st.markdown(f"💰 Valor: R$ {prop['jogador_valor']:,.0f}".replace(",", "."))

    tipo = "💵 Dinheiro"
    if prop["jogadores_oferecidos"]:
        tipo = "🔁 Troca Simples" if len(prop["jogadores_oferecidos"]) == 1 else "🔁 Troca Composta"

    st.markdown(f"📦 Tipo de proposta: **{tipo}**")
    if prop["valor_oferecido"] > 0:
        st.markdown(f"💸 Valor Oferecido: R$ {prop['valor_oferecido']:,.0f}".replace(",", "."))

    if prop["jogadores_oferecidos"]:
        st.markdown("👥 Jogadores Oferecidos:")
        for jogador in prop["jogadores_oferecidos"]:
            st.markdown(f"- {jogador['nome']} (OVR {jogador['overall']})")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Aceitar Proposta", key=f"aceitar_{prop['id']}"):
            try:
                # ✅ Atualizar status da proposta
                supabase.table("propostas").update({"status": "aceita"}).eq("id", prop["id"]).execute()

                # ✅ Remover jogador do time atual
                supabase.table("elenco").delete().eq("id_time", id_time).eq("nome", prop["jogador_nome"]).execute()

                # ✅ Adicionar jogador ao elenco do comprador
                novo_jogador = {
                    "id": str(uuid.uuid4()),
                    "id_time": prop["id_time_origem"],
                    "nome": prop["jogador_nome"],
                    "posicao": prop["jogador_posicao"],
                    "overall": prop["jogador_overall"],
                    "valor": prop["jogador_valor"],
                    "imagem_url": prop.get("imagem_url", ""),
                    "nacionalidade": prop.get("nacionalidade", "-"),
                    "origem": prop.get("origem", "-"),
                    "classificacao": prop.get("classificacao", "")
                }
                supabase.table("elenco").insert(novo_jogador).execute()

                # ✅ Mover jogadores oferecidos (caso tenha)
                for jogador in prop["jogadores_oferecidos"]:
                    # Remover do time comprador
                    supabase.table("elenco").delete().eq("id_time", prop["id_time_origem"]).eq("nome", jogador["nome"]).execute()
                    # Adicionar ao time atual
                    jogador["id"] = str(uuid.uuid4())
                    jogador["id_time"] = id_time
                    supabase.table("elenco").insert(jogador).execute()

                # ✅ Movimentação Financeira
                valor = int(prop["valor_oferecido"])
                if valor > 0:
                    # Saída do comprador
                    registrar_movimentacao(prop["id_time_origem"], "saida", valor, f"Compra de {prop['jogador_nome']}")
                    # Entrada do vendedor
                    registrar_movimentacao(id_time, "entrada", valor, f"Venda de {prop['jogador_nome']}")

                st.success("✅ Proposta aceita com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao aceitar proposta: {e}")
    with col2:
        if st.button("❌ Recusar Proposta", key=f"recusar_{prop['id']}"):
            supabase.table("propostas").update({"status": "recusada"}).eq("id", prop["id"]).execute()
            st.warning("❌ Proposta recusada.")
            st.rerun()
