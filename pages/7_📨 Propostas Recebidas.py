# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")
verificar_login()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📨 Propostas Recebidas")
st.markdown("---")

propostas = supabase.table("propostas").select("*").eq("time_destino", id_time).execute().data

if not propostas:
    st.info("Nenhuma proposta recebida no momento.")
else:
    for proposta in propostas:
        st.subheader(f"💰 Proposta por: {proposta['jogador_nome']}")
        st.write(f"📤 Time que enviou: `{proposta['nome_time_origem']}`")
        st.write(f"💸 Valor oferecido: R$ {proposta['valor']:,}".replace(",", "."))
        st.write(f"📅 Data: {proposta['data'].split('T')[0]}")
        st.write(f"📦 Tipo: {proposta['tipo']}")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                try:
                    # Buscar saldo do comprador
                    origem_id = proposta["time_origem"]
                    destino_id = proposta["time_destino"]
                    valor = proposta["valor"]

                    res = supabase.table("times").select("saldo").eq("id", origem_id).execute()
                    saldo_atual = res.data[0]["saldo"] if res.data else 0
                    novo_saldo = saldo_atual - valor

                    # Atualizar saldo do comprador
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", origem_id).execute()

                    # Atualizar saldo do vendedor
                    res_v = supabase.table("times").select("saldo").eq("id", destino_id).execute()
                    saldo_v = res_v.data[0]["saldo"] if res_v.data else 0
                    novo_saldo_v = saldo_v + valor
                    supabase.table("times").update({"saldo": novo_saldo_v}).eq("id", destino_id).execute()

                    # Transferir jogador
                    jogador = {
                        "nome": proposta["jogador_nome"],
                        "posicao": proposta["jogador_posicao"],
                        "overall": proposta["jogador_overall"],
                        "valor": proposta["valor"]
                    }
                    supabase.table("elenco").insert({**jogador, "id_time": origem_id}).execute()
                    supabase.table("elenco").delete().eq("id", proposta["id_jogador"]).execute()

                    # Registrar movimentações
                    registrar_movimentacao(origem_id, proposta["jogador_nome"], "Transferência - Compra", "compra", valor)
                    registrar_movimentacao(destino_id, proposta["jogador_nome"], "Transferência - Venda", "venda", valor)

                    # Remover proposta
                    supabase.table("propostas").delete().eq("id", proposta["id"]).execute()

                    st.success("✅ Proposta aceita com sucesso!")

                except Exception as e:
                    st.error(f"Erro ao aceitar a proposta: {e}")

        with col2:
            if st.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                supabase.table("propostas").delete().eq("id", proposta["id"]).execute()
                st.warning("🚫 Proposta recusada.")

        with col3:
            if st.button("🔁 Contra proposta", key=f"contra_{proposta['id']}"):
                novo_valor = st.number_input("💰 Valor da contra proposta", min_value=0, step=100000,
                                             value=proposta["valor"], key=f"input_{proposta['id']}")
                if st.button("📨 Enviar contra proposta", key=f"enviar_contra_{proposta['id']}"):
                    supabase.table("propostas").update({
                        "valor": novo_valor,
                        "status": "pendente"
                    }).eq("id", proposta["id"]).execute()
                    st.success("✅ Contra proposta enviada.")
