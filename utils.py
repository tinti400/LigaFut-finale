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
    Registra uma movimentação na tabela 'movimentacoes' do Supabase.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Ex: 'mercado', 'leilao', 'proposta'
    - categoria: 'compra' ou 'venda'
    - valor: número inteiro (sem ponto ou vírgula)
    - origem: nome do time de origem (opcional)
    - destino: nome do time de destino (opcional)
    """
    try:
        tipo = tipo.lower().strip()
        categoria = categoria.lower().strip()

        valor_int = int(float(valor))  # Garante tipo correto para bigint/numeric

        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor_int,
            "origem": origem,
            "destino": destino,
            "data_hora": datetime.now().isoformat()
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")




