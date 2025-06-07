# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import uuid
from utils import verificar_login

st.set_page_config(page_title="Negociações entre clubes", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if not verificar_login():
    st.stop()

# 📌 Dados do time logado
id_time = st.session_state.get("id_time")
nome_time = st.session_state.get("nome_time")

if not id_time or not nome_time:
    st.error("❌ Erro: Informações do time não encontradas.")
    st.stop()

st.title("🤝 Negociações entre Clubes")
st.markdown("---")

# 📋 Lista de times (exceto o próprio)
try:
    res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
    times = res_times.data
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

if not times:
    st.warning("⚠️ Nenhum outro clube disponível para negociar.")
    st.stop()

nomes_times = {t["id"]: t["nome"] for t in times}
time_alvo = st.selectbox("Escolha o clube para negociar:", options=list(nomes_times.keys()), format_func=lambda x: nomes_times[x])

# 📊 Buscar elenco do time alvo
try:
    elenco_res = supabase.table("elenco").select("*").eq("id_time", time_alvo).execute()
    elenco = elenco_res.data
except Exception as e:
    st.error(f"Erro ao buscar elenco do time alvo: {e}")
    elenco = []

if not elenco:
    st.info(f"O time {nomes_times[time_alvo]} ainda não possui jogadores cadastrados.")
else:
    st.subheader(f"Elenco do {nomes_times[time_alvo]}")
    for jogador in elenco:
        key_suffix = f'{jogador["id"]}_{jogador["nome"]}'

        with st.expander(f'{jogador["nome"]} - {jogador["posicao"]} - Overall {jogador["overall"]}'):
            st.markdown(f'💰 **Valor atual:** R$ {jogador["valor"]:,}'.replace(",", "."))

            valor_oferecido = st.number_input("💸 Valor da proposta (R$)", min_value=0, step=100000, key=f"valor_{key_suffix}")

            if st.button("✉️ Enviar proposta", key=f"enviar_{key_suffix}"):
                proposta = {
                    "id": str(uuid.uuid4()),
                    "destino_id": time_alvo,
                    "id_time_origem": id_time,
                    "id_time_alvo": time_alvo,
                    "nome_time_origem": nome_time,
                    "nome_time_alvo": nomes_times[time_alvo],
                    "jogador_nome": jogador["nome"],
                    "jogador_posicao": jogador["posicao"],
                    "jogador_overall": jogador["overall"],
                    "jogador_valor": jogador["valor"],
                    "valor_oferecido": int(valor_oferecido),
                    "status": "pendente"
                }

                try:
                    supabase.table("propostas").insert(proposta).execute()
                    st.success(f"✅ Proposta enviada para {nomes_times[time_alvo]} por {jogador['nome']}.")
                except Exception as e:
                    st.error(f"Erro ao enviar proposta: {e}")


