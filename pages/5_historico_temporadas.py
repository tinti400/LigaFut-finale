# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏅 Histórico de Temporadas", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏅 Histórico de Temporadas LigaFut</h1><hr>", unsafe_allow_html=True)

# 🔄 Buscar dados do histórico
def buscar_historico():
    res = supabase.table("historico_temporadas").select("*").order("data_finalizacao", desc=True).execute()
    return res.data if res.data else []

# 📥 Carrega dados
dados = buscar_historico()

# 🚫 Nenhum registro
if not dados:
    st.info("Nenhuma temporada registrada ainda.")
    st.stop()

# 📊 Separa por tipo
ligas = [item for item in dados if item.get("tipo") == "liga"]
copas = [item for item in dados if item.get("tipo") == "copa"]

# 🎨 Card
def exibir_card_temporada(item):
    tipo = "🏆 Liga" if item.get("tipo") == "liga" else "🥇 Copa"
    campeao = item.get("campeao", "Desconhecido")
    ataque = item.get("melhor_ataque", "N/A")
    defesa = item.get("melhor_defesa", "N/A")
    divisao = item.get("divisao", "")
    temporada = item.get("temporada", "?")
    data = pd.to_datetime(item.get("data_finalizacao")).strftime("%d/%m/%Y")

    st.markdown(f"""
        <div style='background:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:15px;
                    box-shadow:0 0 6px rgba(0,0,0,0.1); color:#000'>
            <h4>{tipo} | Temporada {temporada} - {divisao}</h4>
            <p><strong>📅 Data:</strong> {data}</p>
            <p><strong>🏅 Campeão:</strong> {campeao}</p>
            <p><strong>🔥 Melhor Ataque:</strong> {ataque}</p>
            <p><strong>🧱 Melhor Defesa:</strong> {defesa}</p>
        </div>
    """, unsafe_allow_html=True)

# 🗂 Tabs para Copa e Liga
tab1, tab2 = st.tabs(["🥇 Copas", "🏆 Ligas"])

with tab1:
    st.subheader("🥇 Campeões da Copa")
    for item in copas:
        exibir_card_temporada(item)

with tab2:
    st.subheader("🏆 Campeões da Liga")
    for item in ligas:
        exibir_card_temporada(item)
