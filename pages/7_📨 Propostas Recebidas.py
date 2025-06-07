# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas - LigaFut", layout="wide")

# Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown("<h1 style='text-align: center;'>📨 Propostas Recebidas</h1><hr>", unsafe_allow_html=True)

# Buscar propostas recebidas
res = supabase.table("propostas").select("*").eq("id_time_alvo", id_time).neq("status", "recusada").execute()
propostas = res.data

if not propostas:
    st.info("Você não possui propostas recebidas no momento.")
    st.stop()

for proposta in propostas:
    with st.container():
        st.markdown("---")
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.subheader(f"🎯 Jogador alvo: {proposta['jogador_alvo']}")
            st.write(f"Posição: {proposta['posicao_alvo']} | Overall: {proposta['overall_alvo']}")
            st.write(f"Time comprador: {proposta['nome_time_proposta']}")
            st.write(f"💰 Valor oferecido: R${proposta['valor']}")

            if proposta["jogadores_oferecidos"]:
                st.markdown("🧩 **Jogadores Oferecidos:**")
                for j in proposta["jogadores_oferecidos"]:
                    st.write(f"- {j['nome']} ({j['posicao']}) | Overall: {j['overall']} | 💰 R$ {j['valor']:,}")

        with col2:
            if st.button(f"✅ Aceitar proposta ({proposta['id']})", key=f"aceitar_{proposta['id']}"):
                # Transferir jogador alvo
                jogador_data = {
                    "nome": proposta["jogador_alvo"],
                    "posicao": proposta["posicao_alvo"],
                    "overall": proposta["overall_alvo"],
                    "valor": proposta["valor"],
                }

                # Remover do time atual
                supabase.table("elenco").delete().match({
                    "id_time": id_time,
                    "nome": proposta["jogador_alvo"],
                    "posicao": proposta["posicao_alvo"],
                    "overall": proposta["overall_alvo"]
                }).execute()

                # Inserir no novo time
                supabase.table("elenco").insert({
                    "id_time": proposta["id_time_proposta"],
                    **jogador_data
                }).execute()

                # Registrar movimentação no BID
                registrar_movimentacao(
                    tipo="Venda entre clubes",
                    time_origem=nome_time,
                    time_destino=proposta["nome_time_proposta"],
                    jogador=proposta["jogador_alvo"],
                    valor=proposta["valor"]
                )

                # Transferir jogadores oferecidos
                if proposta["jogadores_oferecidos"]:
                    for j in proposta["jogadores_oferecidos"]:
                        supabase.table("elenco").delete().match({
                            "id_time": proposta["id_time_proposta"],
                            "nome": j["nome"],
                            "posicao": j["posicao"],
                            "overall": j["overall"]
                        }).execute()

                        supabase.table("elenco").insert({
                            "id_time": id_time,
                            **j
                        }).execute()

                        # Registrar cada jogador oferecido
                        registrar_movimentacao(
                            tipo="Troca entre clubes",
                            time_origem=proposta["nome_time_proposta"],
                            time_destino=nome_time,
                            jogador=j["nome"],
                            valor=j["valor"]
                        )

                # Atualiza status
                supabase.table("propostas").update({
                    "status": "aceita"
                }).eq("id", proposta["id"]).execute()

                st.success("✅ Proposta aceita com sucesso!")
                st.experimental_rerun()

        with col3:
            if st.button(f"❌ Recusar proposta ({proposta['id']})", key=f"recusar_{proposta['id']}"):
                supabase.table("propostas").update({
                    "status": "recusada"
                }).eq("id", proposta["id"]).execute()
                st.warning("Proposta recusada.")
                st.experimental_rerun()
