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
    - tipo: Tipo da movimentação (ex: 'mercado', 'leilão', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: Valor positivo (em reais)
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        # 🔁 Converte para lowercase e garante valor inteiro
        tipo = tipo.strip().lower()
        categoria = categoria.strip().lower()
        valor = int(valor)

        # 📅 Data com fuso horário
        tz = pytz.timezone("America/Sao_Paulo")
        data_movimentacao = datetime.now(tz).isoformat()

        # 📦 Registro da movimentação
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data": data_movimentacao
        }

        # 📝 Insere no Supabase
        supabase.table("movimentacoes").insert(registro).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

