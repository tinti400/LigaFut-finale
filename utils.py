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
    Registra uma movimentação na tabela 'movimentacoes' do Supabase.

    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Ex: 'mercado', 'leilao', 'proposta'
    - categoria: 'compra' ou 'venda'
    - valor: número inteiro (sem ponto ou vírgula)
    - origem: nome do time de origem (opcional)
    - destino: nome do time de destino (opcional)
    """
    try:
        tipo = tipo.lower().strip()
        categoria = categoria.lower().strip()

        valor_int = int(float(valor))  # Garante tipo correto para bigint/numeric

        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor_int,
            "origem": origem,
            "destino": destino,
            "data_hora": datetime.now().isoformat()
        }).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

def verificar_sessao():
    """
    Garante que a sessão do usuário está ativa e válida.
    Encerra a execução se não estiver logado ou se a sessão foi encerrada em outro dispositivo.
    """
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
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




