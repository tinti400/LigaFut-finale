# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Gerar Grupos Fixos - Copa LigaFut", layout="centered")
st.title("🏆 Gerar Grupos da Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

# ⚙️ Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("🔒 Acesso restrito apenas para administradores.")
    st.stop()

# 📦 Grupos fixos 100% iguais aos da imagem
grupos_fixos = {
    "Grupo A": ["Bayern", "Borussia", "PSG", "Atletico de Madrid"],
    "Grupo B": ["Belgrano", "Ajax", "Liverpool", "Manchester United"],
    "Grupo C": ["venezia", "Milan", "Charleroi", "Boca Jrs"],
    "Grupo D": ["tottenham", "Estudiantes", "Casa Pia", "Lyon"],
    "Grupo E": ["Olympique Marselhe", "Newells", "Real Betis", "Stuttgart"],
    "Grupo F": ["River", "Arsenal", "Inter Miami", "Chelsea"],
    "Grupo G": ["Rio Ave", "Napoli", "Leicester", "Wolverhampton"],
    "Grupo H": ["Barcelona", "Wrexham", "Atlanta", "Real Madrid"]
}

# 🔘 Botão para gerar os grupos
if st.button("✅ Gerar Grupos Fixos"):
    try:
        # 🧹 Apagar grupos anteriores
        supabase.table("grupos_copa").delete().neq("grupo", "").execute()

        # 💾 Inserir os grupos no Supabase
        for grupo, times in grupos_fixos.items():
            for ordem, nome_time in enumerate(times):
                supabase.table("grupos_copa").insert({
                    "grupo": grupo,
                    "nome_time": nome_time,
                    "ordem": ordem,  # Mantém a ordem exata da imagem
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

        st.success("✅ Grupos fixos criados exatamente como na imagem!")
    except Exception as e:
        st.error(f"❌ Erro ao criar os grupos: {e}")
