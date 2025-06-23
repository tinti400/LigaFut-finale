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

# 💰 Registrar movimentação financeira (controle interno)
def registrar_movimentacao_financeira(id_time, tipo, valor, descricao):
    """
    Registra uma movimentação na tabela 'movimentacoes_financeiras'.

    :param id_time: ID do time
    :param tipo: 'entrada' ou 'saida'
    :param valor: valor numérico (float ou int)
    :param descricao: descrição da transação
    """
    try:
        nova = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": float(valor),
            "descricao": descricao,
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes_financeiras").insert(nova).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação financeira: {e}")

# 📋 Registrar no BID (log completo de transferências e negociações)
def registrar_movimentacao(id_time, tipo, valor, descricao, categoria="mercado", jogador=None, origem=None, destino=None):
    """
    Registra uma movimentação visível no BID (tabela 'movimentacoes').

    :param id_time: ID do time que realizou a ação
    :param tipo: 'compra', 'venda', 'leilão', etc.
    :param valor: valor numérico da transação
    :param descricao: descrição da movimentação
    :param categoria: tipo de evento (ex: 'mercado', 'leilao', 'proposta')
    :param jogador: nome do jogador envolvido
    :param origem: nome do time de origem
    :param destino: nome do time de destino
    """
    try:
        mov = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": float(valor),
            "descricao": descricao,
            "categoria": categoria,
            "jogador": jogador,
            "origem": origem,
            "destino": destino,
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes").insert(mov).execute()
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")



