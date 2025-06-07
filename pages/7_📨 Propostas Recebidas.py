# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

# Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.error("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# Consulta propostas recebidas
try:
    res = supabase.table("propostas").select("*").eq("id_time_alvo", id_time).neq("status", "recusada").execute()
    propostas = res.data
except Exception as e:
    st.error(f"Erro ao buscar propostas: {e}")
    st.stop()

if not propostas:
    st.info("Nenhuma proposta recebida no momento.")
    st.stop()

for proposta in propostas:
    with st.container():
        st.subheader(f"Proposta de {proposta['nome_time_origem']} por {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
        st.write(f"💰 Valor oferecido: R$ {proposta['valor_oferecido']:,}".replace(",", "."))
        if proposta.get("jogadores_oferecidos"):
            st.write("🔁 Jogadores oferecidos:")
            for jogador in proposta["jogadores_oferecidos"]:
                st.markdown(f"- **{jogador['nome']}** ({jogador['posicao']}) | {jogador['overall']} | R$ {jogador['valor']:,}".replace(",", "."))

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                # Transferência do jogador
                jogador = {
                    "nome": proposta["jogador_nome"],
                    "posicao": proposta["jogador_posicao"],
                    "overall": proposta["jogador_overall"],
                    "valor": proposta["jogador_valor"]
                }

                # Remover jogador do time alvo (quem está sendo comprado)
                supabase.table("elencos").delete().eq("id_time", id_time).eq("nome", jogador["nome"]).execute()

                # Adicionar jogador ao time de origem (quem comprou)
                supabase.table("elencos").insert({
                    "id_time": proposta["id_time_origem"],
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": proposta["valor_oferecido"]
                }).execute()

                # Atualizar proposta como aceita
                supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                # Atualizar saldos
                supabase.table("times").rpc("atualizar_saldo_transferencia", {
                    "id_time_origem": proposta["id_time_origem"],
                    "id_time_alvo": proposta["id_time_alvo"],
                    "valor": proposta["valor_oferecido"]
                }).execute()

                # Registrar no BID
                supabase.table("bid").insert({
                    "jogador": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "valor": proposta["valor_oferecido"],
                    "origem": proposta["nome_time_origem"],
                    "destino": proposta["nome_time_alvo"]
                }).execute()

                # Movimentação financeira
                registrar_movimentacao(proposta["id_time_origem"], f"Compra de {jogador['nome']} do {proposta['nome_time_alvo']}", -proposta["valor_oferecido"])
                registrar_movimentacao(proposta["id_time_alvo"], f"Venda de {jogador['nome']} para o {proposta['nome_time_origem']}", proposta["valor_oferecido"])

                st.success("✅ Proposta aceita com sucesso!")
                st.experimental_rerun()

        with col2:
            if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                st.warning("❌ Proposta recusada.")
                st.experimental_rerun()

        with col3:
            nova_valor = st.number_input("Contra-proposta", min_value=1, value=proposta["valor_oferecido"], step=50000, key=f"contra_{proposta['id']}")
            if st.button("📤 Enviar Contra-Proposta", key=f"enviar_contra_{proposta['id']}"):
                supabase.table("propostas").update({
                    "valor_oferecido": nova_valor,
                    "status": "pendente"
                }).eq("id", proposta["id"]).execute()
                st.info("📤 Contra-proposta enviada.")
                st.experimental_rerun()

