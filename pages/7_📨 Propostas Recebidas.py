# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao
import uuid

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔄 Buscar propostas recebidas
try:
    res = supabase.table("propostas").select("*").eq("destino_id", id_time).order("created_at", desc=True).execute()
    propostas = res.data if res.data else []
except Exception as e:
    st.error(f"Erro ao buscar propostas: {e}")
    propostas = []

st.markdown(f"<h2>📨 Propostas Recebidas - {nome_time}</h2>", unsafe_allow_html=True)

if not propostas:
    st.info("Nenhuma proposta recebida ainda.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown("---")
            st.markdown(f"### {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
            st.write(f"🌍 **Nacionalidade:** {proposta.get('nacionalidade', '-')}")
            st.write(f"📌 **Posição:** {proposta['jogador_posicao']}")
            st.write(f"⭐ **Overall:** {proposta['jogador_overall']}")
            st.write(f"💰 **Valor do Jogador:** R$ {proposta['jogador_valor']:,.0f}".replace(",", "."))
            st.write(f"🏟️ **Proposta de:** {proposta['nome_time_origem']}")
            st.write(f"📦 **Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
            st.write(f"📅 **Data:** {datetime.fromisoformat(proposta['created_at']).strftime('%d/%m/%Y %H:%M')}")

            status = proposta.get("status", "pendente")
            if status == "pendente":
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                        try:
                            # 🔁 Transferir jogador para time comprador
                            jogador = {
                                "nome": proposta["jogador_nome"],
                                "posicao": proposta["jogador_posicao"],
                                "overall": proposta["jogador_overall"],
                                "valor": proposta["valor_oferecido"],
                                "imagem_url": proposta.get("imagem_url", ""),
                                "nacionalidade": proposta.get("nacionalidade", "-"),
                                "origem": proposta.get("origem", "-"),
                                "classificacao": proposta.get("classificacao", "")
                            }

                            supabase.table("elenco").insert({"id_time": proposta["id_time_origem"], **jogador}).execute()

                            # 🧹 Remover jogador do elenco original
                            supabase.table("elenco").delete().match({
                                "id_time": proposta["id_time_alvo"],
                                "nome": proposta["jogador_nome"]
                            }).execute()

                            # 💰 Atualiza saldo do time COMPRADOR (desconta)
                            res_saldo_comp = supabase.table("times").select("saldo").eq("id", proposta["id_time_origem"]).execute()
                            saldo_comp = res_saldo_comp.data[0]["saldo"] if res_saldo_comp.data else 0
                            novo_saldo_comp = saldo_comp - proposta["valor_oferecido"]
                            supabase.table("times").update({"saldo": novo_saldo_comp}).eq("id", proposta["id_time_origem"]).execute()

                            # 💰 Atualiza saldo do time VENDEDOR (recebe)
                            res_saldo_vend = supabase.table("times").select("saldo").eq("id", proposta["id_time_alvo"]).execute()
                            saldo_vend = res_saldo_vend.data[0]["saldo"] if res_saldo_vend.data else 0
                            novo_saldo_vend = saldo_vend + proposta["valor_oferecido"]
                            supabase.table("times").update({"saldo": novo_saldo_vend}).eq("id", proposta["id_time_alvo"]).execute()

                            # 🔁 Atualiza status da proposta
                            supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                            # 💾 Registrar movimentações
                            registrar_movimentacao(proposta["id_time_origem"], "saida", proposta["valor_oferecido"], f"Compra de {proposta['jogador_nome']}")
                            registrar_movimentacao(proposta["id_time_alvo"], "entrada", proposta["valor_oferecido"], f"Venda de {proposta['jogador_nome']}")

                            # 📝 Registro no BID (informativo, sem alterar saldo)
                            supabase.table("bid").insert({
                                "id": str(uuid.uuid4()),
                                "data": datetime.now().isoformat(),
                                "jogador_nome": proposta["jogador_nome"],
                                "jogador_posicao": proposta["jogador_posicao"],
                                "id_time_origem": proposta["id_time_alvo"],
                                "id_time_destino": proposta["id_time_origem"],
                                "nome_time_origem": nome_time,
                                "nome_time_destino": proposta["nome_time_origem"],
                                "valor": proposta["valor_oferecido"],
                                "tipo": "Venda",
                                "categoria": "Proposta"
                            }).execute()

                            st.success("✅ Proposta aceita com sucesso!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"Erro ao aceitar proposta: {e}")

                with col2:
                    if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                        try:
                            supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                            st.info("Proposta recusada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao recusar proposta: {e}")

            elif status == "aceita":
                st.success("✅ Proposta aceita.")
            elif status == "recusada":
                st.error("❌ Proposta recusada.")
