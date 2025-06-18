# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Atualizar Fase Alcançada na Copa")

# ✅ Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔍 Buscar participantes da Copa
res_copa = supabase.table("copa").select("id, id_time, fase_alcancada").execute()
dados_copa = res_copa.data

if not dados_copa:
    st.warning("⚠️ Nenhum time participante encontrado na tabela 'copa'.")
    st.stop()

# 🔍 Buscar nomes dos times
ids_times = [item["id_time"] for item in dados_copa]
res_times = supabase.table("times").select("id", "nome").in_("id", ids_times).execute()
nomes_map = {t["id"]: t["nome"] for t in res_times.data}

# 🎯 Fases possíveis
fases_possiveis = ["grupos", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"]

# 📋 Montar dataframe editável
linhas = []
for item in dados_copa:
    id_time = item["id_time"]
    fase_atual = item.get("fase_alcancada", "grupos")
    nome = nomes_map.get(id_time, "Desconhecido")
    linhas.append({
        "id": item["id"],
        "id_time": id_time,
        "nome": nome,
        "fase": fase_atual if fase_atual in fases_possiveis else "grupos"
    })

df = pd.DataFrame(linhas)

# ✅ Exibição segura
if not df.empty and all(col in df.columns for col in ["nome", "fase"]):
    st.markdown("### 🔎 Prévia das Fases Selecionadas")
    st.dataframe(df[["nome", "fase"]], use_container_width=True)
else:
    st.info("⚠️ Nenhum dado válido para exibir.")

# ✏️ Interface para selecionar fase manualmente
st.markdown("### ✏️ Atualize as fases abaixo:")

for i, row in df.iterrows():
    nova_fase = st.selectbox(
        f"{row['nome']}", 
        fases_possiveis, 
        index=fases_possiveis.index(row["fase"]), 
        key=f"fase_{row['id_time']}"
    )
    df.at[i, "fase"] = nova_fase

# 💾 Salvar no banco
if st.button("💾 Salvar Fases da Copa"):
    for _, row in df.iterrows():
        supabase.table("copa").update({
            "fase_alcancada": row["fase"]
        }).eq("id", row["id"]).execute()
    st.success("✅ Fases atualizadas com sucesso!")






