# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="👑 Admin - Divisões", layout="wide")
st.markdown("## 👑 Administração de Divisões dos Times")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito a administradores.")
    st.stop()

# 🔍 Buscar todos usuários com time vinculado
usuarios = supabase.table("usuarios").select("id, usuario, time_id, Divisão").execute().data
times = supabase.table("times").select("id, nome").execute().data
mapa_times = {t["id"]: t["nome"] for t in times}

# 📋 Mostrar tabela de usuários
st.markdown("### 👥 Lista de Usuários com Times")
divisoes_opcoes = ["Divisão 1", "Divisão 2", "Divisão 3"]

for usuario in usuarios:
    time_id = usuario.get("time_id")
    if not time_id:
        continue

    nome_time = mapa_times.get(time_id, "Desconhecido")
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 3, 2])
    col1.markdown(f"**👤 Usuário:** {usuario['usuario']}")
    col2.markdown(f"**🏷️ Time:** {nome_time}")
    
    nova_divisao = col3.selectbox(
        "Divisão:",
        divisoes_opcoes,
        index=divisoes_opcoes.index(usuario.get("Divisão", "Divisão 1")),
        key=f"divisao_{usuario['id']}"
    )
    
    # Botão para salvar alteração
    if st.button(f"💾 Salvar para {usuario['usuario']}", key=f"save_{usuario['id']}"):
        try:
            supabase.table("usuarios").update({"Divisão": nova_divisao}).eq("id", usuario["id"]).execute()
            st.success(f"Divisão de {usuario['usuario']} atualizada para {nova_divisao}")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")
