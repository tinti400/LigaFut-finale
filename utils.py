# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime

def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()
    if "id_time" not in st.session_state or "nome_time" not in st.session_state:
        st.warning("Informações do time não encontradas na sessão.")
        st.stop()

def registrar_movimentacao(supabase, id_time, jogador, categoria, tipo, valor):
    """
    Registra uma movimentação financeira na tabela 'movimentacoes' do Supabase.

    Args:
        supabase: conexão ativa com o Supabase.
        id_time: ID do time (UUID).
        jogador: nome do jogador envolvido na transação.
        categoria: categoria da transação (ex: "Leilão", "Transferência").
        tipo: tipo da transação (ex: "Compra", "Venda").
        valor: valor em R$ (float ou int).
    """
    try:
        movimentacao = {
            "id_time": id_time,
            "jogador": jogador,
            "categoria": categoria,
            "tipo": tipo,
            "valor": valor,
            "data": datetime.utcnow().isoformat()
        }
        supabase.table("movimentacoes").insert(movimentacao).execute()
    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação financeira: {e}")
