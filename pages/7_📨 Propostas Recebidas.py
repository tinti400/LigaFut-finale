# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")
verificar_sessao()

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔄 Buscar propostas pendentes
res = supabase.table("propostas").select("*").eq("destino_id", id_time).eq("status", "pendente").execute()
propostas = res.data if res.data else []

# 🔔 Sidebar
with st.sidebar:
    if propostas:
        st.markdown(f"""
        <span style='color:white;background:red;padding:4px 10px;border-radius:50%;font-size:14px'>
        {len(propostas)}</span> 🔔 Propostas Recebidas
        """, unsafe_allow_html=True)

st.markdown(f"""
<h3>📨 Propostas Recebidas - {nome_time}
<span style='color:white;background:red;padding:2px 8px;border-radius:50%;margin-left:10px;'>{len(propostas)}</span>
</h3>
""", unsafe_allow_html=True)

if not propostas:
    st.info("📭 Nenhuma proposta pendente no momento.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 3])

            with col1:
                imagem = proposta.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                st.image(imagem, width=80)

            with col2:
                st.markdown(f"**👤 Jogador:** {proposta['jogador_nome']}")
                st.markdown(f"📌 **Posição:** {proposta['jogador_posicao']}")
                st.markdown(f"⭐ **Overall:** {proposta['jogador_overall']}")
                st.markdown(f"💰 **Valor da Proposta:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))
                if proposta["jogadores_oferecidos"]:
                    st.markdown("🔁 **Jogadores oferecidos:**")
                    for j in proposta["jogadores_oferecidos"]:
                        st.markdown(f"- {j['nome']} (OVR {j['overall']})")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                        try:
                            # Atualizar status da proposta
                            supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                            # Remover jogador do time atual (destino) e mover para o comprador (origem)
                            jogador_data = {
                                "nome": proposta["jogador_nome"],
                                "posicao": proposta["jogador_posicao"],
                                "overall": proposta["jogador_overall"],
                                "valor": proposta["jogador_valor"],
                                "imagem_url": proposta.get("imagem_url", ""),
                                "nacionalidade": proposta.get("nacionalidade", "-"),
                                "origem": proposta.get("origem", "-"),
                                "classificacao": proposta.get("classificacao", "")
                            }
                            supabase.table("elenco").insert({"id_time": proposta["id_time_origem"], **jogador_data}).execute()
                            supabase.table("elenco").delete().eq("id_time", proposta["id_time_alvo"]).eq("nome", proposta["jogador_nome"]).execute()

                            # Transferência de jogadores oferecidos (se houver)
                            for j in proposta["jogadores_oferecidos"]:
                                novo = {
                                    "id_time": proposta["id_time_alvo"],
                                    "nome": j["nome"],
                                    "posicao": j["posicao"],
                                    "overall": j["overall"],
                                    "valor": j["valor"],
                                    "imagem_url": j.get("imagem_url", ""),
                                    "nacionalidade": j.get("nacionalidade", "-"),
                                    "origem": j.get("origem", "-"),
                                    "classificacao": j.get("classificacao", "")
                                }
                                supabase.table("elenco").insert(novo).execute()
                                supabase.table("elenco").delete().eq("id_time", proposta["id_time_origem"]).eq("nome", j["nome"]).execute()

                            # 💸 Fluxo financeiro correto
                            valor = proposta["valor_oferecido"]
                            if valor and valor > 0:
                                registrar_movimentacao(proposta["id_time_origem"], "saida", valor, f"Compra de {proposta['jogador_nome']}")
                                registrar_movimentacao(proposta["id_time_alvo"], "entrada", valor, f"Venda de {proposta['jogador_nome']}")

                            st.success("✅ Proposta aceita com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao aceitar proposta: {e}")

                with col_b:
                    if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                        supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                        st.warning("Proposta recusada.")
                        st.rerun()

