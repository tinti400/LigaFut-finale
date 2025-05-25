import streamlit as st
from supabase import create_client, Client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Login - LigaFut", page_icon="🔐", layout="centered")
st.title("🔐 Login - LigaFut")

# 🌐 Recuperar da URL se possível
params = st.experimental_get_query_params()
if "usuario" not in st.session_state and "usuario" in params:
    try:
        usuario_param = params["usuario"][0]
        res = supabase.table("usuarios").select("*").ilike("usuario", usuario_param).execute()
        if res.data:
            user = res.data[0]
            st.session_state["usuario"] = user["usuario"]
            st.session_state["usuario_id"] = user["id"]
            st.session_state["id_time"] = user["time_id"]
            st.session_state["divisao"] = user.get("divisao", "Divisão 1")
            time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
            st.session_state["nome_time"] = time_res.data[0]["nome"] if time_res.data else "Sem Nome"
    except:
        pass

# 👉 Já logado?
if "usuario" in st.session_state:
    st.success(f"🔓 Logado como: {st.session_state['usuario']}")
    if st.button("🔓 Sair"):
        for key in ["usuario", "usuario_id", "id_time", "nome_time", "divisao"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params()
        st.success("Sessão encerrada. Recarregue ou faça login.")
        st.stop()
    st.sidebar.success("Acesse seu painel ao lado.")
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
                res = supabase.table("usuarios").select("*").ilike("usuario", usuario).ilike("senha", senha).execute()
                if res.data:
                    user = res.data[0]
                    st.session_state["usuario"] = user["usuario"]
                    st.session_state["usuario_id"] = user["id"]
                    st.session_state["id_time"] = user["time_id"]
                    st.session_state["divisao"] = user.get("divisao", "Divisão 1")
                    time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
                    st.session_state["nome_time"] = time_res.data[0]["nome"] if time_res.data else "Sem Nome"

                    # 🔗 Salva na URL
                    st.experimental_set_query_params(usuario=user["usuario"])
                    st.success("✅ Login realizado com sucesso!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")
    else:
        st.warning("⚠️ Preencha todos os campos.")

# 🔁 Trocar senha
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
                res = supabase.table("usuarios").select("*").ilike("usuario", email_confirm).ilike("senha", senha_atual).execute()
                if res.data:
                    usuario_id = res.data[0]["id"]
                    supabase.table("usuarios").update({"senha": nova_senha}).eq("id", usuario_id).execute()
                    st.success("🔐 Senha atualizada com sucesso!")
                else:
                    st.error("❌ E-mail ou senha atual inválidos.")
            except Exception as e:
                st.error(f"Erro ao atualizar senha: {e}")

# ❓ Esqueci minha senha
with st.expander("❓ Esqueci minha senha"):
    st.info("Entre em contato com o administrador da LigaFut para redefinir sua senha.")

