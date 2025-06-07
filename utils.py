from supabase import create_client
from datetime import datetime
import streamlit as st

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor):
    """
    Registra a movimentação financeira e atualiza o saldo do time.

    Args:
        id_time (str): ID do time.
        jogador (str): Nome do jogador.
        tipo (str): Tipo de movimentação (Ex: "Transferência", "Leilão").
        categoria (str): Categoria da movimentação (Ex: "Compra", "Venda").
        valor (float): Valor da transação (positivo para entrada, negativo para saída).
    """

    # 🔢 Atualiza o saldo
    try:
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if res.data:
            saldo_atual = res.data[0]["saldo"]
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        else:
            st.warning(f"⚠️ Time com ID {id_time} não encontrado para atualizar saldo.")
    except Exception as e:
        st.error(f"Erro ao atualizar saldo do time: {e}")
        return

    # 🧾 Registra a movimentação
    try:
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes").insert(registro).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")
