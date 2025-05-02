import streamlit as st
from supabase import create_client, Client

# 🔐 Conexão com Supabase usando secrets
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Login - LigaFut", page_icon="🔐", layout="centered")
st.title("🔐 Login - LigaFut")

# 👉 Verifica se já está logado
if "usuario" in st.session_state:
    st.success(f"🔓 Já logado como: {st.session_state['usuario']}")
    st.stop()

# 📄 Formulário de login
with st.form("login_form"):
    usuario = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    botao_login = st.form_submit_button("Entrar")

# ✅ Só executa se o botão for clicado
if botao_login:
    if usuario and senha:
        try:
            # 🔍 Consulta com ilike para não diferenciar maiúsculas/minúsculas
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
                st.session_state["divisao"] = user.get("divisao", "Divisão 1")  # padrão caso não tenha

                # 🔎 Busca o nome do time (agora na tabela `times`)
                time_res = supabase.table("times").select("nome").eq("id", user["time_id"]).execute()
                if time_res.data:
                    st.session_state["nome_time"] = time_res.data[0]["nome"]
                else:
                    st.session_state["nome_time"] = "Sem Nome"

                st.success("✅ Login realizado com sucesso!")
                st.switch_page("pages/3_Home.py")  # ajuste se o nome da sua home for outro
            else:
                st.error("❌ Usuário ou senha inválidos.")
        except Exception as e:
            st.error(f"Erro no login: {e}")
    else:
        st.warning("⚠️ Preencha todos os campos.")
