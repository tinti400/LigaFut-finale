import streamlit as st
from supabase import create_client, Client

# ✅ Deve ser a primeira linha executada
st.set_page_config(page_title="Login - LigaFut", page_icon="⚽", layout="centered")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# 🎨 Estilo com imagem do Ronaldinho
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)),
                          url("https://hceqyuvrythihhbvacyo.supabase.co/storage/v1/object/public/fundo/Ronaldinhobarca.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .login-card {
        background-color: rgba(0, 0, 0, 0.8);
        padding: 2rem;
        border-radius: 16px;
        max-width: 400px;
        margin: auto;
        color: white;
    }
    .login-card input {
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 Login via URL
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

# 🔓 Se já logado
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

# 🔐 Formulário visual de login
with st.container():
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🏟️ LigaFut</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Simule qualquer campeonato com seus amigos</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        usuario = st.text_input("Usuário (e-mail)")
        senha = st.text_input("Senha", type="password")
        botao_login = st.form_submit_button("Entrar")

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
                        st.experimental_set_query_params(usuario=user["usuario"])
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos.")
                except Exception as e:
                    st.error(f"Erro no login: {e}")
        else:
            st.warning("⚠️ Preencha todos os campos.")
    st.markdown("</div>", unsafe_allow_html=True)

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

