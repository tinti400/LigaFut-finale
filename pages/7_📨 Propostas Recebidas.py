# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
from utils import registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# 📥 Buscar propostas recebidas
res = supabase.table("propostas").select("*").eq("id_time_alvo", id_time).eq("status", "pendente").execute()
propostas = res.data or []

if not propostas:
    st.info("Nenhuma proposta recebida no momento.")
else:
    for proposta in propostas:
        st.markdown("---")
        st.markdown(f"👤 **Jogador:** {proposta['jogador_nome']}")
        st.markdown(f"📌 **Posição:** {proposta['jogador_posicao']}")
        st.markdown(f"⭐ **Overall:** {proposta['jogador_overall']}")
        st.markdown(f"💰 **Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
        st.markdown(f"📨 **Proposta enviada por:** {proposta['nome_time_origem']}")

        if proposta.get("jogadores_oferecidos"):
            st.markdown("🔁 **Jogadores Oferecidos em Troca:**")
            for j in proposta["jogadores_oferecidos"]:
                st.markdown(f"- {j.get('nome', '')} (OVR {j.get('overall', '')})")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                try:
                    # 🔄 Transferir jogador para o novo time
                    novo_jogador = {
                        "id": str(uuid.uuid4()),
                        "id_time": proposta["id_time_origem"],
                        "nome": proposta["jogador_nome"],
                        "posicao": proposta["jogador_posicao"],
                        "overall": proposta["jogador_overall"],
                        "valor": proposta["jogador_valor"],
                        "imagem_url": proposta.get("imagem_url", ""),
                        "nacionalidade": proposta.get("nacionalidade", "-"),
                        "origem": proposta.get("origem", "-"),
                        "classificacao": proposta.get("classificacao", "-")
                    }
                    supabase.table("elenco").insert(novo_jogador).execute()

                    # 🔄 Remover jogador do elenco do time atual
                    supabase.table("elenco").delete().match({
                        "id_time": proposta["id_time_alvo"],
                        "nome": proposta["jogador_nome"]
                    }).execute()

                    # 🔁 Inserir jogadores oferecidos no elenco do time atual
                    for j in proposta.get("jogadores_oferecidos", []):
                        jogador_recebido = {
                            "id": str(uuid.uuid4()),
                            "id_time": proposta["id_time_alvo"],
                            "nome": j["nome"],
                            "posicao": j["posicao"],
                            "overall": j["overall"],
                            "valor": j["valor"],
                            "imagem_url": j.get("imagem_url", ""),
                            "nacionalidade": j.get("nacionalidade", "-"),
                            "origem": j.get("origem", "-"),
                            "classificacao": j.get("classificacao", "-")
                        }
                        supabase.table("elenco").insert(jogador_recebido).execute()

                        # 🔄 Remover jogador oferecido do time de origem
                        supabase.table("elenco").delete().match({
                            "id_time": proposta["id_time_origem"],
                            "nome": j["nome"]
                        }).execute()

                    # 💸 Atualizar saldo do time que vendeu
                    if proposta["valor_oferecido"] > 0:
                        supabase.table("times").update({
                            "saldo": f"saldo + {proposta['valor_oferecido']}"
                        }).eq("id", proposta["id_time_alvo"]).execute()

                        registrar_movimentacao(
                            id_time=proposta["id_time_alvo"],
                            tipo="entrada",
                            valor=proposta["valor_oferecido"],
                            descricao=f"Venda de {proposta['jogador_nome']} para {proposta['nome_time_origem']}"
                        )

                    # ✅ Atualizar status da proposta
                    supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                    st.success("✅ Proposta aceita e jogadores transferidos com sucesso!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao aceitar proposta: {e}")

        with col2:
            if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                try:
                    supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                    st.warning("🚫 Proposta recusada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao recusar proposta: {e}")
