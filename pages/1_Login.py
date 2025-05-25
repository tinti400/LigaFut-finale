import streamlit as st
from supabase import create_client, Client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Login - LigaFut", page_icon="🔐", layout="centered")
st.title("🔐 Login - LigaFut")

# 👉 Verifica se já está logado
if "usuario" in st.session_state:
    st.success(f"🔓 Já logado como: {st.session_state['usuario']}")
    st.write("Você já está logado! Acesse o painel ao lado.")
    st.sidebar.success("Bem-vindo ao seu painel!")
    st.stop()

# 📄 Formulário de login
with st.form("login_form"):
    usuario = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    botao_login = st.form_submit_button("Entrar")

# ✅ Lógica de login
if botao_login:
    if usuario and senha:
        with st.spinner("🔄 Verificando suas credenciais..."):
            try:
                res = supabase.table("usuarios") \
                    .select("*") \
                    .ilike("usuario", usuario) \
                    .ilike("senha", senha) \
                    .execute()

                if res.data:
                    user = res.data[0]
                    st.session_state["usuario"] = user["usuario"]
                    st.session_state["usuario_id"] = user["id"]
                    st.session_state["id_time"] = user["time_id"]
                    st.session_state["divisao"] = user.get("divisao", "Divisão 1")

                    time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
                    st.session_state["nome_time"] = time_res.data[0]["nome"] if time_res.data else "Sem Nome"

                    st.success("✅ Login realizado com sucesso!")
                    st.sidebar.success("Bem-vindo ao seu painel!")
                else:
                    st.error("❌ Usuário ou senha inválidos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")
    else:
        st.warning("⚠️ Preencha todos os campos.")

# 🔁 Trocar senha (formulário opcional)
with st.expander("🔒 Trocar Senha"):
    email_confirm = st.text_input("Confirme seu e-mail")
    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirma_nova_senha = st.text_input("Confirme a nova senha", type="password")
    botao_trocar = st.button("✅ Atualizar Senha")

    if botao_trocar:
        if not all([email_confirm, senha_atual, nova_senha, confirma_nova_senha]):
            st.warning("⚠️ Preencha todos os campos.")
        elif nova_senha != confirma_nova_senha:
            st.error("❌ As novas senhas não coincidem.")
        else:
            try:
                res = supabase.table("usuarios") \
                    .select("*") \
                    .ilike("usuario", email_confirm) \
                    .ilike("senha", senha_atual) \
                    .execute()

                if res.data:
                    usuario_id = res.data[0]["id"]
                    update = supabase.table("usuarios").update({"senha": nova_senha}).eq("id", usuario_id).execute()
                    st.success("🔐 Senha atualizada com sucesso!")
                else:
                    st.error("❌ E-mail ou senha atual inválidos.")
            except Exception as e:
                st.error(f"Erro ao atualizar senha: {e}")

# ❓ Esqueci minha senha
with st.expander("❓ Esqueci minha senha"):
    st.info("Entre em contato com o administrador da LigaFut para redefinir sua senha.")
