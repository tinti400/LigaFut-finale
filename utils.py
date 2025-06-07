# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz
import os

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"] if "supabase" in st.secrets else os.getenv("SUPABASE_URL")
key = st.secrets["supabase"]["key"] if "supabase" in st.secrets else os.getenv("SUPABASE_KEY")
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
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras e atualiza saldo do time.

    - tipo: Ex: "leilao", "mercado", "proposta"
    - categoria: "compra" ou "venda"
    - valor: sempre positivo
    - origem: time de onde veio o jogador (opcional)
    - destino: time para onde foi o jogador (opcional)
    """
    try:
        # Padroniza os campos
        tipo = tipo.strip().lower()
        categoria = categoria.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning("Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID {id_time} não encontrado.")
            return

        saldo_atual = res.data[0]["saldo"]

        # Atualiza saldo
        novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Data e hora no fuso de Brasília
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia).isoformat()

        # Registro da movimentação
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

        supabase.table("movimentacoes").insert(registro).execute()

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")
