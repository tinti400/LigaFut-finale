# utils.py

import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client

# 🔐 Conexão com Supabase (caso ainda não esteja feita fora deste arquivo)
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão única do usuário
def verificar_sessao():
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

    res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
    if res.data and res.data[0]["session_id"] != st.session_state["session_id"]:
        st.error("⚠️ Sua sessão foi encerrada em outro dispositivo.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.stop()

# 📒 Registra movimentações financeiras no BID (sem alterar saldo)
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    """
    Apenas registra no BID, sem atualizar saldo (valor já deve ter sido alterado antes no código).
    
    Parâmetros:
    - id_time: ID do time
    - jogador: Nome do jogador
    - tipo: Ex: 'leilao', 'mercado', 'proposta'
    - categoria: 'compra' ou 'venda'
    - valor: Valor positivo
    - origem: time de onde o jogador veio (opcional)
    - destino: time para onde o jogador foi (opcional)
    """
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.error("Categoria inválida ao registrar movimentação.")
            return

        if valor <= 0:
            st.warning("Valor da movimentação deve ser positivo.")
            return

        # Horário com fuso horário de Brasília
        fuso_brasilia = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M:%S")

        dados = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }

        supabase.table("movimentacoes").insert(dados).execute()

    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")



