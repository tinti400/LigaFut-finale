# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def verificar_login():
    """
    Verifica se o usuário está logado. Caso não esteja, bloqueia o acesso à página.
    """
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda' (case-insensitive)
    - valor: Valor positivo
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning("⚠️ Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # Verifica o saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID '{id_time}' não encontrado.")
            return

        saldo_atual = res.data[0]["saldo"]

        # Calcula o novo saldo
        novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor

        # Atualiza o saldo no banco
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Data atual no fuso de Brasília
        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

        # Monta registro da movimentação
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }

        # Salva no Supabase
        supabase.table("movimentacoes").insert(registro).execute()

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")
