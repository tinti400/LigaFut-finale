# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

def verificar_login():
    """
    Verifica se o usuário está logado. Caso não esteja, bloqueia o acesso à página.
    """
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

def verificar_sessao():
    """
    Verifica se a sessão do usuário é válida (sessão única).
    Se outro login tiver ocorrido, desconecta automaticamente.
    """
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado.")
        st.stop()

    try:
        res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
        if res.data and res.data[0]["session_id"] != st.session_state["session_id"]:
            st.error("⚠️ Sua sessão foi encerrada em outro dispositivo.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.stop()
    except Exception as e:
        st.error(f"Erro ao verificar sessão: {e}")
        st.stop()

def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Registra movimentações financeiras no Supabase e atualiza saldo do time.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Tipo de movimentação (ex: 'leilao', 'mercado', 'proposta')
    - categoria: 'compra' ou 'venda'
    - valor: Valor positivo
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning("⚠️ Categoria inválida. Use 'compra' ou 'venda'.")
            return

        # Verifica o saldo atual
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID '{id_time}' não encontrado.")
            return

        saldo_atual = res.data[0].get("saldo")
        if saldo_atual is None:
            st.error("❌ Saldo atual não encontrado para este time.")
            return

        st.write(f"[DEBUG] Saldo antes: {saldo_atual}, valor: {valor}, tipo: {tipo}, categoria: {categoria}")

        # Calcula o novo saldo
        novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor

        # Atualiza o saldo no banco
        update = supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        if not update.data:
            st.error("❌ Falha ao atualizar o saldo no banco de dados (sem retorno).")
            return

        # Data atual no fuso de Brasília
        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

        # Monta registro da movimentação
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

        # Salva no Supabase
        supabase.table("movimentacoes").insert(registro).execute()
        st.success(f"✅ Movimentação registrada com sucesso. Novo saldo: R$ {novo_saldo:,.0f}".replace(",", "."))

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")
