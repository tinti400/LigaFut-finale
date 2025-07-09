# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao, registrar_bid

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

# 🔄 Buscar as 5 últimas propostas recebidas
try:
    res = supabase.table("propostas")\
        .select("*")\
        .eq("destino_id", id_time)\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()
    propostas = res.data if res.data else []
except Exception as e:
    st.error(f"Erro ao buscar propostas: {e}")
    propostas = []

st.markdown(f"<h2>📨 Propostas Recebidas - {nome_time}</h2>", unsafe_allow_html=True)

if not propostas:
    st.info("Nenhuma proposta recebida.")
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
            st.write(f"📦 **Valor Oferecido (dinheiro):** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
            st.write(f"📅 **Data:** {datetime.fromisoformat(proposta['created_at']).strftime('%d/%m/%Y %H:%M')}")

            # 🎁 Jogadores oferecidos na troca (se houver)
            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.markdown("**🎁 Jogadores Oferecidos na Troca:**")
                for j in jogadores_oferecidos:
                    nome = j.get("nome", "Desconhecido")
                    posicao = j.get("posicao", "-")
                    overall = j.get("overall", "-")
                    valor = j.get("valor", 0)
                    st.write(f"• {nome} ({posicao}) - ⭐ {overall} - 💰 R$ {valor:,.0f}".replace(",", "."))

            status = proposta.get("status", "pendente")
            if status == "pendente":
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                        try:
                            # ➕ Adiciona o jogador ao time comprador com novo valor
                            jogador = {
                                "nome": proposta["jogador_nome"],
                                "posicao": proposta["jogador_posicao"],
                                "overall": proposta["jogador_overall"],
                                "valor": proposta["valor_oferecido"],  # novo valor
                                "imagem_url": proposta.get("imagem_url", ""),
                                "nacionalidade": proposta.get("nacionalidade", "-"),
                                "origem": proposta.get("origem", "-"),
                                "classificacao": proposta.get("classificacao", "")
                            }
                            supabase.table("elenco").insert({"id_time": proposta["id_time_origem"], **jogador}).execute()

                            # 🗑️ Remove do vendedor
                            supabase.table("elenco").delete().match({
                                "id_time": proposta["id_time_alvo"],
                                "nome": proposta["jogador_nome"]
                            }).execute()

                            # 🔁 Troca (se houver)
                            for j in jogadores_oferecidos:
                                supabase.table("elenco").insert({
                                    "id_time": proposta["id_time_alvo"],
                                    "nome": j["nome"],
                                    "posicao": j["posicao"],
                                    "overall": j["overall"],
                                    "valor": j["valor"],
                                    "nacionalidade": j.get("nacionalidade", "-"),
                                    "origem": j.get("origem", "-"),
                                    "classificacao": j.get("classificacao", ""),
                                    "imagem_url": j.get("imagem_url", "")
                                }).execute()

                                supabase.table("elenco").delete().match({
                                    "id_time": proposta["id_time_origem"],
                                    "nome": j["nome"]
                                }).execute()

                            # 💰 Saldos
                            if proposta["valor_oferecido"] > 0:
                                saldo_comp = supabase.table("times").select("saldo").eq("id", proposta["id_time_origem"]).execute().data[0]["saldo"]
                                saldo_vend = supabase.table("times").select("saldo").eq("id", proposta["id_time_alvo"]).execute().data[0]["saldo"]

                                supabase.table("times").update({"saldo": saldo_comp - proposta["valor_oferecido"]}).eq("id", proposta["id_time_origem"]).execute()
                                supabase.table("times").update({"saldo": saldo_vend + proposta["valor_oferecido"]}).eq("id", proposta["id_time_alvo"]).execute()

                                registrar_movimentacao(proposta["id_time_origem"], "saida", proposta["valor_oferecido"], f"Compra de {proposta['jogador_nome']}")
                                registrar_movimentacao(proposta["id_time_alvo"], "entrada", proposta["valor_oferecido"], f"Venda de {proposta['jogador_nome']}")

                            # 📝 Registro no BID
                            registrar_bid(proposta["id_time_origem"], "compra", "proposta", proposta["jogador_nome"], -proposta["valor_oferecido"], nome_time, proposta["nome_time_origem"])
                            registrar_bid(proposta["id_time_alvo"], "venda", "proposta", proposta["jogador_nome"], proposta["valor_oferecido"], nome_time, proposta["nome_time_origem"])

                            for j in jogadores_oferecidos:
                                registrar_bid(proposta["id_time_alvo"], "compra", "troca", j["nome"], 0, proposta["nome_time_origem"], nome_time)
                                registrar_bid(proposta["id_time_origem"], "venda", "troca", j["nome"], 0, proposta["nome_time_origem"], nome_time)

                            # Atualiza status
                            supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                            st.success("✅ Proposta aceita com sucesso!")
                            st.experimental_rerun()

                        except Exception as e:
                            st.error(f"Erro ao aceitar proposta: {e}")

                with col2:
                    if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                        try:
                            supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                            st.info("Proposta recusada.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao recusar proposta: {e}")

            elif status == "aceita":
                st.success("✅ Proposta aceita.")
            elif status == "recusada":
                st.error("❌ Proposta recusada.")
