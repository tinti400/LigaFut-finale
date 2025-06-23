# utils.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão ativa
def verificar_sessao():
    if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 💰 Registrar movimentação financeira (atualiza saldo + histórico)
def registrar_movimentacao(id_time, tipo, valor, descricao):
    """
    Registra uma movimentação financeira e atualiza o saldo do time na tabela 'times'.

    :param id_time: ID do time
    :param tipo: 'entrada' ou 'saida'
    :param valor: valor numérico
    :param descricao: descrição da movimentação
    """
    try:
        # Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo_atual = res.data[0]["saldo"] if res.data else 0

        # Atualizar saldo
        novo_saldo = saldo_atual + valor if tipo == "entrada" else saldo_atual - valor
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Registrar histórico
        nova = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": valor,
            "descricao": descricao,
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes_financeiras").insert(nova).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação financeira: {e}")

# 📈 Registrar movimentação pública no BID
def registrar_bid(id_time, tipo, categoria, jogador, valor, origem="", destino=""):
    """
    Registra uma movimentação para exibição pública no BID (tabela 'movimentacoes').

    :param id_time: ID do time responsável
    :param tipo: 'compra' ou 'venda'
    :param categoria: 'mercado', 'leilao', 'proposta', etc.
    :param jogador: nome do jogador
    :param valor: valor da movimentação
    :param origem: nome do time de origem
    :param destino: nome do time de destino
    """
    try:
        if not all([id_time, tipo, categoria, jogador]) or valor is None:
            st.error("❌ Dados obrigatórios ausentes para registrar no BID.")
            return False

        registro = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": str(tipo),
            "categoria": str(categoria),
            "jogador": str(jogador),
            "valor": int(valor),
            "data": datetime.now().isoformat(),
            "origem": origem or "",
            "destino": destino or ""
        }

        # 🐞 DEBUG VISUAL
        st.markdown("### 🐞 DEBUG BID - Conteúdo enviado:")
        st.json(registro)

        supabase.table("movimentacoes").insert(registro).execute()
        return True

    except Exception as e:
        st.error(f"❌ Erro ao registrar no BID: {e}")
        return False


