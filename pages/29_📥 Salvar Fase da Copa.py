# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Registrar Fase Alcançada na Copa")

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time_logado = st.session_state["id_time"]
nome_time_logado = st.session_state["nome_time"]

# 🔄 Buscar todos os times
res_times = supabase.table("times").select("id", "nome").execute()
times = res_times.data if res_times.data else []

# Criar mapa de nomes
mapa_nomes = {t["id"]: t["nome"] for t in times}

# Fases disponíveis
fases = [
    "grupo", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"
]

# Interface de seleção
st.markdown("### 🏆 Selecione a fase da copa para cada time:")

dados = []
for time in times:
    id_time = time["id"]
    nome_time = time["nome"]

    # Verificar se já tem registro
    res = supabase.table("copa").select("id_time").eq("id_time", id_time).execute()
    ja_salvo = bool(res.data)

    fase = st.selectbox(
        f"{nome_time}",
        options=[""] + fases,
        key=f"fase_{id_time}"
    )

    dados.append({
        "id_time": id_time,
        "nome": nome_time,
        "fase": fase,
        "ja_salvo": ja_salvo
    })

# Tabela para conferência
df = pd.DataFrame([d for d in dados if d["fase"]])
if not df.empty:
    st.markdown("### 🔎 Pré-visualização das fases que serão salvas:")
    st.dataframe(df[["nome", "fase"]], use_container_width=True)

# Botão de confirmação
if st.button("💾 Salvar Fases da Copa"):
    for d in dados:
        if not d["fase"]:
            continue
        if d["ja_salvo"]:
            supabase.table("copa").update({"fase_alcancada": d["fase"]}).eq("id_time", d["id_time"]).execute()
        else:
            supabase.table("copa").insert({"id_time": d["id_time"], "fase_alcancada": d["fase"]}).execute()

    st.success("✅ Fases da copa registradas com sucesso!")
    st.rerun()



