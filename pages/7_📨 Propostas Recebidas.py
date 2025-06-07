# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

verificar_login()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown("<h1 style='text-align: center;'>📨 Propostas Recebidas</h1><hr>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center;'>Time: {nome_time}</h4>", unsafe_allow_html=True)

# 🔍 Filtro por status
status_filtro = st.selectbox("🔎 Filtrar por status", ["Todas", "Pendentes", "Aceitas", "Recusadas"])

query = supabase.table("propostas").select("*").eq("destino_id", id_time)
if status_filtro != "Todas":
    query = query.eq("status", status_filtro.lower())
res = query.execute()
propostas = res.data if res.data else []

if not propostas:
    st.info("📭 Nenhuma proposta encontrada para este filtro.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown(f"### 🎯 {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
            st.markdown("---")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Overall", proposta["jogador_overall"])
            col2.metric("Valor Oferecido", f"R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
            col3.metric("Time Proponente", proposta["nome_time_origem"])
            col4.metric("Status", proposta["status"].capitalize())

            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.markdown("**🔁 Jogadores Oferecidos em Troca:**")
                for j in jogadores_oferecidos:
                    st.markdown(f"- {j['nome']} (OVR {j['overall']}) - {j['posicao']}")

            if proposta["status"] == "pendente":
                col_aceitar, col_recusar = st.columns([1, 1])
                with col_aceitar:
                    if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                        try:
                            valor = proposta["valor_oferecido"]
                            id_time_origem = proposta["id_time_origem"]
                            id_time_destino = proposta["id_time_alvo"]
                            jogador_nome = proposta["jogador_nome"]

                            # Remover jogador do time vendedor
                            supabase.table("elenco").delete().eq("id_time", id_time_destino).eq("nome", jogador_nome).execute()

                            # Adicionar ao comprador com novo valor
                            novo_jogador = {
                                "nome": jogador_nome,
                                "posicao": proposta["jogador_posicao"],
                                "overall": proposta["jogador_overall"],
                                "valor": valor,
                                "id_time": id_time_origem
                            }
                            supabase.table("elenco").insert(novo_jogador).execute()

                            # Troca de jogadores (se houver)
                            for jogador in jogadores_oferecidos:
                                supabase.table("elenco").delete().eq("id_time", id_time_origem).eq("nome", jogador["nome"]).execute()
                                jogador_trocado = {
                                    "nome": jogador["nome"],
                                    "posicao": jogador["posicao"],
                                    "overall": jogador["overall"],
                                    "valor": jogador["valor"],
                                    "id_time": id_time_destino
                                }
                                supabase.table("elenco").insert(jogador_trocado).execute()

                            # Registrar movimentações financeiras
                            if valor > 0:
                                registrar_movimentacao(id_time_origem, jogador_nome, "Transferência", "Compra", valor)
                                registrar_movimentacao(id_time_destino, jogador_nome, "Transferência", "Venda", valor)

                            supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()
                            st.success(f"✅ Proposta aceita! {jogador_nome} foi transferido para {proposta['nome_time_origem']}.")
                            st.experimental_rerun()

                        except Exception as e:
                            st.error(f"Erro ao aceitar a proposta: {e}")

                with col_recusar:
                    if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                        try:
                            supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                            st.warning("❌ Proposta recusada.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao recusar a proposta: {e}")
