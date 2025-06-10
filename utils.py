# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🌎 Timezone Brasil
fuso_brasilia = pytz.timezone("America/Sao_Paulo")


def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra uma movimentação financeira e atualiza o saldo do time.

    Parâmetros:
    - id_time (str): ID do time
    - jogador (str): Nome do jogador envolvido
    - tipo (str): Tipo da movimentação (leilao, mercado, proposta, etc)
    - categoria (str): 'compra' ou 'venda'
    - valor (float): Valor positivo da movimentação
    - origem (str): Nome do time de origem (opcional)
    - destino (str): Nome do time de destino (opcional)
    """

    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        # ✅ Ajusta valor
        if categoria == "compra":
            valor_final = -abs(valor)
        elif categoria == "venda":
            valor_final = abs(valor)
        else:
            raise ValueError("Categoria inválida. Use 'compra' ou 'venda'.")

        # 🔄 Atualiza saldo
        saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        saldo_atual = saldo_res.data[0]["saldo"] if saldo_res.data else 0
        novo_saldo = saldo_atual + valor_final

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # 📝 Registrar movimentação
        agora = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor_final,
            "data": agora,
            "origem": origem,
            "destino": destino
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")


def verificar_sessao():
    """
    Verifica se a sessão atual é válida e ainda ativa.
    Encerra automaticamente se a sessão foi invalidada no banco.
    """
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

    res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
    if res.data and res.data[0]["session_id"] != st.session_state["session_id"]:
        st.error("⚠️ Sua sessão foi encerrada em outro dispositivo.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.stop()


