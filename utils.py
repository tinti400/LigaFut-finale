# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: Valor positivo (R$)
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        categoria = categoria.lower().strip()
        tipo = tipo.lower().strip()

        if categoria not in ["compra", "venda"]:
            raise ValueError("Categoria deve ser 'compra' ou 'venda'.")

        # 🔄 Buscar saldo atual do time
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            raise Exception("Time não encontrado.")
        saldo_atual = res.data[0]["saldo"]

        # ➕ ou ➖ saldo
        if categoria == "compra":
            novo_saldo = saldo_atual - valor
        elif categoria == "venda":
            novo_saldo = saldo_atual + valor

        # 📝 Atualizar saldo
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # 📦 Registrar a movimentação
        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")
