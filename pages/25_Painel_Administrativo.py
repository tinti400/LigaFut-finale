# 25_Painel_Administrativo.py

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="🛠️ Painel Administrativo", layout="centered")
st.title("🛠️ Painel Administrativo - LigaFut")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.subheader("⚖️ Aplicar Punição de Perda de Pontos")

# 📥 Buscar times
try:
    res = supabase.table("times").select("id, nome").execute()
    times = res.data
except Exception as e:
    st.error(f"Erro ao carregar times: {e}")
    st.stop()

if not times:
    st.warning("Nenhum time encontrado.")
    st.stop()

# 📌 Lista de times
nomes_times = {t["nome"]: t["id"] for t in times}
nome_escolhido = st.selectbox("Selecione o time para punir", list(nomes_times.keys()))
id_time = nomes_times[nome_escolhido]

# 🔢 Pontos a retirar
pontos_retirar = st.number_input("Quantos pontos deseja retirar?", min_value=1, max_value=100, step=1)

# 📝 Motivo (opcional)
motivo = st.text_input("Motivo da punição (opcional)").strip()

# ✅ Aplicar punição
if st.button("✅ Aplicar Punição"):
    try:
        supabase.table("punicoes").insert({
            "id_time": id_time,
            "nome_time": nome_escolhido,
            "pontos_retirados": pontos_retirar,
            "motivo": motivo or "-"
        }).execute()

        st.success(f"Punição aplicada com sucesso: -{pontos_retirar} ponto(s) para o time {nome_escolhido}.")
        st.info("⚠️ A punição será refletida automaticamente na tabela de classificação.")

    except Exception as e:
        st.error(f"Erro ao aplicar punição: {e}")

