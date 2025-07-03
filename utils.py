# utils.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão ativa
def verificar_sessao():
    campos_obrigatorios = ["usuario_id", "id_time", "nome_time"]
    faltando = [campo for campo in campos_obrigatorios if campo not in st.session_state]
    if faltando:
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.stop()

# 💰 Registrar movimentação financeira com verificação de duplicidade
def registrar_movimentacao(id_time, tipo, valor, descricao, jogador=None, categoria=None, origem=None, destino=None):
    try:
        # ⚠️ Verifica se já existe movimentação idêntica nos últimos 10 segundos
        dez_segundos_atras = datetime.now().isoformat(timespec='seconds')
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
            ultima_data = datetime.fromisoformat(ultima["data"])
            if (datetime.now() - ultima_data).seconds < 10:
                # ⛔ Já existe uma movimentação igual recente — evita duplicar
                return

        nova = {
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "valor": valor,
            "descricao": descricao,
            "data": datetime.now().isoformat()
        }
        supabase.table("movimentacoes_financeiras").insert(nova).execute()

        # Se for venda ou compra, registra também no BID
        # 🔒 Evita registrar entrada no BID se for leilão (apenas o vencedor aparece)
        if tipo in ["entrada", "saida"] and jogador and categoria:
            if categoria == "leilao" and tipo != "saida":
                return  # só registra no BID se for saída no leilão (compra)

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

# 📈 Registrar movimentação pública no BID
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
            "data": datetime.now().isoformat(),
            "origem": origem or "",
            "destino": destino or ""
        }

        supabase.table("movimentacoes").insert(registro).execute()
        return True

    except Exception as e:
        st.error(f"❌ Erro ao registrar no BID: {e}")
        return False

