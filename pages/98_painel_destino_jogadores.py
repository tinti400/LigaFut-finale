# 98_painel_destino_jogadores.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from PIL import Image

st.set_page_config(page_title="🎯 Painel de Destino dos Jogadores", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🎯 Painel de Destino dos Jogadores")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔍 Buscar jogadores da base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

# 📌 Cores por destino
cores_destino = {
    "disponivel": "🟢",
    "mercado": "🔵",
    "leilao": "🟡",
    "atribuido": "🔴"
}

# 🧩 Exibição
for jogador in jogadores:
    destino = jogador.get("destino", "disponivel")
    cor = cores_destino.get(destino, "⚪")
    st.markdown("---")
    cols = st.columns([0.5, 3, 2, 2, 2, 2])

    # 📷 Imagem do jogador
    try:
        if jogador.get("imagem_url"):
            cols[0].image(jogador["imagem_url"], width=80)
        else:
            cols[0].markdown("❌")
    except:
        cols[0].markdown("❌")

    # 📛 Nome e posição
    nome = jogador["nome"]
    posicao = jogador.get("posicao", "")
    overall = jogador.get("overall", "")
    valor = jogador.get("valor", 0)
    cols[1].markdown(f"{cor} **{nome}**")
    cols[1].markdown(f"`{posicao}` | Overall: {overall} | R$ {valor:,.0f}".replace(",", "."))

    # 📎 Link SoFIFA
    if jogador.get("sofifa_id"):
        cols[2].markdown(f"[📎 Ficha Técnica](https://sofifa.com/player/{jogador['sofifa_id']})")
    else:
        cols[2].markdown("Ficha Técnica não disponível")

    # 🛒 Botão Mercado
    if cols[3].button("🛒 Mandar Mercado", key=f"mercado_{jogador['id']}"):
        supabase.table("mercado_transferencias").insert({
            "nome": nome,
            "posicao": posicao,
            "overall": overall,
            "valor": valor,
            "imagem_url": jogador.get("imagem_url", "")
        }).execute()
        supabase.table("jogadores_base").update({"destino": "mercado"}).eq("id", jogador["id"]).execute()
        st.success(f"{nome} enviado ao mercado com sucesso!")
        st.experimental_rerun()

    # 📢 Botão Leilão
    if cols[4].button("📢 Mandar Leilão", key=f"leilao_{jogador['id']}"):
        supabase.table("fila_leilao").insert({
            "nome": nome,
            "posicao": posicao,
            "overall": overall,
            "valor": valor,
            "imagem_url": jogador.get("imagem_url", ""),
            "status": "aguardando",
            "id_jogador_base": jogador["id"]
        }).execute()
        supabase.table("jogadores_base").update({"destino": "leilao"}).eq("id", jogador["id"]).execute()
        st.success(f"{nome} enviado à fila do leilão para validação do admin.")
        st.experimental_rerun()

    # ✅ Histórico visual
    cols[5].markdown(f"Status: {cor}")

