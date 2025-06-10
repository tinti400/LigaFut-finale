import streamlit as st
from datetime import datetime
from supabase import create_client
import pytz

# Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Função para registrar movimentações no Firestore (sem atualizar saldo)
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        # Data atual em UTC-3
        fuso = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso).strftime("%Y-%m-%d %H:%M:%S")

        # Inserir no histórico (sem alterar saldo)
        supabase.table("historico_financeiro").insert({
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

# Função para validar sessão ativa
def verificar_sessao(usuario_id, session_id):
    try:
        res = supabase.table("usuarios").select("session_id").eq("id", usuario_id).execute()
        if res.data and res.data[0]["session_id"] != session_id:
            return False
        return True
    except:
        return False



