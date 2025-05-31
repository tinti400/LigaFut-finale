# 24_Gerar_Grupos_Copa.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🌟 Gerar Grupos da Copa", layout="centered")
st.title("🌟 Gerar Grupos da Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("🔒 Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
try:
    admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    eh_admin = len(admin_ref.data) > 0
    if not eh_admin:
        st.warning("🔐 Acesso permitido apenas para administradores.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar admin: {e}")
    st.stop()

# 🔹 Buscar todos os times
try:
    res = supabase.table("times").select("id, nome").execute()
    times = res.data
    if len(times) != 21:
        st.warning(f"⚠️ Precisamos de exatamente 21 times. Atualmente há {len(times)} cadastrados.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 🔀 Sortear times nos grupos
random.shuffle(times)
grupos = {"Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []}
tamanho_grupo = [5, 5, 5, 6]
indice = 0

for grupo, tamanho in zip(grupos.keys(), tamanho_grupo):
    for _ in range(tamanho):
        grupos[grupo].append(times[indice])
        indice += 1

# 🖇 Apagar dados antigos (opcional)
if st.button("🔀 Sortear e Salvar Grupos"):
    try:
        supabase.table("copa_grupos").delete().neq("grupo", "").execute()
        for grupo, lista in grupos.items():
            for time in lista:
                supabase.table("copa_grupos").insert({
                    "grupo": grupo,
                    "time_id": time["id"],
                    "pontos": 0,
                    "gp": 0,
                    "gc": 0,
                    "sg": 0,
                    "jogos": 0,
                    "nome_time": time["nome"]
                }).execute()
        st.success("✅ Grupos sorteados e salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar grupos: {e}")

# 📊 Mostrar grupos
st.markdown("---")
st.markdown("### 📅 Grupos Sorteados")
cols = st.columns(4)

for i, (grupo, lista) in enumerate(grupos.items()):
    with cols[i]:
        st.markdown(f"**{grupo}**")
        for time in lista:
            st.write(f"- {time['nome']}")
