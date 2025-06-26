# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import re

st.set_page_config(page_title="🛠️ Corrigir Imagens do Elenco", layout="wide")
st.title("🛠️ Correção de Imagens do Elenco")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica se é admin
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito apenas para administradores.")
    st.stop()

# 🔄 Função para corrigir imagens do elenco
def corrigir_imagens():
    resultado = []
    res = supabase.table("elenco").select("id", "nome", "imagem_url").execute()
    jogadores = res.data

    for jogador in jogadores:
        id_jogador = jogador["id"]
        nome = jogador.get("nome", "Sem nome")
        imagem_url = jogador.get("imagem_url") or ""

        if not imagem_url or ".svg" in imagem_url or "player_0" in imagem_url:
            match = re.search(r'/players/(\d{3})/(\d{3})/', imagem_url)

            if match:
                parte1, parte2 = match.groups()
                nova_url = f"https://cdn.sofifa.net/players/{parte1}/{parte2}/25.png"
            else:
                nova_url = "https://via.placeholder.com/80x80.png?text=Sem+Foto"

            supabase.table("elenco").update({"imagem_url": nova_url}).eq("id", id_jogador).execute()
            resultado.append(f"✅ {nome} atualizado para: {nova_url}")
        else:
            resultado.append(f"🔒 {nome} já possui imagem válida.")

    return resultado

# 🧠 Botão de correção
if st.button("🔁 Corrigir Imagens Quebradas"):
    with st.spinner("Corrigindo imagens..."):
        resultado = corrigir_imagens()
        st.success("Correção concluída!")
        for linha in resultado:
            st.write(linha)
