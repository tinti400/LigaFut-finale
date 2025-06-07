
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

verificar_login()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title(f"📨 Propostas Recebidas - {nome_time}")

# Carregar propostas recebidas
res = supabase.table("propostas").select("*").eq("destino_id", id_time).execute()
propostas = res.data if res.data else []

if not propostas:
    st.info("Você não recebeu nenhuma proposta até o momento.")
else:
    for proposta in propostas:
        with st.container():
            st.subheader(f"{proposta['jogador_nome']} ({proposta['jogador_posicao']})")
            col1, col2 = st.columns(2)
            col1.markdown(f"**Overall:** {proposta['jogador_overall']}")
            col1.markdown(f"**Valor Oferecido:** R$ {proposta['valor']:,}")
            col2.markdown(f"**Proposta de:** {proposta['origem_nome']}")
            col2.markdown(f"**Status:** {proposta['status']}")

            if proposta["status"] == "pendente":
                col_aceitar, col_recusar = st.columns(2)
                if col_aceitar.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                    try:
                        valor = proposta["valor"]
                        jogador_id = proposta["jogador_id"]
                        origem_id = proposta["origem_id"]
                        destino_id = proposta["destino_id"]

                        # Transferir jogador
                        jogador = {
                            "nome": proposta["jogador_nome"],
                            "posicao": proposta["jogador_posicao"],
                            "overall": proposta["jogador_overall"],
                            "valor": valor
                        }

                        # Remover do elenco do time atual
                        supabase.table("elenco").delete().eq("id", jogador_id).execute()

                        # Adicionar ao novo time
                        supabase.table("elenco").insert({**jogador, "time_id": origem_id}).execute()

                        # Registrar movimentações
                        registrar_movimentacao(origem_id, proposta["jogador_nome"], "Transferência", "Compra", -valor)
                        registrar_movimentacao(destino_id, proposta["jogador_nome"], "Transferência", "Venda", valor)

                        # Atualizar status da proposta
                        supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                        st.success(f"✅ Proposta aceita e jogador transferido para {proposta['origem_nome']}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao aceitar a proposta: {e}")

                if col_recusar.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                    try:
                        supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                        st.warning("Proposta recusada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao recusar a proposta: {e}")
