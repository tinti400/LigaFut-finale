# utils.py

import os
import streamlit as st
from supabase import create_client
from datetime import datetime
import pytz

# 🔐 Conexão com Supabase
url = os.getenv("SUPABASE_URL") or st.secrets["supabase"]["url"]
key = os.getenv("SUPABASE_KEY") or st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 💰 Registrar movimentação financeira com atualização de saldo
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras e atualiza saldo do time.

    - tipo: Ex: "Transferência", "Leilão", "Mercado"
    - categoria: "compra" ou "venda"
    - valor: sempre positivo
    - origem: time de onde veio o jogador (opcional)
    - destino: time para onde foi o jogador (opcional)
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

        # Atualiza saldo do time
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Data e hora no fuso de Brasília
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia).isoformat()

        # Registro da movimentação
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "ti

