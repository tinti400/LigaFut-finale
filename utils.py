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
    Registra movimentações financeiras no Supabase.
    
    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: Valor POSITIVO
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        # Garantir formato consistente
        categoria = categoria.lower().strip()
        tipo = tipo.lower().strip()

        if not id_time or not jogador or not tipo or not categoria:
            raise ValueError("Dados obrigatórios ausentes para registrar movimentação.")

        # Data e hora com fuso horário de Brasília
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia)

        # Monta objeto da movimentação
        movimentacao = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data_hora": agora.isoformat()
        }

        # Insere no banco
        supabase.table("movimentacoes").insert(movimentacao).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")


