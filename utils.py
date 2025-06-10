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
    Registra movimentações financeiras no Firestore e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda' (case-insensitive)
    - valor: Valor positivo
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning(f"⚠️ Categoria inválida ao registrar movimentação: {categoria}")
            return

        if tipo not in ["leilao", "mercado", "proposta"]:
            st.warning(f"⚠️ Tipo inválido ao registrar movimentação: {tipo}")
            return

        data_hora = datetime.now().isoformat()

        # 🟢 Registra no BID (boletim informativo diário)
        supabase.table("bid").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data_hora": data_hora
        }).execute()

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação no BID: {e}")




