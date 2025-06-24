# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client, Client
import uuid

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Login - LigaFut", page_icon="⚽", layout="centered")

# 🎨 Estilo visual completo
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)),
                          url("https://hceqyuvryhtihhbvacyo.supabase.co/storage/v1/object/public/fundo/Ronaldinhobarca.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .login-card {
        background-color: rgba(0, 0, 0, 0.85);
        padding: 2rem;
        border-radius: 16px;
        max-width: 420px;
        margin: auto;
        color: white;
    }
    .stTextInput>div>div>input {
        font-size: 1.05rem !important;
    }
    .stButton>button {
        background-color: #66fcf1;
        color: black;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        padding: 0.75em;
        margin-top: 1em;
        transition: 0.3s ease;
        font-size: 1.05rem;
    }
    .stButton>button:hover {
        background-color: #45e0d1;
        transform: scale(1.02);
    }
    button[data-baseweb="button"][id="senha"] {
        background-color: #34c759 !important;
        color: white !important;
    }
    h2 {
        font-size: 30px;
        text-align: center;
        color: white !important;
    }
    p {
        text-align: center;
        font-size: 18px;
        color: #d1d1d1;
    }
    label {
        color: white !important;
        font-size: 1.05rem !important;
    }
    [data-testid="stExpander"] > summary {
        background-color: #66fcf1 !important;
        color: black !important;
        font-weight: bold;
        padding: 10px;
        border-radius: 8px;
        font-size: 1.05rem;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 Login via URL (?usuario=...)
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
            st.session_state["administrador"] = user.get("administrador", False)
            st.session_state["session_id"] = user.get("session_id", "")
            time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
            st.session_state["nome_time"] = time_res.data[0]["nome"] if time_res.data else "Sem Nome"
    except:
        pass

# 🔓 Se já estiver logado
if "usuario" in st.session_state:
    if st.session_state.get("login_realizado"):
        st.session_state.pop("login_realizado", None)
        st.sidebar.success("✅ Login realizado com sucesso! Use o menu ao lado.")
        st.stop()

    st.success(f"🔓 Logado como: {st.session_state['usuario']}")
    if st.button("🔒 Sair"):
        for key in ["usuario", "usuario_id", "id_time", "nome_time", "divisao", "session_id", "administrador"]:
            st.session_state.pop(key, None)
        st.experimental_set_query_params()
        st.success("Sessão encerrada. Recarregue ou faça login.")
        st.stop()
    st.sidebar.success("Acesse seu painel ao lado.")
    st.stop()

# 🧾 Formulário de login
with st.container():
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.image("https://hceqyuvryhtihhbvacyo.supabase.co/storage/v1/object/public/fundo/logo-ligafut.png", width=100)
    st.markdown("<h2>🏟️ LigaFut</h2>", unsafe_allow_html=True)
    st.markdown("<p>Gerencie seu clube. Simule torneios. Comande como um verdadeiro técnico!</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        usuario = st.text_input("Usuário (e-mail)")
        mostrar_senha = st.checkbox("👁 Mostrar senha")
        senha = st.text_input("Senha", type="default" if mostrar_senha else "password")
        botao_login = st.form_submit_button("Entrar")

    if botao_login:
        if usuario and senha:
            with st.spinner("🔄 Verificando suas credenciais..."):
                try:
                    res = supabase.table("usuarios").select("*").ilike("usuario", usuario).ilike("senha", senha).execute()
                    if res.data:
                        user = res.data[0]
                        novo_session_id = str(uuid.uuid4())
                        supabase.table("usuarios").update({"session_id": novo_session_id}).eq("id", user["id"]).execute()
                        st.session_state["usuario"] = user["usuario"]
                        st.session_state["usuario_id"] = user["id"]
                        st.session_state["id_time"] = user["time_id"]
                        st.session_state["divisao"] = user.get("divisao", "Divisão 1")
                        st.session_state["administrador"] = user.get("administrador", False)
                        st.session_state["session_id"] = novo_session_id
                        st.experimental_set_query_params(usuario=user["usuario"])
                        time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
                        st.session_state["nome_time"] = time_res.data[0]["nome"] if time_res.data else "Sem Nome"
                        st.session_state["login_realizado"] = True
                        st.experimental_rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos.")
                except Exception as e:
                    st.error(f"Erro no login: {e}")
        else:
            st.warning("⚠️ Preencha todos os campos.")
    st.markdown("</div>", unsafe_allow_html=True)

# 🔁 Troca de senha
with st.expander("🔒 Trocar Senha"):
    email_confirm = st.text_input("Confirme seu e-mail")
    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirma_nova_senha = st.text_input("Confirme a nova senha", type="password")
    botao_trocar = st.button("✅ Atualizar Senha", key="senha")

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
