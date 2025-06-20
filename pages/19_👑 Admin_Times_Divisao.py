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

# 📥 Opções válidas de divisão
divisoes_opcoes = ["Divisão 1", "Divisão 2", "Divisão 3"]

# 🔍 Buscar usuários e times
usuarios = supabase.table("usuarios").select("id, usuario, time_id, Divisão").execute().data
times = supabase.table("times").select("id, nome").execute().data

mapa_times = {t["id"]: t["nome"] for t in times if "id" in t and "nome" in t}

# 📋 Criar listas para filtros
lista_nomes_times = sorted(set([mapa_times.get(u["time_id"]) for u in usuarios if u.get("time_id") in mapa_times]))
lista_usuarios = sorted(set([u["usuario"] for u in usuarios]))

# 🔎 Filtros
colf1, colf2 = st.columns(2)
filtro_time = colf1.selectbox("🔍 Filtrar por time", ["Todos"] + lista_nomes_times)
filtro_usuario = colf2.selectbox("👤 Filtrar por usuário", ["Todos"] + lista_usuarios)

# 📋 Mostrar tabela de usuários
st.markdown("### 👥 Lista de Usuários com Times")

encontrou = False

for usuario in usuarios:
    time_id = usuario.get("time_id")
    divisao_atual = usuario.get("Divisão")
    nome_usuario = usuario.get("usuario")

    if not time_id or divisao_atual not in divisoes_opcoes:
        continue

    nome_time = mapa_times.get(time_id, "Desconhecido")

    # Aplica filtros
    if (filtro_time != "Todos" and nome_time != filtro_time) or \
       (filtro_usuario != "Todos" and nome_usuario != filtro_usuario):
        continue

    encontrou = True
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 3, 2])
    col1.markdown(f"**👤 Usuário:** {nome_usuario}")
    col2.markdown(f"**🏷️ Time:** {nome_time}")

    nova_divisao = col3.selectbox(
        "Divisão:",
        divisoes_opcoes,
        index=divisoes_opcoes.index(divisao_atual),
        key=f"divisao_{usuario['id']}"
    )

    if st.button(f"💾 Salvar para {nome_usuario}", key=f"save_{usuario['id']}"):
        try:
            supabase.table("usuarios").update({"Divisão": nova_divisao}).eq("id", usuario["id"]).execute()
            st.success(f"Divisão de {nome_usuario} atualizada para {nova_divisao}")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

if not encontrou:
    st.info("Nenhum resultado encontrado com os filtros selecionados.")

