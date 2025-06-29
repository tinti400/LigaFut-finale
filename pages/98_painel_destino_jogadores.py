# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Definir Destino dos Jogadores", layout="wide")
st.title("🎯 Painel de Destino dos Jogadores")

# 🔎 Buscar jogadores com destino 'nenhum'
res = supabase.table("jogadores_base").select("*").eq("destino", "nenhum").execute()
jogadores = res.data

if not jogadores:
    st.info("✅ Todos os jogadores já têm destino definido.")
    st.stop()

# 🔁 Mostrar em tabela com opções de destino
df = pd.DataFrame(jogadores)

for i, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 2])

    with col1:
        st.markdown(f"**{row['nome']}**")
        st.caption(f"{row['posicao']} | Overall: {row['overall']} | R$ {row['valor']:,.0f}".replace(",", "."))

    with col2:
        if st.button("📤 Mercado", key=f"mercado_{row['id']}"):
            supabase.table("jogadores_base").update({"destino": "mercado"}).eq("id", row["id"]).execute()
            st.success(f"{row['nome']} enviado para o mercado.")
            st.experimental_rerun()

    with col3:
        if st.button("🔨 Leilão", key=f"leilao_{row['id']}"):
            supabase.table("jogadores_base").update({"destino": "leilao"}).eq("id", row["id"]).execute()
            st.success(f"{row['nome']} enviado para o leilão.")
            st.experimental_rerun()

    with col4:
        with st.expander("⚽ Time"):
            novo_destino = st.text_input(f"ID do time para {row['nome']}", key=f"time_{row['id']}")
            if st.button("✅ Atribuir", key=f"atribuir_{row['id']}"):
                if novo_destino.strip() != "":
                    supabase.table("jogadores_base").update({"destino": novo_destino}).eq("id", row["id"]).execute()
                    st.success(f"{row['nome']} atribuído ao time: {novo_destino}")
                    st.experimental_rerun()

    with col5:
        if row.get("imagem_url"):
            st.image(row["imagem_url"], width=60)
