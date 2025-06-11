# 25_Painel_Administrativo.py

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="🛠️ Painel Administrativo", layout="centered")
st.title("🛠️ Painel Administrativo - LigaFut")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.subheader("⚖️ Aplicar Punição de Perda de Pontos")

# 📥 Buscar times
res = supabase.table("times").select("id, nome, pontos").execute()
times = res.data

if not times:
    st.warning("Nenhum time encontrado.")
    st.stop()

# 📌 Selecionar time
nomes_times = {time["nome"]: time["id"] for time in times}
nome_escolhido = st.selectbox("Selecione o time para punir", list(nomes_times.keys()))
id_time = nomes_times[nome_escolhido]

# 🔢 Pontos a retirar
pontos_retirar = st.number_input("Quantos pontos deseja retirar?", min_value=1, max_value=100, step=1)

# 📝 Motivo da punição
motivo = st.text_input("Motivo da punição (opcional)")

if st.button("✅ Aplicar Punição"):
    # Verificar pontos atuais
    pontos_atual = next((t["pontos"] for t in times if t["id"] == id_time), 0)
    novos_pontos = max(pontos_atual - pontos_retirar, 0)  # Evita valor negativo

    # Atualizar pontos
    supabase.table("times").update({"pontos": novos_pontos}).eq("id", id_time).execute()

    # Registrar punição (opcional)
    supabase.table("punicoes").insert({
        "id_time": id_time,
        "nome_time": nome_escolhido,
        "pontos_retirados": pontos_retirar,
        "motivo": motivo
    }).execute()

    st.success(f"Punição aplicada: {pontos_retirar} ponto(s) retirado(s) do time {nome_escolhido}.")

    st.info("✅ Registro de punição salvo com sucesso.")
