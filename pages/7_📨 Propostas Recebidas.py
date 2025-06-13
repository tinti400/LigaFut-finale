# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")
verificar_sessao()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔴 Contador de propostas pendentes
count_recebidas = supabase.table("propostas").select("*").eq("destino_id", id_time).eq("status", "pendente").execute()
notificacoes_recebidas = len(count_recebidas.data) if count_recebidas.data else 0

st.markdown(f"""
<h3>📨 Propostas Recebidas - {nome_time}
<span style='color:white;background:red;padding:2px 8px;border-radius:50%;margin-left:10px;'>{notificacoes_recebidas}</span>
</h3>
""", unsafe_allow_html=True)

res = count_recebidas
propostas = res.data if res.data else []

if not propostas:
    st.info("📭 Nenhuma proposta pendente no momento.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown(f"### {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
            st.write(f"**Overall:** {proposta['jogador_overall']}")
            st.write(f"**Valor Oferecido:** R$ {proposta['valor_oferecido']:,}".replace(",", "."))
            st.write(f"**Proposta de:** {proposta['nome_time_origem']}")

            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.write("**Jogadores Oferecidos em Troca:**")
                for j in jogadores_oferecidos:
                    st.write(f"- {j['nome']} (OVR {j['overall']}) - {j['posicao']}")

            col1, col2 = st.columns(2)

            if col1.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                try:
                    valor = proposta["valor_oferecido"]
                    id_time_origem = proposta["id_time_origem"]
                    id_time_destino = proposta["id_time_alvo"]
                    jogador_nome = proposta["jogador_nome"]

                    supabase.table("elenco").delete().eq("id_time", id_time_destino).eq("nome", jogador_nome).execute()

                    novo_jogador = {
                        "nome": jogador_nome,
                        "posicao": proposta["jogador_posicao"],
                        "overall": proposta["jogador_overall"],
                        "valor": valor,
                        "id_time": id_time_origem
                    }
                    supabase.table("elenco").insert(novo_jogador).execute()

                    for jogador in jogadores_oferecidos:
                        supabase.table("elenco").delete().eq("id_time", id_time_origem).eq("nome", jogador["nome"]).execute()
                        jogador_trocado = {
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"],
                            "id_time": id_time_destino
                        }
                        supabase.table("elenco").insert(jogador_trocado).execute()

                    if valor > 0:
                        registrar_movimentacao(id_time_origem, jogador_nome, "Transferência", "Compra", valor)
                        registrar_movimentacao(id_time_destino, jogador_nome, "Transferência", "Venda", valor)

                    supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()
                    supabase.table("propostas").update({"status": "cancelada"})                         .eq("jogador_nome", jogador_nome)                         .eq("destino_id", id_time)                         .eq("status", "pendente")                         .neq("id", proposta["id"]).execute()

                    st.success(f"✅ Proposta aceita! {jogador_nome} foi transferido para {proposta['nome_time_origem']}.")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Erro ao aceitar a proposta: {e}")

            if col2.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                try:
                    supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                    st.warning("❌ Proposta recusada.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao recusar a proposta: {e}")
