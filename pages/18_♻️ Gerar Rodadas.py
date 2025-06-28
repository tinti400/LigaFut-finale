# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Definir Grupos Manualmente - LigaFut", layout="wide")
st.title("🏆 Definir Grupos da Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("⚠️ Você precisa estar logado.")
    st.stop()

# ⚙️ Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("🔒 Acesso restrito apenas para administradores.")
    st.stop()

# 🔄 Buscar todos os times disponíveis no sistema
res = supabase.table("times").select("nome").execute()
todos_times = sorted([t["nome"] for t in res.data])

# 🧠 Armazena escolhas dos grupos
grupos = {}
colunas = st.columns(4)
nomes_grupos = ["Grupo A", "Grupo B", "Grupo C", "Grupo D", "Grupo E", "Grupo F", "Grupo G", "Grupo H"]

for i, grupo in enumerate(nomes_grupos):
    with colunas[i % 4]:
        times_escolhidos = st.multiselect(f"{grupo}", todos_times, key=grupo)
        grupos[grupo] = times_escolhidos

# 🔘 Botão para salvar os grupos manualmente
if st.button("✅ Salvar Grupos"):
    # Validação: todos os grupos devem ter 4 times
    erros = [g for g in grupos if len(grupos[g]) != 4]
    if erros:
        st.warning(f"⛔ Cada grupo precisa ter exatamente 4 times. Verifique: {', '.join(erros)}")
        st.stop()

    try:
        # 🧹 Apagar dados antigos
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()

        # 💾 Salvar grupos conforme escolhido
        for grupo, times in grupos.items():
            for ordem, nome_time in enumerate(times):
                supabase.table("grupos_copa").insert({
                    "grupo": grupo,
                    "nome_time": nome_time,
                    "ordem": ordem,
                    "pontos": 0,
                    "jogos": 0,
                    "vitorias": 0,
                    "empates": 0,
                    "derrotas": 0,
                    "gols_pro": 0,
                    "gols_contra": 0,
                    "saldo_gols": 0,
                    "data_criacao": datetime.now().isoformat()
                }).execute()
        st.success("✅ Grupos salvos com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao salvar grupos: {e}")
