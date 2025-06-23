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

# 💰 Registrar movimentação financeira e opcionalmente no BID
def registrar_movimentacao(id_time, tipo, valor, descricao, jogador=None, categoria=None, origem=None, destino=None):
    """
    Registra uma movimentação financeira e, se aplicável, também registra no BID.

    :param id_time: ID do time responsável
    :param tipo: 'entrada' ou 'saida'
    :param valor: valor numérico da movimentação
    :param descricao: descrição da movimentação
    :param jogador: nome do jogador (opcional)
    :param categoria: tipo da negociação: mercado, leilao, proposta (opcional)
    :param origem: nome do time de origem (opcional)
    :param destino: nome do time de destino (opcional)
    """
    try:
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

    # Se for venda ou compra, registra no BID
    if tipo in ["entrada", "saida"] and jogador and categoria:
        registrar_bid(
            id_time=id_time,
            tipo="compra" if tipo == "saida" else "venda",
            categoria=categoria,
            jogador=jogador,
            valor=valor,
            origem=origem or "",
            destino=destino or ""
        )

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

        # 🐞 DEBUG OPCIONAL
        # st.markdown("### 🐞 DEBUG BID:")
        # st.json(registro)

        supabase.table("movimentacoes").insert(registro).execute()
        return True

    except Exception as e:
        st.error(f"❌ Erro ao registrar no BID: {e}")
        return False


