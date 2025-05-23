# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import json

st.set_page_config(page_title="📨 Propostas Recebidas - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_logado = st.session_state["id_time"]
nome_time_logado = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# 🔍 Buscar apenas propostas pendentes
res = supabase.table("negociacoes").select("*").eq("id_time_destino", id_time_logado).eq("status", "pendente").execute()
propostas = res.data or []

if not propostas:
    st.info("Nenhuma proposta pendente no momento.")
    st.stop()

for proposta in propostas:
    st.markdown("---")
    jogador_nome = proposta.get("jogador_desejado", "Desconhecido")
    jogador_id = proposta.get("id_jogador")
    tipo = proposta.get("tipo_negociacao", "N/A")
    valor = proposta.get("valor_oferecido", 0)
    time_origem_id = proposta.get("id_time_origem")

    # 🔄 Conversão segura do campo jogador_oferecido
    jogadores_oferecidos_ids = []
    try:
        brutos = proposta.get("jogador_oferecido", [])
        if isinstance(brutos, str):
            jogadores_oferecidos_ids = json.loads(brutos)
        elif isinstance(brutos, list):
            jogadores_oferecidos_ids = brutos
    except Exception:
        jogadores_oferecidos_ids = []

    # Buscar nome do time de origem
    nome_time_origem = "Desconhecido"
    res_time = supabase.table("times").select("nome").eq("id", time_origem_id).execute()
    if res_time.data:
        nome_time_origem = res_time.data[0]["nome"]

    col1, col2 = st.columns([4, 2])
    with col1:
        st.markdown(f"**👤 Jogador Desejado:** {jogador_nome}")
        st.markdown(f"**🏷️ Tipo de Negociação:** {tipo}")
        st.markdown(f"**💰 Valor Oferecido:** R$ {valor:,.0f}")
        st.markdown(f"**📤 Time Proponente:** {nome_time_origem}")

        if jogadores_oferecidos_ids:
            st.markdown("**👥 Jogadores Oferecidos:**")
            nomes = []
            for id_j in jogadores_oferecidos_ids:
                if isinstance(id_j, str) and id_j.strip() != "":
                    try:
                        res_jog = supabase.table("elenco").select("nome").eq("id", id_j).execute()
                        if res_jog.data:
                            nomes.append(res_jog.data[0]["nome"])
                        else:
                            nomes.append(f"(Jogador não encontrado: {id_j})")
                    except Exception:
                        nomes.append(f"(Erro ao buscar jogador: {id_j})")
                else:
                    nomes.append(f"(ID inválido: {id_j})")
            for nome in nomes:
                st.markdown(f"- {nome}")

        st.markdown(f"**📝 Status:** `PENDENTE`")

    with col2:
        if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
            try:
                # 1️⃣ Transfere o jogador desejado para o time proponente
                if tipo == "Somente Dinheiro":
                    supabase.table("elenco").update({
                        "id_time": time_origem_id,
                        "valor": valor
                    }).eq("id", jogador_id).execute()
                else:
                    # Mantém valor original
                    supabase.table("elenco").update({
                        "id_time": time_origem_id
                    }).eq("id", jogador_id).execute()

                # 2️⃣ Transfere os jogadores oferecidos (se houver) para o time que recebeu a proposta
                for id_j in jogadores_oferecidos_ids:
                    if isinstance(id_j, str) and id_j.strip() != "":
                        supabase.table("elenco").update({
                            "id_time": id_time_logado
                        }).eq("id", id_j).execute()

                # 3️⃣ Atualiza o status da proposta
                supabase.table("negociacoes").update({
                    "status": "aceita",
                    "valor_aceito": valor
                }).eq("id", proposta["id"]).execute()

                st.success("✅ Proposta aceita com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao aceitar a proposta: {e}")

        if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
            try:
                supabase.table("negociacoes").update({
                    "status": "recusada"
                }).eq("id", proposta["id"]).execute()
                st.warning("🚫 Proposta recusada.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao recusar a proposta: {e}")
