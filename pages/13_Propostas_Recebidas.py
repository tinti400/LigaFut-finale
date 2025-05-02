import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Propostas Recebidas - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Dados do time logado
id_time_logado = st.session_state["id_time"]
nome_time_logado = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")

# 🔍 Busca propostas destinadas ao time logado
propostas_ref = supabase.table("negociacoes").select("*").eq("id_time_destino", id_time_logado).execute()
propostas = propostas_ref.data

if not propostas:
    st.info("Nenhuma proposta recebida até o momento.")
    st.stop()

for proposta in propostas:
    st.markdown("---")
    
    # Verificando se as chaves necessárias existem na proposta antes de acessá-las
    jogador_nome = proposta.get("jogador_desejado", "Desconhecido")
    jogador_overall = proposta.get("overall_jogador_desejado", "N/A")
    valor = proposta.get("valor_oferecido", 0)
    tipo = proposta.get("tipo_negociacao", "N/A")
    status = proposta.get("status", "pendente")
    jogadores_oferecidos = proposta.get("jogador_oferecido", [])
    time_origem_id = proposta.get("id_time_origem")

    # Busca o nome do time que fez a proposta
    time_origem_ref = supabase.table("times").select("nome").eq("id", time_origem_id).execute()
    nome_time_origem = time_origem_ref.data[0]["nome"] if time_origem_ref.data else "Desconhecido"

    col1, col2 = st.columns([4, 2])
    with col1:
        st.markdown(f"**👤 Jogador Desejado:** {jogador_nome} - ⭐ {jogador_overall}")
        st.markdown(f"**💼 Tipo de proposta:** {tipo}")
        st.markdown(f"**💸 Valor em dinheiro:** R$ {valor:,.0f}".replace(",", "."))
        
        if jogadores_oferecidos:
            st.markdown("**👥 Jogadores oferecidos:**")
            for j in jogadores_oferecidos:
                st.markdown(f"- {j}")  # Exibe os jogadores oferecidos

        st.markdown(f"**📝 Status:** {status.upper()}")

    with col2:
        try:
            if status == "pendente":
                aceitar = st.button("✅ Aceitar", key=f"aceitar_{proposta['id_doc']}")
                recusar = st.button("❌ Recusar", key=f"recusar_{proposta['id_doc']}")

                if aceitar:
                    jogador_id = proposta.get("id_jogador")
                    jogador_data = {
                        "nome": jogador_nome,
                        "overall": jogador_overall,
                        "valor": valor,  # O valor do jogador será o valor da proposta
                        "id_time": time_origem_id  # Atualiza o time do jogador
                    }

                    # Remover jogador do time atual
                    supabase.table("elenco").delete().eq("id_time", id_time_logado).eq("id", jogador_id).execute()

                    # Adiciona jogador ao time comprador
                    supabase.table("elenco").insert(jogador_data).execute()

                    # Atualiza status da proposta
                    supabase.table("negociacoes").update({
                        "status": "aceita",
                        "valor_aceito": valor
                    }).eq("id_doc", proposta["id_doc"]).execute()

                    st.success("✅ Proposta aceita com sucesso!")
                    st.rerun()

                if recusar:
                    supabase.table("negociacoes").update({"status": "recusada"}).eq("id_doc", proposta["id_doc"]).execute()
                    st.warning("🚫 Proposta recusada.")
                    st.rerun()
            else:
                # Exclui propostas já respondidas
                supabase.table("negociacoes").delete().eq("id_doc", proposta["id_doc"]).execute()
                st.info("⏳ Proposta já respondida e excluída.")
        except Exception as e:
            st.error(f"Erro ao processar a proposta: {e}")