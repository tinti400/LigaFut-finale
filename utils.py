# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🌐 Timezone
tz = pytz.timezone("America/Sao_Paulo")

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo da operação (ex: leilao, mercado, proposta)
    - categoria: compra ou venda
    - valor: valor da movimentação
    - origem: time de onde veio
    - destino: time para onde vai
    """

    try:
        categoria = categoria.lower().strip()
        tipo = tipo.lower().strip()

        if categoria not in ["compra", "venda"]:
            st.warning("Categoria inválida na movimentação.")
            return

        valor = float(valor)
        if valor <= 0:
            st.warning("Valor da movimentação inválido.")
            return

        # Busca saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error("Erro ao buscar saldo do time.")
            return
        saldo_atual = res.data[0]["saldo"]

        if categoria == "venda":
            novo_saldo = saldo_atual + valor
        else:  # compra
            if saldo_atual < valor:
                st.error("❌ Saldo insuficiente para a compra.")
                return
            novo_saldo = saldo_atual - valor

        # Atualiza saldo
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        # Registra movimentação
        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "origem": origem,
            "destino": destino,
            "data": datetime.now(tz).isoformat()
        }

        supabase.table("movimentacoes").insert(registro).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")


def verificar_sessao():
    """
    Verifica se o usuário está com a sessão válida.
    """
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

    try:
        res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
        session_db = res.data[0]["session_id"] if res.data else None
        if session_db != st.session_state["session_id"]:
            st.error("⚠️ Sessão encerrada em outro dispositivo.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.stop()
    except Exception as e:
        st.error(f"Erro ao verificar sessão: {e}")
        st.stop()

