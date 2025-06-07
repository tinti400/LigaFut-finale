# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Negociações entre Clubes", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# 🚫 Verificar status do mercado
try:
    status_ref = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
    mercado_aberto = status_ref.data[0]["mercado_aberto"] if status_ref.data else False
except Exception as e:
    st.error(f"Erro ao verificar status do mercado: {e}")
    mercado_aberto = False

st.title("🤝 Negociações entre Clubes")
st.markdown(f"### Seu Time: **{nome_time}**")

if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento. As negociações entre clubes estão desativadas.")
    st.stop()

# 🔍 Buscar outros times
res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times = {t["id"]: t["nome"] for t in res_times.data}

# 📋 Buscar elenco do time logado
res_elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
meu_elenco = res_elenco.data or []

# 🔁 Exibir todos os outros times
for id_time_adv, nome_adv in times.items():
    with st.expander(f"⚽ {nome_adv}"):

        elenco_adv = supabase.table("elenco").select("*").eq("id_time", id_time_adv).execute().data or []

        if not elenco_adv:
            st.info("Nenhum jogador disponível neste time.")
        else:
            for jogador in elenco_adv:
                st.markdown("---")
                st.markdown(f"**👤 Nome:** {jogador.get('nome', '-')}")
                st.markdown(f"**🎯 Overall:** {jogador.get('overall', '-')}")
                valor_jogador = jogador.get("valor", 0)
                st.markdown(f"**💰 Valor:** R$ {valor_jogador:,.0f}")

                tipo = st.radio(
                    f"Tipo de negociação para {jogador['nome']}",
                    ["Somente Dinheiro", "Troca Simples", "Troca Composta"],
                    horizontal=True,
                    key=f"tipo_{jogador['id']}"
                )

                jogador_oferecido = []
                valor_proposta = 0

                if tipo == "Somente Dinheiro":
                    valor_proposta = st.number_input(
                        "💵 Valor da Proposta (R$)",
                        min_value=valor_jogador,
                        step=500_000,
                        value=valor_jogador,
                        key=f"valor_dinheiro_{jogador['id']}"
                    )

                elif tipo == "Troca Simples":
                    opcoes = [f"{j['nome']} (OVR {j['overall']})" for j in meu_elenco]
                    selecao = st.selectbox(
                        "🔁 Escolha um jogador do seu elenco",
                        opcoes,
                        key=f"troca_simples_{jogador['id']}"
                    )
                    jogador_oferecido = [meu_elenco[opcoes.index(selecao)]["id"]]
                    valor_proposta = 0

                elif tipo == "Troca Composta":
                    opcoes = [f"{j['nome']} (OVR {j['overall']})" for j in meu_elenco]
                    selecao = st.multiselect(
                        "🔁 Escolha um ou mais jogadores do seu elenco",
                        opcoes,
                        key=f"troca_composta_{jogador['id']}"
                    )
                    jogador_oferecido = [meu_elenco[opcoes.index(s)]["id"] for s in selecao]
                    valor_proposta = st.number_input(
                        "💰 Valor adicional em dinheiro (R$)",
                        min_value=0,
                        step=500_000,
                        key=f"valor_composta_{jogador['id']}"
                    )

                if st.button("📩 Enviar Proposta", key=f"btn_proposta_{jogador['id']}"):
                    if tipo != "Somente Dinheiro" and not jogador_oferecido:
                        st.warning("Selecione ao menos um jogador do seu elenco para a troca.")
                    elif tipo == "Somente Dinheiro" and valor_proposta < valor_jogador:
                        st.warning(f"O valor deve ser igual ou superior a R$ {valor_jogador:,.0f}")
                    else:
                        proposta = {
                            "id": jogador["id"] + "_" + id_time,  # ID único
                            "id_time_origem": id_time,
                            "nome_time_origem": nome_time,
                            "destino_id": id_time_adv,
                            "nome_time_alvo": nome_adv,
                            "jogador_nome": jogador["nome"],
                            "jogador_posicao": jogador["posicao"],
                            "jogador_overall": jogador["overall"],
                            "jogador_valor": jogador["valor"],
                            "valor_oferecido": int(valor_proposta),
                            "jogadores_oferecidos": jogador_oferecido,
                            "status": "pendente",
                            "created_at": datetime.now().isoformat()
                        }
                        try:
                            resp = supabase.table("propostas").insert(proposta).execute()
                            if resp.data:
                                st.success("✅ Proposta enviada com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao enviar proposta.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
