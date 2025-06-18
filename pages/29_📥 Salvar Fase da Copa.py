# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Atualizar Fase Alcançada na Copa")

# 🔍 Buscar times que participaram da copa
res_copa = supabase.table("copa").select("id, id_time, fase_alcancada").execute()
dados_copa = res_copa.data

if not dados_copa:
    st.warning("Nenhum time participante encontrado na tabela 'copa'.")
    st.stop()

# Buscar todos os nomes dos times
ids_times = [item["id_time"] for item in dados_copa]
res_times = supabase.table("times").select("id", "nome").in_("id", ids_times).execute()
nomes = {item["id"]: item["nome"] for item in res_times.data}

# Construir DataFrame para exibição e edição
dados_organizados = []
for registro in dados_copa:
    id_time = registro["id_time"]
    nome_time = nomes.get(id_time, "Desconhecido")
    fase = registro.get("fase_alcancada", "")
    dados_organizados.append({"id": registro["id"], "id_time": id_time, "nome": nome_time, "fase": fase})

df = pd.DataFrame(dados_organizados)

# Interface de edição
st.dataframe(df[["nome", "fase"]], use_container_width=True)

# Fases possíveis para seleção
fases_possiveis = [
    "grupos", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"
]

st.markdown("### ✏️ Atualizar fases manualmente")

for i, row in df.iterrows():
    nova_fase = st.selectbox(f"🔄 {row['nome']}", fases_possiveis, index=fases_possiveis.index(row["fase"]) if row["fase"] in fases_possiveis else 0, key=f"fase_{i}")
    df.at[i, "fase"] = nova_fase

if st.button("💾 Salvar Fases da Copa"):
    for i, row in df.iterrows():
        supabase.table("copa").update({
            "fase_alcancada": row["fase"]
        }).eq("id", row["id"]).execute()
    st.success("✅ Fases atualizadas com sucesso!")





