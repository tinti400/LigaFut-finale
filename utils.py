# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# 🔌 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verificação de login
def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()
    if "id_time" not in st.session_state or "nome_time" not in st.session_state:
        st.warning("Informações do time não encontradas na sessão.")
        st.stop()

# 💰 Registrar movimentação financeira com atualização de saldo
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor):
    """
    Registra movimentações financeiras e atualiza saldo do time.

    - tipo: Ex: "Transferência", "Leilão", "Mercado"
    - categoria: "Compra" ou "Venda"
    - valor: sempre positivo

    A função debita para 'compra' e credita para 'venda'.
    """
    try:
        # Buscar saldo atual do time
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID {id_time} não encontrado.")
            return

        saldo_atual = res.data[0]["saldo"]

        # Calcula novo saldo
        if categoria.lower() == "compra":
            novo_saldo = saldo_atual - valor
        elif categoria.lower() == "venda":
            novo_saldo = saldo_atual + valor
        else:
            st.warning("Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # Atualiza saldo no banco
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Pega data e hora no fuso de Brasília
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia).isoformat()

        # Registra movimentação
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora
        }
        supabase.table("movimentacoes").insert(registro).execute()

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")
