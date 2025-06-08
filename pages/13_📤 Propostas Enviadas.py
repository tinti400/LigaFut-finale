# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
from utils import verificar_sessao  # ✅ Sessão única

st.set_page_config(page_title="📤 Propostas Enviadas - LigaFut", layout="wide")

verificar_sessao()  # ✅ Aplicação de sessão única

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Dados do time logado
id_time_origem = st.session_state["id_time"]
nome_time_origem = st.session_state["nome_time"]

st.title("📤 Propostas Enviadas")

# 🧠 Buscar todos os times (para enviar proposta)
times_ref = supabase.table("times").select("id", "nome").neq("id", id_time_origem).execute()
times_disponiveis = times_ref.data or []

nomes_times = {t["nome"]: t["id"] for t in times_disponiveis}
nome_time_alvo = st.selectbox("Escolha o time para enviar proposta:", list(nomes_times.keys()))

# Buscar elenco do time escolhido
id_time_alvo = nomes_times[nome_time_alvo]
elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time_alvo).execute()
elenco_disponivel = elenco_ref.data or []

jogadores_alvo = [f'{j["nome"]} ({j["posicao"]})' for j in elenco_disponivel]
jogador_escolhido = st.selectbox("Escolha o jogador desejado:", jogadores_alvo)

# Dados do jogador alvo
jogador_data = next((j for j in elenco_disponivel if f'{j["nome"]} ({j["posicao"]})' == jogador_escolhido), None)

# Valor da proposta
valor_oferecido = st.number_input("Valor oferecido (R$):", min_value=0, step=100000)

if st.button("📩 Enviar proposta"):
    if jogador_data:
        try:
            nova_proposta = {
                "id": str(uuid.uuid4()),
                "id_time_origem": id_time_origem,
                "nome_time_origem": nome_time_origem,
                "id_time_alvo": id_time_alvo,
                "nome_time_alvo": nome_time_alvo,
                "jogador_nome": jogador_data["nome"],
                "jogador_posicao": jogador_data["posicao"],
                "jogador_overall": jogador_data["overall"],
                "jogador_valor": jogador_data["valor"],
                "valor_oferecido": valor_oferecido,
                "status": "pendente",
                "created_at": datetime.now().isoformat()
            }
            supabase.table("propostas").insert(nova_proposta).execute()
            st.success("✅ Proposta enviada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao enviar proposta: {e}")
    else:
        st.warning("Jogador não encontrado!")

# 🔎 Ver propostas enviadas
st.subheader("📜 Suas propostas enviadas")
try:
    propostas_ref = supabase.table("propostas") \
        .select("*") \
        .eq("id_time_origem", id_time_origem) \
        .order("created_at", desc=True) \
        .execute()

    propostas = propostas_ref.data or []
    if not propostas:
        st.info("Você ainda não enviou nenhuma proposta.")
    else:
        for p in propostas:
            with st.container():
                st.markdown("---")
                st.markdown(f"**🎯 Jogador Alvo:** {p['jogador_nome']} ({p['jogador_posicao']})")
                st.markdown(f"**🎽 Time Alvo:** {p['nome_time_alvo']}")
                st.markdown(f"**💰 Valor Oferecido:** R$ {p['valor_oferecido']:,.0f}".replace(",", "."))
                st.markdown(f"**📅 Enviada em:** {datetime.fromisoformat(p['created_at']).strftime('%d/%m/%Y %H:%M')}")
                st.markdown(f"**📌 Status:** {p['status'].capitalize()}")

                if p["status"] == "pendente":
                    if st.button("❌ Cancelar proposta", key=f"cancelar_{p['id']}"):
                        try:
                            supabase.table("propostas").update({"status": "cancelada"}).eq("id", p["id"]).execute()
                            st.warning("❌ Proposta cancelada.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao cancelar proposta: {e}")
except Exception as e:
    st.error(f"Erro ao buscar propostas enviadas: {e}")
