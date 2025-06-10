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
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: valor inteiro (não string com ponto)
    - origem: time de onde saiu (opcional)
    - destino: time que recebeu (opcional)
    """
    try:
        # 🕒 Timestamp atual
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🧮 Garante que o valor seja inteiro
        valor_int = int(round(float(valor)))

        # 📦 Dados da movimentação
        movimentacao = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo.lower(),
            "categoria": categoria.lower(),
            "valor": valor_int,
            "data": data,
            "origem": origem,
            "destino": destino
        }

        # 🚀 Envia para Supabase
        supabase.table("movimentacoes").insert(movimentacao).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

