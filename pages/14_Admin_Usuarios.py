import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Admin Usuários - LigaFut", layout="centered")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_logado = st.session_state.get("usuario", "")
usuario_id = st.session_state.get("usuario_id", "")

# Verifica se o usuário logado é admin
admin_ref = supabase.table("admins").select("email").eq("email", usuario_logado).execute()
eh_admin = len(admin_ref.data) > 0

st.title("👥 Gerenciar Administradores")

if eh_admin:
    st.success(f"Você está logado como ADMIN: `{usuario_logado}`")

    st.markdown("### ➕ Adicionar novo administrador")
    novo_email = st.text_input("E-mail do usuário a ser promovido")

    if st.button("✅ Tornar administrador"):
        if novo_email:
            try:
                # Adiciona o novo admin na tabela 'admins'
                supabase.table("admins").insert({"email": novo_email}).execute()
                st.success(f"Usuário `{novo_email}` agora é um administrador!")
            except Exception as e:
                st.error(f"Erro ao adicionar administrador: {e}")
        else:
            st.warning("Informe um e-mail válido.")
else:
    st.error("❌ Você não tem permissão para acessar esta página. Apenas administradores.")
