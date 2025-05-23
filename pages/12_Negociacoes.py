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

st.title("🤝 Negociações entre Clubes")
st.markdown(f"### Seu Time: **{nome_time}**")

# 🔍 Buscar outros times
res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times = {t["id"]: t["nome"] for t in res_times.data}

# 📋 Buscar elenco do time logado
res_elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
meu_elenco = res_elenco.data

# 🔐 Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔁 Exibir todos os outros times
for id_time_adv, nome_adv in times.items():
    with st.expander(f"⚽ {nome_adv}"):
        # 👑 Painel do Admin para adicionar jogador
        if eh_admin:
            with st.form(f"form_adicionar_{id_time_adv}"):
                st.subheader("📥 Adicionar Jogador ao Elenco")

                col1, col2 = st.columns(2)
                nome = col1.text_input("Nome do Jogador")
                posicao = col2.selectbox("Posição", [
                    "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
                    "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
                    "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
                ])

                col3, col4 = st.columns(2)
                overall = col3.number_input("Overall", min_value=1, max_value=99, step=1)
                nacionalidade = col4.text_input("Nacionalidade")

                col5, col6 = st.columns(2)
                valor = col5.number_input("Valor (R$)", min_value=0, step=100_000)
                origem = col6.text_input("Time de Origem")

                if st.form_submit_button("➕ Adicionar Jogador"):
                    if all([nome, posicao, overall, nacionalidade, valor > 0, origem]):
                        try:
                            supabase.table("elenco").insert({
                                "id_time": id_time_adv,
                                "nome": nome,
                                "posicao": posicao,
                                "overall": overall,
                                "nacionalidade": nacionalidade,
                                "valor": valor,
                                "time_origem": origem
                            }).execute()
                            st.success(f"✅ {nome} adicionado ao elenco do {nome_adv}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao adicionar jogador: {e}")
                    else:
                        st.warning("Preencha todos os campos corretamente.")

        # 🎯 Exibir elenco do time adversário
        elenco_adv = supabase.table("elenco").select("*").eq("id_time", id_time_adv).execute().data

        if not elenco_adv:
            st.info("Nenhum jogador disponível neste time.")
        else:
            for jogador in elenco_adv:
                st.markdown("---")
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"**👤 Nome:** {jogador.get('nome', '-')}")
                    st.markdown(f"**🌍 Nacionalidade:** {jogador.get('nacionalidade', '-')}")
                    st.markdown(f"**🎯 Overall:** {jogador.get('overall', '-')}")
                    st.markdown(f"**🏷️ Origem:** {jogador.get('time_origem', '-')}")
                with col2:
                    valor_jogador = jogador.get("valor", 0)
                    st.markdown(f"**💰 Valor:** R$ {valor_jogador:,.0f}")

                    proposta_valor = st.number_input(
                        "💸 Proposta (R$)",
                        min_value=valor_jogador,
                        step=500_000,
                        value=valor_jogador,
                        key=f"input_valor_{jogador['id']}"
                    )

                    if st.button("📩 Enviar Proposta", key=f"btn_proposta_{jogador['id']}"):
                        try:
                            proposta = {
                                "id_time_origem": id_time,
                                "id_time_destino": id_time_adv,
                                "jogador_desejado": jogador["nome"],
                                "id_jogador": jogador["id"],
                                "jogador_oferecido": [],
                                "valor_oferecido": proposta_valor,
                                "tipo_negociacao": "Somente Dinheiro",
                                "status": "pendente",
                                "data": datetime.utcnow().isoformat()
                            }
                            resp = supabase.table("negociacoes").insert(proposta).execute()
                            if resp and resp.data:
                                st.success("✅ Proposta enviada com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao enviar proposta: resposta vazia.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
