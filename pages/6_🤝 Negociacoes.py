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
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("🤝 Negociações entre Clubes")
st.markdown("---")

# 📋 Lista de times (exceto o próprio)
times = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
nomes_times = {time["id"]: time["nome"] for time in times}
time_alvo = st.selectbox("Escolha o clube com quem deseja negociar:", options=list(nomes_times.keys()), format_func=lambda x: nomes_times[x])

# 📊 Exibir elenco do time alvo
if time_alvo:
    elenco = supabase.table("elenco").select("*").eq("id_time", time_alvo).execute().data
    st.subheader(f"Elenco do {nomes_times[time_alvo]}")
    for jogador in elenco:
        with st.expander(f'{jogador["nome"]} - {jogador["posicao"]} - Overall: {jogador["overall"]}'):
            st.write(f"💰 Valor: R$ {jogador['valor']:,}".replace(",", "."))
            st.write("✉️ Enviar proposta de compra")

            valor_oferecido = st.number_input("Valor oferecido (R$)", min_value=0, step=100000, key=f"valor_{jogador['nome']}_{jogador['posicao']}")
            if st.button("Enviar proposta", key=f"btn_{jogador['nome']}_{jogador['posicao']}"):
                proposta = {
                    "id": str(uuid.uuid4()),  # ✅ Gera UUID válido
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

