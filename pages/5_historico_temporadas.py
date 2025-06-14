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

# 🔄 Função para buscar dados do histórico
def buscar_historico():
    res = supabase.table("historico_temporadas").select("*").order("data", desc=True).execute()
    return res.data if res.data else []

# 📥 Carrega dados
dados = buscar_historico()

# 🚫 Caso não haja registros
if not dados:
    st.info("Nenhuma temporada registrada ainda.")
    st.stop()

# 📊 Separa por tipo
ligas = [item for item in dados if item.get("tipo") == "liga"]
copas = [item for item in dados if item.get("tipo") == "copa"]

# 🎨 Função para exibir cards
def exibir_card_temporada(item):
    tipo = "🏆 Liga" if item["tipo"] == "liga" else "🥇 Copa"
    nome = item.get("campeao", "Desconhecido")
    melhor_ataque = item.get("melhor_ataque", "N/A")
    melhor_defesa = item.get("melhor_defesa", "N/A")
    data = pd.to_datetime(item["data"]).strftime("%d/%m/%Y")

    st.markdown(f"""
        <div style='background:#f0f0f0;padding:15px;border-radius:10px;margin-bottom:15px;
                    box-shadow:0 0 6px rgba(0,0,0,0.1); color:#000'>
            <h4>{tipo} - {data}</h4>
            <p><strong>🏅 Campeão:</strong> {nome}</p>
            <p><strong>🔥 Melhor Ataque:</strong> {melhor_ataque}</p>
            <p><strong>🧱 Melhor Defesa:</strong> {melhor_defesa}</p>
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
