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
    - valor: Valor positivo da operação
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        if not id_time or not jogador or not tipo or not categoria or valor <= 0:
            st.error("❌ Dados inválidos para registrar movimentação.")
            return

        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.error("❌ Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # 📊 Buscar saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error("❌ Time não encontrado ao buscar saldo.")
            return

        saldo_atual = res.data[0].get("saldo")

        if saldo_atual is None:
            st.error("❌ Saldo atual não encontrado para este time.")
            return

        st.write(f"[DEBUG] Saldo antes: {saldo_atual}, valor: {valor}, tipo: {tipo}, categoria: {categoria}")

        # 📅 Horário de registro (fuso -3)
        data_atual = datetime.now(pytz.timezone("America/Sao_Paulo"))

        # 📉 Atualiza o saldo
        novo_saldo = saldo_atual + valor if categoria == "venda" else saldo_atual - valor

        update = supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        if update.status_code >= 400:
            st.error("❌ Falha ao atualizar o saldo no banco de dados.")
            return

        # 📄 Registrar a movimentação
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "created_at": data_atual.isoformat()
        }).execute()

        st.success(f"✅ Movimentação registrada com sucesso. Novo saldo: R$ {novo_saldo:,.0f}".replace(",", "."))

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")
