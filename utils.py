# utils.py

import streamlit as st
from datetime import datetime
import pytz

# 🔐 Conexão com Supabase (evita duplicar isso se já estiver fora da função)
from supabase import create_client
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras e atualiza saldo do time.

    - tipo: Ex: "transferência", "leilao", "mercado", "proposta"
    - categoria: "compra" ou "venda"
    - valor: sempre positivo
    """

    try:
        categoria = categoria.lower().strip()

        if categoria not in ["compra", "venda"]:
            st.warning("Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID {id_time} não encontrado.")
            return

        saldo_atual = res.data[0]["saldo"]

        # Calcular novo saldo
        if categoria == "compra":
            novo_saldo = saldo_atual - valor
        else:  # venda
            novo_saldo = saldo_atual + valor

        # Atualizar saldo
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Data e hora no fuso de Brasília
        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

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
