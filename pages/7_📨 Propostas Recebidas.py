# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from supabase import create_client
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")

verificar_login()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados do usuário logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title(f"📨 Propostas Recebidas - {nome_time}")

# 🔍 Carregar apenas propostas pendentes
res = supabase.table("propostas").select("*").eq("destino_id", id_time).eq("status", "pendente").execute()
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

                    # Remover jogador do time vendedor
                    supabase.table("elenco").delete().eq("id_time", id_time_destino).eq("nome", jogador_nome).execute()

                    # Adicionar ao comprador com novo valor
                    novo_jogador = {
                        "nome": jogador_nome,
                        "posicao": proposta["jogador_posicao"],
                        "overall": proposta["jogador_overall"],
                        "valor": valor,
                        "id_time": id_time_origem
                    }
                    supabase.table("elenco").insert(novo_jogador).execute()

                    # Troca de jogadores (se houver)
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

                    # Registrar movimentações financeiras
                    if valor > 0:
                        registrar_movimentacao(id_time_origem, jogador_nome, "proposta", "compra", valor)
                        registrar_movimentacao(id_time_destino, jogador_nome, "proposta", "venda", valor)

                    # Atualizar status da proposta aceita
                    supabase.table("propostas").update({"status": "aceita"}).eq("id", proposta["id"]).execute()

                    # Cancelar outras propostas pendentes pelo mesmo jogador
                    supabase.table("propostas").update({"status": "cancelada"}) \
                        .eq("jogador_nome", jogador_nome) \
                        .eq("destino_id", id_time) \
                        .eq("status", "pendente") \
                        .neq("id", proposta["id"]).execute()

                    st.success(f"✅ Proposta aceita! {jogador_nome} foi transferido para {proposta['nome_time_origem']}.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao aceitar a proposta: {e}")

            if col2.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                try:
                    supabase.table("propostas").update({"status": "recusada"}).eq("id", proposta["id"]).execute()
                    st.warning("❌ Proposta recusada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao recusar a proposta: {e}")
