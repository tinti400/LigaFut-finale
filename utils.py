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
    Registra movimentações financeiras e atualiza o saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo da transação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: Valor POSITIVO
    - origem: (opcional) time de origem
    - destino: (opcional) time de destino
    """

    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            raise ValueError("Categoria deve ser 'compra' ou 'venda'")

        # 🔄 Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).single().execute()
        saldo_atual = res.data.get("saldo", 0)

        # 🧮 Calcular novo saldo
        if categoria == "compra":
            novo_saldo = saldo_atual - valor
        elif categoria == "venda":
            novo_saldo = saldo_atual + valor

        # ⛔ Limitar saldo máximo
        saldo_maximo = 5_000_000_000
        if novo_saldo > saldo_maximo:
            novo_saldo = saldo_maximo

        # 💾 Atualizar saldo
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # 🕓 Timestamp Brasil
        fuso = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")

        # 📝 Registrar movimentação
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data": agora
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

