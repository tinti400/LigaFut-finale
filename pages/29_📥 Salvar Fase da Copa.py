# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="centered")
st.title("🏆 Atualizar Fase Alcançada na Copa")

# 🚫 Verifica login
if "usuario_id" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔄 Buscar todos os times
res = supabase.table("times").select("id", "nome").execute()
times = res.data if res.data else []

# 🔄 Buscar fases atuais da copa
res_fase = supabase.table("copa").select("id_time", "fase_alcancada").execute()
fase_por_time = {item["id_time"]: item["fase_alcancada"] for item in res_fase.data} if res_fase.data else {}

# 🔁 Interface de atualização
st.subheader("📝 Atualizar fase da copa por time")
fase_opcoes = list({
    "grupo", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"
})

with st.form("form_fases"):
    atualizacoes = {}
    for time in times:
        id_time = time["id"]
        nome = time["nome"]
        fase_atual = fase_por_time.get(id_time, "grupo")
        nova_fase = st.selectbox(f"🛡️ {nome}", fase_opcoes, index=fase_opcoes.index(fase_atual), key=f"fase_{id_time}")
        atualizacoes[id_time] = nova_fase

    submitted = st.form_submit_button("💾 Salvar fases")
    if submitted:
        for id_time, fase in atualizacoes.items():
            res = supabase.table("copa").select("id").eq("id_time", id_time).execute()
            if res.data:
                supabase.table("copa").update({"fase_alcancada": fase}).eq("id_time", id_time).execute()
            else:
                supabase.table("copa").insert({"id_time": id_time, "fase_alcancada": fase}).execute()
        st.success("✅ Fases salvas com sucesso!")

# 👁️ Visualização com nomes dos times + Exportar CSV
mostrar = st.checkbox("👁️ Ver resumo com nomes dos times")
if mostrar:
    res_times = supabase.table("times").select("id", "nome").execute()
    mapa_nomes = {t["id"]: t["nome"] for t in res_times.data} if res_times.data else {}

    dados_visual = []
    for id_time, fase in fase_por_time.items():
        nome = mapa_nomes.get(id_time, "❓ Desconhecido")
        dados_visual.append({
            "Time": nome,
            "Fase Alcançada": fase.capitalize()
        })

    if dados_visual:
        df = pd.DataFrame(dados_visual).sort_values("Fase Alcançada", ascending=False)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name="fase_copa_times.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ Nenhum dado foi encontrado para exibição.")


