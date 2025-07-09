# utils.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📍 Timezone de Brasília
TZ_BR = ZoneInfo("America/Sao_Paulo")

# ✅ Verifica sessão ativa
def verificar_sessao():
    campos_obrigatorios = ["usuario_id", "id_time", "nome_time"]
    faltando = [campo for campo in campos_obrigatorios if campo not in st.session_state]
    if faltando:
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.stop()

# 💰 Registrar movimentação financeira (com BID automático)
def registrar_movimentacao(id_time, tipo, valor, descricao, jogador=None, categoria=None, origem=None, destino=None):
    try:
        agora = datetime.now(TZ_BR)

        # 🔎 Verificação de duplicidade (somente para a tabela de movimentações financeiras)
        consulta = supabase.table("movimentacoes_financeiras")\
            .select("*")\
            .eq("id_time", id_time)\
            .eq("tipo", tipo)\
            .eq("valor", valor)\
            .eq("descricao", descricao)\
            .order("data", desc=True)\
            .limit(1)\
            .execute()

        if consulta.data:
            ultima = consulta.data[0]
            data_mov = ultima.get("data")
            if data_mov:
                mov_time = datetime.fromisoformat(data_mov)
                if mov_time.tzinfo is None:
                    mov_time = mov_time.replace(tzinfo=TZ_BR)
                if (agora - mov_time).total_seconds() < 10:
                    return  # Já existe, evita duplicar

        # 💾 Registro principal
        nova = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": valor,
            "descricao": descricao,
            "data": agora.isoformat(),
            "categoria": categoria or None,
            "jogador": jogador or None
        }
        supabase.table("movimentacoes_financeiras").insert(nova).execute()

        # 📝 Também registrar no BID
        registrar_bid(
            id_time=id_time,
            tipo="compra" if tipo == "saida" else "venda",
            categoria=categoria,
            jogador=jogador,
            valor=valor,
            origem=origem or "",
            destino=destino or ""
        )

    except Exception as e:
        st.error(f"Erro ao registrar movimentação financeira: {e}")

# 📈 Registrar movimentação pública no BID (tabela 'movimentacoes')
def registrar_bid(id_time, tipo, categoria, jogador, valor, origem="", destino=""):
    try:
        if not all([id_time, tipo, categoria, jogador]) or valor is None:
            st.error("❌ Dados obrigatórios ausentes para registrar no BID.")
            return False

        registro = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": str(tipo),
            "categoria": str(categoria),
            "jogador": str(jogador),
            "valor": int(valor),
            "data": datetime.now(TZ_BR).isoformat(),
            "origem": origem or "",
            "destino": destino or ""
        }

        supabase.table("movimentacoes").insert(registro).execute()
        return True

    except Exception as e:
        st.error(f"❌ Erro ao registrar no BID: {e}")
        return False
