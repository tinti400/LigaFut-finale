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

# 💰 Registrar movimentação financeira (controle de saldo)
def registrar_movimentacao(id_time, tipo, valor, descricao):
    """
    Registra uma movimentação financeira na tabela 'movimentacoes_financeiras'.

    :param id_time: ID do time responsável
    :param tipo: 'entrada' ou 'saida'
    :param valor: valor numérico da movimentação
    :param descricao: descrição da movimentação
    """
    try:
        nova = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo or "saida",
            "valor": valor or 0,
            "descricao": descricao or "Sem descrição",
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes_financeiras").insert(nova).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar movimentação financeira: {e}")
        return False

# 📈 Registrar movimentação pública no BID
def registrar_bid(id_time, tipo, categoria, jogador, valor, origem="", destino=""):
    """
    Registra uma movimentação para exibição pública no BID (tabela 'movimentacoes').

    :param id_time: ID do time responsável
    :param tipo: 'compra' ou 'venda'
    :param categoria: 'mercado', 'leilao', 'proposta', etc.
    :param jogador: nome do jogador
    :param valor: valor da movimentação (positivo para entrada, negativo para saída)
    :param origem: nome do time de origem (opcional)
    :param destino: nome do time de destino (opcional)
    """
    try:
        registro = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo or "compra",
            "categoria": categoria or "mercado",
            "jogador": jogador or "Desconhecido",
            "valor": valor or 0,
            "data": datetime.now().isoformat(),
            "origem": origem or "",
            "destino": destino or ""
        }
        supabase.table("movimentacoes").insert(registro).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")
        return False

