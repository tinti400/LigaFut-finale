# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔒 Verificação de login
def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 🔒 Verificação de sessão única
def verificar_sessao():
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

# 💰 Registrar compra ou venda de jogador
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning("⚠️ Categoria inválida. Use 'compra' ou 'venda'.")
            return

        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID '{id_time}' não encontrado.")
            return

        saldo_atual = res.data[0].get("saldo")
        if saldo_atual is None:
            st.error("❌ Saldo atual não encontrado para este time.")
            return

        valor = int(valor)
        novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor
        novo_saldo = int(novo_saldo)

        update = supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        if not update.data:
            st.error("❌ Falha ao atualizar o saldo no banco de dados (sem retorno).")
            return

        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

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
        st.success(f"✅ Movimentação registrada com sucesso. Novo saldo: {formatar_valor(novo_saldo)}")

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")

# 💰 Registrar movimentação simples (amistosos, prêmios, multas)
def registrar_movimentacao_simples(id_time, valor, descricao):
    try:
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error("❌ Time não encontrado.")
            return

        saldo_atual = res.data[0].get("saldo", 0)
        valor = int(valor)
        novo_saldo = int(saldo_atual + valor)

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

        registro = {
            "id_time": id_time,
            "jogador": None,
            "tipo": "sistema",
            "categoria": "ajuste",
            "valor": abs(valor),
            "data": agora,
            "origem": None,
            "destino": None,
            "descricao": descricao
        }

        supabase.table("movimentacoes").insert(registro).execute()
        st.success(f"✅ {descricao} registrada. Novo saldo: {formatar_valor(novo_saldo)}")

    except Exception as e:
        st.error(f"Erro ao registrar movimentação simples: {e}")

# 💵 Formatar valores em R$ (ex: 1.500.000 → R$ 1.500.000)
def formatar_valor(valor):
    try:
        valor = float(valor)
        return f"R$ {valor:,.0f}".replace(",", ".")
    except:
        return "R$ 0"
