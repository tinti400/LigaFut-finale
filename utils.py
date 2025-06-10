# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None, ajustar_saldo=True):
    """
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo da movimentação (ex: mercado, leilão)
    - categoria: 'compra' ou 'venda'
    - valor: valor positivo
    - origem: time de origem (opcional)
    - destino: time de destino (opcional)
    - ajustar_saldo: se True, ajusta o saldo automaticamente
    """

    try:
        categoria = categoria.lower().strip()
        tipo = tipo.lower().strip()

        if categoria not in ["compra", "venda"]:
            raise ValueError("Categoria deve ser 'compra' ou 'venda'.")

        # Atualiza saldo se necessário
        if ajustar_saldo:
            saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
            saldo_atual = saldo_res.data[0]["saldo"] if saldo_res.data else 0

            novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Registra movimentação
        data_hora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": data_hora,
            "origem": origem,
            "destino": destino
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")


