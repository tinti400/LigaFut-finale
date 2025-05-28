# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Histórico de Campeões", layout="wide")
st.title("📜 Histórico de Campeões da Copa LigaFut")

# 📊 Buscar dados dos campeões
try:
    campeoes = supabase.table("campeoes_copa").select("*").order("numero").execute().data
    times_data = supabase.table("times").select("id", "logo").execute().data
    logo_map = {t["id"]: t.get("logo", "") for t in times_data}
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    campeoes = []

# 🧮 Agrupar títulos por time
from collections import Counter
contagem = Counter(c["nome_time"] for c in campeoes)

st.subheader("🥇 Ranking de Títulos")
for time, titulos in contagem.most_common():
    st.markdown(f"- **{time}**: {titulos} título{'s' if titulos > 1 else ''}")

st.markdown("---")

# 🖼️ Exibir histórico completo
if not campeoes:
    st.info("Nenhum campeão registrado ainda.")
else:
    for c in campeoes:
        logo = logo_map.get(c["id_time"], "")
        try:
            data = datetime.strptime(c["data_titulo"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            data = datetime.now()
        col1, col2 = st.columns([1, 8])
        with col1:
            if logo:
                st.image(logo, width=80)
        with col2:
            st.markdown(f"### 🏆 {c['numero']}ª Copa - **{c['nome_time']}**")
            st.markdown(f"<span style='color: gray;'>Data: {data.strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
    st.markdown("---")
