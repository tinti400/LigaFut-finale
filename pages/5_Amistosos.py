# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🤝 Amistosos - LigaFut", layout="wide")
st.title("🤝 Amistosos de Pré-Temporada")

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu time")

# 🔄 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo").execute()
todos_times = res_times.data or []
mapa_times = {t["id"]: t for t in todos_times}

# 🔄 Buscar amistosos enviados
def buscar_convites_enviados():
    res = supabase.table("amistosos").select("*").eq("time_convidante", id_time).execute()
    return res.data or []

convites_enviados = buscar_convites_enviados()
times_ja_convidados = [item["time_convidado"] for item in convites_enviados if item["status"] != "recusado"]
limite_alcancado = len(times_ja_convidados) >= 3

st.markdown(f"🔄 {len(times_ja_convidados)} de 3 amistosos enviados.")

# 📌 Selectbox no lugar de abas
aba = st.selectbox("📂 Escolha a visualização", ["📨 Convidar adversário", "📥 Convites recebidos", "📤 Convites enviados"])

# 📨 Convidar adversário
if aba == "📨 Convidar adversário":
    if limite_alcancado:
        st.warning("Você já enviou o máximo de 3 convites de amistoso.")
    else:
        times_disponiveis = [t for t in todos_times if t["id"] != id_time and t["id"] not in times_ja_convidados]
        nomes_disponiveis = {t["nome"]: t["id"] for t in times_disponiveis}

        if nomes_disponiveis:
            adversario_nome = st.selectbox("Escolha o adversário", list(nomes_disponiveis.keys()))
            valor = st.number_input("Valor da aposta (em milhões)", min_value=1.0, max_value=100.0, step=1.0)

            if st.button("Enviar convite"):
                time_convidado_id = nomes_disponiveis[adversario_nome]
                supabase.table("amistosos").insert({
                    "time_convidante": id_time,
                    "time_convidado": time_convidado_id,
                    "valor_aposta": valor,
                    "status": "pendente"
                }).execute()
                st.success(f"Convite enviado para {adversario_nome} com aposta de R${valor:.2f} milhões.")
                st.experimental_rerun()
        else:
            st.info("Nenhum adversário disponível para convite no momento.")

# 📥 Convites recebidos
elif aba == "📥 Convites recebidos":
    res_recebidos = supabase.table("amistosos").select("*").eq("time_convidado", id_time).eq("status", "pendente").execute()
    amistosos_recebidos = res_recebidos.data or []

    if not amistosos_recebidos:
        st.info("Você não recebeu nenhum convite.")
    else:
        for item in amistosos_recebidos:
            id_amistoso = item["id"]
            valor = item["valor_aposta"]
            time_a_id = item["time_convidante"]
            time_b_id = item["time_convidado"]

            convidante = mapa_times.get(time_a_id, {"nome": "Desconhecido"})["nome"]

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{convidante}** convidou você para um amistoso apostando **R${valor:.2f} milhões**")
            with col2:
                if st.button("✅ Aceitar", key=f"aceitar_{id_amistoso}"):
                    saldo_a = mapa_times.get(time_a_id, {}).get("saldo", 0)
                    saldo_b = mapa_times.get(time_b_id, {}).get("saldo", 0)

                    if saldo_a >= valor and saldo_b >= valor:
                        # Debitar dos dois times
                        supabase.table("times").update({"saldo": saldo_a - valor}).eq("id", time_a_id).execute()
                        supabase.table("times").update({"saldo": saldo_b - valor}).eq("id", time_b_id).execute()

                        registrar_movimentacao(supabase, time_a_id, -valor, "Aposta amistoso")
                        registrar_movimentacao(supabase, time_b_id, -valor, "Aposta amistoso")

                        supabase.table("amistosos").update({"status": "aceito"}).eq("id", id_amistoso).execute()
                        st.success("Amistoso aceito! Apostas debitadas dos dois clubes.")
                        st.experimental_rerun()
                    else:
                        st.error("Um dos clubes não tem saldo suficiente para aceitar a aposta.")

                if st.button("❌ Recusar", key=f"recusar_{id_amistoso}"):
                    supabase.table("amistosos").update({"status": "recusado"}).eq("id", id_amistoso).execute()
                    st.info("Convite recusado.")
                    st.experimental_rerun()

# 📤 Convites enviados
elif aba == "📤 Convites enviados":
    for item in convites_enviados:
        convidado = mapa_times.get(item["time_convidado"], {"nome": "Desconhecido"})["nome"]
        valor = item["valor_aposta"]
        status = item["status"]
        st.markdown(f"- Para **{convidado}** | 💰 R${valor:.2f} milhões | Status: `{status}`")




