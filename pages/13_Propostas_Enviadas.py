import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Propostas Enviadas - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📤 Propostas Enviadas")

# 🚫 Verifica status do mercado
try:
    status_ref = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
    mercado_aberto = status_ref.data[0]["mercado_aberto"] if status_ref.data else False
except Exception as e:
    st.error(f"Erro ao verificar status do mercado: {e}")
    mercado_aberto = False

if not mercado_aberto:
    st.warning("⚠️ O mercado está fechado. As propostas enviadas ainda estão visíveis, mas não podem ser aceitas ou recusadas no momento.")

# 🔎 Buscar propostas enviadas
try:
    propostas_ref = supabase.table("negociacoes") \
        .select("*") \
        .eq("id_time_origem", id_time) \
        .order("data", desc=True) \
        .execute()

    propostas = propostas_ref.data

    if not propostas:
        st.info("Você ainda não enviou nenhuma proposta.")
    else:
        for proposta in propostas:
            jogador = proposta.get("jogador_desejado", "Desconhecido")
            tipo = proposta.get("tipo_negociacao", "N/A")
            status = proposta.get("status", "pendente")
            valor = proposta.get("valor_oferecido", 0)
            jogadores_oferecidos = proposta.get("jogador_oferecido", None)
            data = proposta.get("data")

            # Trata data (ISO)
            if data:
                try:
                    data_obj = datetime.fromisoformat(data)
                    data_str = data_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    data_str = "Data inválida"
            else:
                data_str = "Data não disponível"

            st.markdown("---")
            st.markdown(f"**🎯 Jogador Alvo:** {jogador}")
            st.markdown(f"**📌 Tipo de Proposta:** {tipo.capitalize()}")
            st.markdown(f"**💬 Status:** {status.capitalize()}")
            st.markdown(f"**💰 Valor Oferecido:** R$ {valor:,.0f}".replace(",", "."))

            if jogadores_oferecidos:
                st.markdown(f"**👥 Jogador Oferecido na Troca:** {jogadores_oferecidos}")

            st.markdown(f"**📅 Enviada em:** {data_str}")
except Exception as e:
    st.error(f"Erro ao carregar propostas: {e}")
