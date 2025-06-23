# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao
import uuid

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica se o usuário está logado
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# 🔄 Buscar propostas recebidas
res = supabase.table("propostas").select("*").eq("id_time_alvo", id_time).eq("status", "pendente").execute()
propostas = res.data or []

if not propostas:
    st.info("Nenhuma proposta recebida no momento.")
    st.stop()

for proposta in propostas:
    with st.container():
        st.markdown("---")
        st.subheader(f"📩 Proposta por {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
        st.markdown(f"**De:** {proposta['nome_time_origem']}")
        st.markdown(f"**Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))

        if proposta["jogadores_oferecidos"]:
            st.markdown("**Jogadores Oferecidos:**")
            for j in proposta["jogadores_oferecidos"]:
                st.markdown(f"- {j['nome']} ({j['posicao']}, OVR {j['overall']})")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                # 🔄 Atualiza status da proposta
                supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                # 🔄 Atualiza saldo
                origem = proposta["id_time_origem"]
                destino = proposta["id_time_alvo"]
                valor = proposta["valor_oferecido"]

                # Subtrai do comprador
                res_origem = supabase.table("times").select("saldo").eq("id", origem).execute()
                saldo_origem = res_origem.data[0]["saldo"] if res_origem.data else 0
                novo_saldo_origem = saldo_origem - valor
                supabase.table("times").update({"saldo": novo_saldo_origem}).eq("id", origem).execute()

                # Registra movimentação
                registrar_movimentacao(origem, "saida", valor, f"Compra de {proposta['jogador_nome']}")
                registrar_movimentacao(destino, "entrada", valor, f"Venda de {proposta['jogador_nome']}")

                # Adiciona jogador no elenco do comprador
                novo_jogador = {
                    "id": str(uuid.uuid4()),
                    "id_time": origem,
                    "nome": proposta["jogador_nome"],
                    "posicao": proposta["jogador_posicao"],
                    "overall": proposta["jogador_overall"],
                    "valor": proposta["jogador_valor"],
                    "imagem_url": proposta.get("imagem_url", ""),
                    "nacionalidade": proposta.get("nacionalidade", "-"),
                    "origem": proposta.get("origem", "-"),
                    "classificacao": proposta.get("classificacao", "")
                }
                supabase.table("elenco").insert(novo_jogador).execute()

                # Remove jogador do time atual
                supabase.table("elenco").delete().eq("id_time", destino).eq("nome", proposta["jogador_nome"]).execute()

                st.success("✅ Proposta aceita com sucesso!")
                st.experimental_rerun()

        with col2:
            if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                st.warning("❌ Proposta recusada.")
                st.experimental_rerun()

        with col3:
            if st.button("🔁 Contra Proposta", key=f"contra_{proposta['id']}"):
                st.session_state["contra_proposta"] = proposta
                st.switch_page("13_Propostas_Enviadas")
