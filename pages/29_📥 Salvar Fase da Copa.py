# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Atualizar Fase Alcançada na Copa")

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🔄 Buscar todos os times
res = supabase.table("times").select("id", "nome").order("nome").execute()
times = res.data

# Lista de fases
fases = ["grupo", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"]

# Cria interface para seleção de fase de cada time
df = pd.DataFrame(times)
df["fase"] = ""

for i, row in df.iterrows():
    df.at[i, "fase"] = st.selectbox(f"🎯 Fase da Copa - {row['nome']}", [""] + fases, key=f"fase_{i}")

# 🔍 Prévia com validação segura
if df.empty or "nome" not in df.columns or "fase" not in df.columns:
    st.info("Nenhuma fase selecionada ou dados incompletos para exibição.")
else:
    st.markdown("### 🔎 Pré-visualização das fases que serão salvas:")
    st.dataframe(df[["nome", "fase"]], use_container_width=True)

# Botão para salvar fases
if st.button("💾 Salvar Fases da Copa"):
    total_salvos = 0
    for _, row in df.iterrows():
        fase = row["fase"]
        if fase and fase in fases:
            id_time = row["id"]

            # Verifica se o time já tem registro
            res = supabase.table("copa").select("id").eq("id_time", id_time).execute()
            data = res.data

            if data:
                id_registro = data[0]["id"]
                supabase.table("copa").update({"fase_alcancada": fase}).eq("id", id_registro).execute()
            else:
                supabase.table("copa").insert({"id_time": id_time, "fase_alcancada": fase}).execute()

            total_salvos += 1

    st.success(f"✅ Fases salvas com sucesso para {total_salvos} times.")




