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

# 🔎 Buscar todos jogadores da base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

if not jogadores:
    st.info("Nenhum jogador encontrado.")
    st.stop()

df = pd.DataFrame(jogadores)

# 🔁 Mostrar jogadores
for row in df.itertuples():
    col1, col2, col3, col4, col5 = st.columns([2, 1.2, 1.2, 2, 1.5])

    # 🔘 Status por bolinha
    if row.destino == "nenhum":
        status = "🟢"
    elif row.destino == "leilao":
        status = "🟡"
    elif row.destino == "mercado":
        status = "🔵"
    else:
        status = "🔴"

    with col1:
        st.markdown(f"**{status} {row.nome}**")
        st.caption(f"{row.posicao} | Overall: {row.overall} | R$ {row.valor:,.0f}".replace(",", "."))
        if getattr(row, "sofifa_id", None):
            st.markdown(f"[📎 Ficha Técnica](https://sofifa.com/player/{row.sofifa_id}/)", unsafe_allow_html=True)
        else:
            st.markdown("📎 Ficha Técnica não disponível")

    with col2:
        if st.button("📤 Mandar Mercado", key=f"mercado_{row.id}"):
            ja_no_mercado = supabase.table("mercado_transferencias").select("id").eq("id_jogador_base", row.id).execute()
            if ja_no_mercado.data:
                st.warning("⚠️ Já está no mercado.")
            else:
                supabase.table("mercado_transferencias").insert({
                    "id_jogador_base": row.id,
                    "nome": row.nome,
                    "posicao": row.posicao,
                    "overall": row.overall,
                    "valor": row.valor,
                    "imagem_url": row.imagem_url,
                    "nacionalidade": row.nacionalidade,
                    "clube_original": row.clube_original
                }).execute()
                supabase.table("jogadores_base").update({"destino": "mercado"}).eq("id", row.id).execute()
                st.success(f"{row.nome} enviado para o mercado.")
                st.experimental_rerun()

    with col3:
        if st.button("🔨 Mandar Leilão", key=f"leilao_{row.id}"):
            ja_na_fila = supabase.table("fila_leilao").select("id").eq("id_jogador_base", row.id).execute()
            if ja_na_fila.data:
                st.warning("⚠️ Já está na fila do leilão.")
            else:
                supabase.table("fila_leilao").insert({
                    "id_jogador_base": row.id,
                    "nome": row.nome,
                    "posicao": row.posicao,
                    "overall": row.overall,
                    "valor": row.valor,
                    "imagem_url": row.imagem_url,
                    "status": "aguardando"
                }).execute()
                supabase.table("jogadores_base").update({"destino": "leilao"}).eq("id", row.id).execute()
                st.success(f"{row.nome} enviado à fila de leilão.")
                st.experimental_rerun()

    with col4:
        st.markdown("---")

    with col5:
        if row.imagem_url:
            st.image(row.imagem_url, width=70)
