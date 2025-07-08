# 8_📤 Propostas Enviadas.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao
from datetime import datetime

st.set_page_config(page_title="📤 Propostas Enviadas", layout="wide")
verificar_sessao()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔄 Buscar propostas enviadas
try:
    res = supabase.table("propostas").select("*").eq("id_time_origem", id_time).order("data", desc=True).execute()
    propostas = res.data if res.data else []
except Exception as e:
    st.error(f"Erro ao buscar propostas enviadas: {e}")
    propostas = []

# 🔰 Título
st.markdown(f"""
<h3>📤 Propostas Enviadas - {nome_time}</h3>
""", unsafe_allow_html=True)

if not propostas:
    st.info("📭 Nenhuma proposta enviada até o momento.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 3])

            with col1:
                imagem = proposta.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                st.image(imagem, width=80)

            with col2:
                st.markdown(f"### {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
                st.write(f"🌍 **Nacionalidade:** {proposta.get('nacionalidade', 'Desconhecida')}")
                st.write(f"📌 **Posição:** {proposta['jogador_posicao']}")
                st.write(f"⭐ **Overall:** {proposta['jogador_overall']}")
                st.write(f"💰 **Valor do Jogador:** R$ {proposta.get('jogador_valor', 0):,.0f}".replace(",", "."))
                st.write(f"🏟️ **Clube Alvo:** {proposta.get('nome_time_destino', 'Desconhecido')}")
                st.write(f"📦 **Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
                st.write(f"📅 **Data da Proposta:** {datetime.fromisoformat(proposta['data']).strftime('%d/%m/%Y %H:%M')}")

                status = proposta.get("status", "pendente")

                if status == "pendente":
                    st.warning("⏳ Proposta ainda não respondida.")

                    # 🔧 Edição do valor
                    with st.expander("✏️ Editar Proposta"):
                        novo_valor = st.number_input(
                            f"Novo valor para {proposta['jogador_nome']}",
                            min_value=1,
                            value=int(proposta["valor_oferecido"]),
                            step=1_000_000,
                            key=f"edit_{proposta['id']}"
                        )
                        if st.button("💾 Salvar alteração", key=f"save_{proposta['id']}"):
                            try:
                                supabase.table("propostas").update({
                                    "valor_oferecido": novo_valor,
                                    "data": datetime.now().isoformat()
                                }).eq("id", proposta["id"]).execute()
                                st.success("✅ Proposta atualizada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar proposta: {e}")

                    # ❌ Cancelar proposta
                    if st.button("❌ Cancelar Proposta", key=f"cancel_{proposta['id']}"):
                        try:
                            supabase.table("propostas").delete().eq("id", proposta["id"]).execute()
                            st.success("✅ Proposta cancelada com sucesso.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cancelar proposta: {e}")

                elif status == "aceita":
                    st.success("✅ Proposta aceita.")
                elif status == "recusada":
                    st.error("❌ Proposta recusada.")
                elif status == "contraproposta":
                    st.info("🔁 Contra proposta enviada.")
