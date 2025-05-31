# 24_Gerar_Grupos_Copa.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Gerar Grupos da Copa", layout="centered")
st.title("🎯 Gerar Grupos da Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
try:
    admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    eh_admin = len(admin_ref.data) > 0
    if not eh_admin:
        st.warning("🔒 Acesso permitido apenas para administradores.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar administrador: {e}")
    st.stop()

# 🔄 Buscar times
try:
    todos_times = supabase.table("times").select("id, nome").execute().data
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# 📌 Seleção manual dos times
st.subheader("📌 Selecione os times participantes")
opcoes = {t['nome']: t['id'] for t in todos_times}
selecionados = st.multiselect("Escolha os times que irão participar da Copa:", list(opcoes.keys()))

if st.button("⚙️ Gerar Grupos da Copa"):
    if len(selecionados) < 4:
        st.warning("🚨 É necessário no mínimo 4 times para formar grupos.")
        st.stop()

    times_escolhidos = [opcoes[nome] for nome in selecionados]
    random.shuffle(times_escolhidos)

    grupos = {"Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []}
    nomes_grupos = list(grupos.keys())

    # Distribui os times nos grupos (1 com 6, 3 com 5)
    qtd_grupos = [6, 5, 5, 5] if len(times_escolhidos) >= 21 else [5] * 4
    idx = 0
    for i, qtd in enumerate(qtd_grupos):
        grupos[nomes_grupos[i]] = times_escolhidos[idx:idx+qtd]
        idx += qtd

    # 💾 Salvar grupos com data atual
    data_copa = datetime.now().strftime("%Y-%m-%d")

    try:
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()
        for grupo_nome, lista_times in grupos.items():
            for id_time in lista_times:
                supabase.table("grupos_copa").insert({
                    "grupo": grupo_nome,
                    "id_time": id_time,
                    "data_criacao": data_copa
                }).execute()
        st.success("✅ Grupos da Copa gerados e salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar grupos: {e}")

    # 🖼️ Visualização
    st.subheader("📊 Grupos Gerados")
    for grupo, lista in grupos.items():
        nomes = [nome for nome, id_ in opcoes.items() if id_ in lista]
        st.markdown(f"**{grupo}**: {', '.join(nomes)}")
