# utils.py

import streamlit as st
from datetime import datetime
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra uma movimentação na tabela 'movimentacoes'.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Ex: 'mercado', 'leilao', 'proposta'
    - categoria: 'compra' ou 'venda'
    - valor: número (int ou float)
    - origem: nome do time de origem (opcional)
    - destino: nome do time de destino (opcional)
    """
    try:
        tipo = tipo.strip().lower()
        categoria = categoria.strip().lower()
        valor_int = int(float(valor))  # garante bigint

        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor_int,
            "origem": origem,
            "destino": destino,
            "data_hora": datetime.now().isoformat()  # obrigatório pro BID
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")




