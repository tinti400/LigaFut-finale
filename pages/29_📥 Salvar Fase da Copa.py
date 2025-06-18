# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Registrar Fase Alcançada na Copa - LigaFut")

# ✅ Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🏆 Fases possíveis
fases = [
    "grupo", "classificado", "oitavas",
    "quartas", "semi", "vice", "campeao"
]

# 🔍 Buscar dados dos participantes da copa
res_copa = supabase.table("copa").select("id", "id_time", "fase_alcancada").execute()
copa_data = res_copa.data

if not copa_data:
    st.warning("⚠️ Nenhum time participante da Copa foi encontrado.")
    st.stop()

# 🔍 Buscar nomes dos times
ids_times = [item["id_time"] for item in copa_data]
res_times = supabase.table("times").select("id", "nome").in_("id", ids_times).execute()
times_map = {t["id"]: t["nome"] for t in res_times.data}

# 📋 Interface para selecionar fase para cada time
st.markdown("### 🏆 Selecione a fase alcançada por cada time da Copa:")

fase_dict = {}
for item in copa_data:
    id_time = item["id_time"]
    nome = times_map.get(id_time, "Nome Desconhecido")
    fase_atual = item.get("fase_alcancada", "grupo")
    fase = st.selectbox(f"Time: {nome}", fases, index=fases.index(fase_atual), key=f"fase_{id_time}")
    fase_dict[id_time] = {"nome": nome, "fase": fase}

# 🔎 Prévia das seleções
df_preview = pd.DataFrame([
    {"Time": dados["nome"], "Fase Selecionada": dados["fase"]}
    for dados in fase_dict.values()
])

st.markdown("### 🔎 Prévia das Fases Selecionadas")
st.dataframe(df_preview, use_container_width=True)

# 💾 Botão para salvar no banco
if st.button("💾 Salvar Fases da Copa"):
    try:
        for item in copa_data:
            id_time = item["id_time"]
            id_registro = item["id"]
            nova_fase = fase_dict[id_time]["fase"]

            supabase.table("copa").update({"fase_alcancada": nova_fase}).eq("id", id_registro).execute()

        st.success("✅ Fases atualizadas com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {e}")





